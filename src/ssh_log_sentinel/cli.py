"""Interface de linha de comando do primeiro incremento."""

import argparse
from collections.abc import Sequence
from datetime import timedelta, timezone
import json
from pathlib import Path
import sys

from .models import FailedAuthenticationAttempt
from .parser import parse_line


def _event_as_dict(event: FailedAuthenticationAttempt) -> dict[str, object]:
    return {
        "timestamp": event.timestamp,
        "occurred_at": event.occurred_at.isoformat() if event.occurred_at else None,
        "hostname": event.hostname,
        "process_id": event.process_id,
        "username": event.username,
        "invalid_user": event.invalid_user,
        "source_ip": str(event.source_ip),
        "source_port": event.source_port,
        "authentication_method": event.authentication_method,
        "raw_line": event.raw_line,
    }


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ssh-log-sentinel",
        description="Normaliza falhas de senha registradas pelo OpenSSH.",
    )
    parser.add_argument("log_file", type=Path, help="arquivo de log a analisar")
    parser.add_argument(
        "--year",
        type=int,
        help="ano a associar a timestamps syslog que não possuem ano",
    )
    parser.add_argument(
        "--utc-offset-hours",
        type=int,
        default=0,
        choices=range(-23, 24),
        metavar="H",
        help="fuso dos timestamps syslog, em horas de UTC (padrão: 0)",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_argument_parser().parse_args(argv)
    parsed = 0
    ignored = 0
    default_timezone = timezone(timedelta(hours=args.utc_offset_hours))

    try:
        with args.log_file.open(encoding="utf-8", errors="replace") as log_file:
            for line in log_file:
                event = parse_line(
                    line,
                    assumed_year=args.year,
                    default_timezone=default_timezone,
                )
                if event is None:
                    ignored += 1
                    continue

                print(json.dumps(_event_as_dict(event), ensure_ascii=False))
                parsed += 1
    except OSError as error:
        print(f"erro ao ler {args.log_file}: {error}", file=sys.stderr)
        return 2

    print(f"reconhecidas={parsed} ignoradas={ignored}", file=sys.stderr)
    return 0
