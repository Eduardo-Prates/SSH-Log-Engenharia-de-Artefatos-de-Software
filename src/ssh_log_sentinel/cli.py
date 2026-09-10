"""Interface de linha de comando do SSH Log Sentinel."""

import argparse
from collections.abc import Iterator, Sequence
from contextlib import nullcontext
from dataclasses import dataclass
from datetime import timedelta, timezone
import json
from pathlib import Path
import re
import sys
from typing import TextIO

from .detector import detect_brute_force
from .models import BruteForceAlert, FailedAuthenticationAttempt
from .parser import TimestampNormalizer, parse_line


@dataclass(slots=True)
class _ProcessingCounts:
    recognized: int = 0
    ignored: int = 0


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


def _alert_as_dict(alert: BruteForceAlert) -> dict[str, object]:
    return {
        "record_type": "alert",
        "source_ip": str(alert.source_ip),
        "window_started_at": alert.window_started_at.isoformat(),
        "detected_at": alert.detected_at.isoformat(),
        "attempt_count": alert.attempt_count,
        "usernames": list(alert.usernames),
    }


def _iter_events(
    log_file: TextIO,
    *,
    timestamp_normalizer: TimestampNormalizer,
    counts: _ProcessingCounts,
) -> Iterator[FailedAuthenticationAttempt]:
    for line in log_file:
        event = parse_line(
            line,
            timestamp_normalizer=timestamp_normalizer,
        )
        if event is None:
            counts.ignored += 1
            continue

        counts.recognized += 1
        yield event


def _parse_utc_offset(value: str) -> timezone:
    match = re.fullmatch(
        r"(?P<sign>[+-])(?P<hours>\d{2}):(?P<minutes>\d{2})",
        value,
    )
    if match is None:
        raise argparse.ArgumentTypeError("use o formato +HH:MM ou -HH:MM")

    hours = int(match.group("hours"))
    minutes = int(match.group("minutes"))
    if hours > 23 or minutes > 59:
        raise argparse.ArgumentTypeError("o deslocamento deve ser menor que 24 horas")

    offset = timedelta(hours=hours, minutes=minutes)
    if match.group("sign") == "-":
        offset = -offset
    return timezone(offset)


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ssh-log-sentinel",
        description="Normaliza falhas de senha registradas pelo OpenSSH.",
    )
    parser.add_argument(
        "log_file",
        help="arquivo de log a analisar, ou - para ler da entrada padrão",
    )
    parser.add_argument(
        "--year",
        type=int,
        help="ano a associar a timestamps syslog que não possuem ano",
    )
    timezone_group = parser.add_mutually_exclusive_group()
    timezone_group.add_argument(
        "--utc-offset",
        type=_parse_utc_offset,
        metavar="OFFSET",
        help="fuso dos timestamps syslog (padrão: +00:00)",
    )
    timezone_group.add_argument(
        "--utc-offset-hours",
        type=int,
        choices=range(-23, 24),
        metavar="H",
        help="fuso em horas inteiras; mantido para compatibilidade",
    )
    parser.add_argument(
        "--detect",
        action="store_true",
        help="emitir alertas de possível força bruta em vez dos eventos",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=5,
        metavar="N",
        help="falhas necessárias para alertar no modo --detect (padrão: 5)",
    )
    parser.add_argument(
        "--window-seconds",
        type=int,
        default=300,
        metavar="S",
        help="tamanho da janela de detecção em segundos (padrão: 300)",
    )
    parser.add_argument(
        "--alerts-file",
        type=Path,
        metavar="PATH",
        help="gravar alertas JSON neste arquivo no modo --detect",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_argument_parser().parse_args(argv)
    if args.alerts_file is not None and not args.detect:
        print("erro: --alerts-file requer --detect", file=sys.stderr)
        return 2

    counts = _ProcessingCounts()
    default_timezone = args.utc_offset
    if default_timezone is None:
        default_timezone = timezone(timedelta(hours=args.utc_offset_hours or 0))
    timestamp_normalizer = TimestampNormalizer(
        assumed_year=args.year,
        default_timezone=default_timezone,
    )

    try:
        input_context = (
            nullcontext(sys.stdin)
            if args.log_file == "-"
            else Path(args.log_file).open(encoding="utf-8", errors="replace")
        )
        with input_context as log_file:
            events = _iter_events(
                log_file,
                timestamp_normalizer=timestamp_normalizer,
                counts=counts,
            )
            if args.detect:
                alerts = list(
                    detect_brute_force(
                        events,
                        threshold=args.threshold,
                        window=timedelta(seconds=args.window_seconds),
                    )
                )
                serialized_alerts = [
                    json.dumps(_alert_as_dict(alert), ensure_ascii=False)
                    for alert in alerts
                ]
                if args.alerts_file is not None:
                    content = "\n".join(serialized_alerts)
                    args.alerts_file.write_text(
                        f"{content}\n" if content else "",
                        encoding="utf-8",
                    )
                else:
                    for serialized_alert in serialized_alerts:
                        print(serialized_alert)
            else:
                alerts = []
                for event in events:
                    print(json.dumps(_event_as_dict(event), ensure_ascii=False))
    except OSError as error:
        print(f"erro ao ler {args.log_file}: {error}", file=sys.stderr)
        return 2
    except ValueError as error:
        print(f"erro de detecção: {error}", file=sys.stderr)
        return 2

    summary = f"reconhecidas={counts.recognized} ignoradas={counts.ignored}"
    if args.detect:
        summary += f" alertas={len(alerts)}"
    print(summary, file=sys.stderr)
    return 1 if alerts else 0
