from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from ssh_log_sentinel.cli import main


class CliTests(unittest.TestCase):
    def test_emits_json_event_and_processing_summary(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            log_path = Path(temporary_directory) / "auth.log"
            log_path.write_text(
                "Jan 10 12:00:00 host sshd[1]: unrelated message\n"
                "Jan 10 12:00:01 host sshd[1]: Failed password for alice "
                "from 192.0.2.10 port 51000 ssh2\n",
                encoding="utf-8",
            )
            stdout = StringIO()
            stderr = StringIO()

            with redirect_stdout(stdout), redirect_stderr(stderr):
                exit_code = main([str(log_path)])

        payload = json.loads(stdout.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["username"], "alice")
        self.assertEqual(payload["source_ip"], "192.0.2.10")
        self.assertEqual(stderr.getvalue(), "reconhecidas=1 ignoradas=1\n")

    def test_detection_mode_emits_alert_and_returns_one(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            log_path = Path(temporary_directory) / "auth.log"
            log_path.write_text(
                "Jan 10 12:00:00 host sshd[1]: Failed password for admin "
                "from 192.0.2.10 port 51000 ssh2\n"
                "Jan 10 12:00:20 host sshd[1]: Failed password for root "
                "from 192.0.2.10 port 51001 ssh2\n"
                "Jan 10 12:00:40 host sshd[1]: Failed password for admin "
                "from 192.0.2.10 port 51002 ssh2\n",
                encoding="utf-8",
            )
            stdout = StringIO()
            stderr = StringIO()

            with redirect_stdout(stdout), redirect_stderr(stderr):
                exit_code = main(
                    [
                        str(log_path),
                        "--year",
                        "2026",
                        "--utc-offset-hours=-3",
                        "--detect",
                        "--threshold",
                        "3",
                        "--window-seconds",
                        "60",
                    ]
                )

        payload = json.loads(stdout.getvalue())
        self.assertEqual(exit_code, 1)
        self.assertEqual(payload["record_type"], "alert")
        self.assertEqual(payload["source_ip"], "192.0.2.10")
        self.assertEqual(payload["attempt_count"], 3)
        self.assertEqual(payload["usernames"], ["admin", "root"])
        self.assertEqual(
            payload["detected_at"],
            "2026-01-10T15:00:40+00:00",
        )
        self.assertEqual(stderr.getvalue(), "reconhecidas=3 ignoradas=0 alertas=1\n")

    def test_detection_mode_returns_zero_when_there_is_no_alert(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            log_path = Path(temporary_directory) / "auth.log"
            log_path.write_text(
                "2026-01-10T12:00:00+00:00 host sshd[1]: "
                "Failed password for admin from 192.0.2.10 port 51000 ssh2\n",
                encoding="utf-8",
            )
            stdout = StringIO()
            stderr = StringIO()

            with redirect_stdout(stdout), redirect_stderr(stderr):
                exit_code = main([str(log_path), "--detect", "--threshold", "2"])

        self.assertEqual(exit_code, 0)
        self.assertEqual(stdout.getvalue(), "")
        self.assertEqual(stderr.getvalue(), "reconhecidas=1 ignoradas=0 alertas=0\n")

    def test_detection_mode_rejects_syslog_without_year(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            log_path = Path(temporary_directory) / "auth.log"
            log_path.write_text(
                "Jan 10 12:00:00 host sshd[1]: Failed password for admin "
                "from 192.0.2.10 port 51000 ssh2\n",
                encoding="utf-8",
            )
            stdout = StringIO()
            stderr = StringIO()

            with redirect_stdout(stdout), redirect_stderr(stderr):
                exit_code = main([str(log_path), "--detect"])

        self.assertEqual(exit_code, 2)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("occurred_at", stderr.getvalue())

    def test_detection_mode_rejects_invalid_configuration(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            log_path = Path(temporary_directory) / "auth.log"
            log_path.write_text("", encoding="utf-8")
            stderr = StringIO()

            with redirect_stdout(StringIO()), redirect_stderr(stderr):
                exit_code = main([str(log_path), "--detect", "--threshold", "0"])

        self.assertEqual(exit_code, 2)
        self.assertIn("threshold", stderr.getvalue())

    def test_reads_log_from_standard_input(self) -> None:
        stdin = StringIO(
            "2026-01-10T12:00:00+00:00 host sshd[1]: "
            "Failed password for admin from 192.0.2.10 port 51000 ssh2\n"
        )
        stdout = StringIO()
        stderr = StringIO()

        with (
            patch("sys.stdin", stdin),
            redirect_stdout(stdout),
            redirect_stderr(stderr),
        ):
            exit_code = main(["-"])

        payload = json.loads(stdout.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["username"], "admin")
        self.assertEqual(stderr.getvalue(), "reconhecidas=1 ignoradas=0\n")

    def test_accepts_utc_offset_with_minutes(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            log_path = Path(temporary_directory) / "auth.log"
            log_path.write_text(
                "Jan 10 12:00:00 host sshd[1]: Failed password for admin "
                "from 192.0.2.10 port 51000 ssh2\n",
                encoding="utf-8",
            )
            stdout = StringIO()

            with redirect_stdout(stdout), redirect_stderr(StringIO()):
                exit_code = main(
                    [str(log_path), "--year", "2026", "--utc-offset=-03:30"]
                )

        payload = json.loads(stdout.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["occurred_at"], "2026-01-10T15:30:00+00:00")

    def test_detection_handles_december_to_january_rollover(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            log_path = Path(temporary_directory) / "auth.log"
            log_path.write_text(
                "Dec 31 23:59:30 host sshd[1]: Failed password for admin "
                "from 192.0.2.10 port 51000 ssh2\n"
                "Jan  1 00:00:00 host sshd[1]: Failed password for root "
                "from 192.0.2.10 port 51001 ssh2\n",
                encoding="utf-8",
            )
            stdout = StringIO()

            with redirect_stdout(stdout), redirect_stderr(StringIO()):
                exit_code = main(
                    [
                        str(log_path),
                        "--year",
                        "2026",
                        "--detect",
                        "--threshold",
                        "2",
                        "--window-seconds",
                        "60",
                    ]
                )

        payload = json.loads(stdout.getvalue())
        self.assertEqual(exit_code, 1)
        self.assertEqual(payload["window_started_at"], "2026-12-31T23:59:30+00:00")
        self.assertEqual(payload["detected_at"], "2027-01-01T00:00:00+00:00")

    def test_writes_alerts_to_optional_file(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            base_path = Path(temporary_directory)
            log_path = base_path / "auth.log"
            alerts_path = base_path / "alerts.jsonl"
            log_path.write_text(
                "2026-01-10T12:00:00+00:00 host sshd[1]: "
                "Failed password for admin from 192.0.2.10 port 51000 ssh2\n"
                "2026-01-10T12:00:10+00:00 host sshd[1]: "
                "Failed password for root from 192.0.2.10 port 51001 ssh2\n",
                encoding="utf-8",
            )
            stdout = StringIO()

            with redirect_stdout(stdout), redirect_stderr(StringIO()):
                exit_code = main(
                    [
                        str(log_path),
                        "--detect",
                        "--threshold",
                        "2",
                        "--alerts-file",
                        str(alerts_path),
                    ]
                )
            payload = json.loads(alerts_path.read_text(encoding="utf-8"))

        self.assertEqual(exit_code, 1)
        self.assertEqual(stdout.getvalue(), "")
        self.assertEqual(payload["record_type"], "alert")

    def test_alerts_file_requires_detection_mode(self) -> None:
        stderr = StringIO()

        with redirect_stderr(stderr):
            exit_code = main(["unused.log", "--alerts-file", "alerts.jsonl"])

        self.assertEqual(exit_code, 2)
        self.assertIn("requer --detect", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
