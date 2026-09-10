"""Reproduz automaticamente as principais alegações do artefato."""

import json
import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def run_case(
    arguments: list[str], expected_code: int
) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    source_path = str(PROJECT_ROOT / "src")
    environment["PYTHONPATH"] = os.pathsep.join(
        part for part in (source_path, environment.get("PYTHONPATH")) if part
    )
    result = subprocess.run(
        [sys.executable, *arguments],
        cwd=PROJECT_ROOT,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != expected_code:
        raise RuntimeError(
            f"código inesperado para {arguments}: {result.returncode}\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return result


def main() -> int:
    tests = run_case(
        ["-m", "unittest", "discover", "-s", "tests", "-v"],
        expected_code=0,
    )
    if "OK" not in tests.stderr:
        raise RuntimeError("a suíte não informou OK")

    alert = run_case(
        [
            "-m",
            "ssh_log_sentinel",
            "examples/sample-brute-force.log",
            "--year",
            "2026",
            "--utc-offset=-03:00",
            "--detect",
        ],
        expected_code=1,
    )
    alert_payload = json.loads(alert.stdout)
    if alert_payload["source_ip"] != "192.0.2.50":
        raise RuntimeError("o alerta principal não identificou o IP esperado")
    if alert_payload["attempt_count"] != 5:
        raise RuntimeError("o alerta principal não contou cinco tentativas")

    no_alert = run_case(
        [
            "-m",
            "ssh_log_sentinel",
            "examples/sample-brute-force.log",
            "--year",
            "2026",
            "--detect",
            "--threshold",
            "6",
        ],
        expected_code=0,
    )
    if no_alert.stdout:
        raise RuntimeError("o cenário abaixo do limiar produziu saída de alerta")

    rollover = run_case(
        [
            "-m",
            "ssh_log_sentinel",
            "examples/sample-year-rollover.log",
            "--year",
            "2026",
            "--detect",
            "--threshold",
            "2",
            "--window-seconds",
            "60",
        ],
        expected_code=1,
    )
    rollover_payload = json.loads(rollover.stdout)
    if rollover_payload["detected_at"] != "2027-01-01T00:00:00+00:00":
        raise RuntimeError("a virada do ano não produziu o instante esperado")

    print("REPRODUCAO CONCLUIDA")
    print("- suite automatizada: OK")
    print("- alerta principal: 192.0.2.50, 5 tentativas")
    print("- cenario abaixo do limiar: 0 alertas")
    print("- virada do ano: 2027-01-01T00:00:00+00:00")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
