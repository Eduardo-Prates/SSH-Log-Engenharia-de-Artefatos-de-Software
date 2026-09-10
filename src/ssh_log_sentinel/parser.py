"""Parser do subconjunto inicial de mensagens de autenticação OpenSSH."""

from collections.abc import Iterable, Iterator
from datetime import datetime, timezone, tzinfo
from ipaddress import ip_address
import re

from .models import FailedAuthenticationAttempt


_LOG_LINE = re.compile(
    r"^(?P<timestamp>"
    r"(?:[A-Z][a-z]{2}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})"
    r"|(?:\d{4}-\d{2}-\d{2}T\S+)"
    r")\s+"
    r"(?P<hostname>\S+)\s+"
    r"sshd(?:\[(?P<process_id>\d+)\])?:\s+"
    r"(?P<message>.+)$"
)

_FAILED_PASSWORD = re.compile(
    r"^Failed password for (?P<invalid_user>invalid user )?"
    r"(?P<username>\S+) from (?P<source_ip>\S+) "
    r"port (?P<source_port>\d+) ssh2(?:\s+\[preauth\])?$"
)

_SYSLOG_TIMESTAMP = re.compile(
    r"^(?P<month>[A-Z][a-z]{2})\s+(?P<day>\d{1,2})\s+"
    r"(?P<hour>\d{2}):(?P<minute>\d{2}):(?P<second>\d{2})$"
)

_MONTHS = {
    "Jan": 1,
    "Feb": 2,
    "Mar": 3,
    "Apr": 4,
    "May": 5,
    "Jun": 6,
    "Jul": 7,
    "Aug": 8,
    "Sep": 9,
    "Oct": 10,
    "Nov": 11,
    "Dec": 12,
}


def normalize_timestamp(
    timestamp_text: str,
    *,
    assumed_year: int | None = None,
    default_timezone: tzinfo = timezone.utc,
) -> datetime | None:
    """Normaliza ISO 8601 ou syslog para UTC quando há contexto suficiente."""

    try:
        if timestamp_text[:1].isdigit():
            parsed = datetime.fromisoformat(timestamp_text.replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=default_timezone)
            return parsed.astimezone(timezone.utc)

        syslog_timestamp = _SYSLOG_TIMESTAMP.fullmatch(timestamp_text)
        if syslog_timestamp is None or assumed_year is None:
            return None

        parsed = datetime(
            assumed_year,
            _MONTHS[syslog_timestamp.group("month")],
            int(syslog_timestamp.group("day")),
            int(syslog_timestamp.group("hour")),
            int(syslog_timestamp.group("minute")),
            int(syslog_timestamp.group("second")),
            tzinfo=default_timezone,
        )
        return parsed.astimezone(timezone.utc)
    except (KeyError, ValueError):
        return None


def parse_line(
    line: str,
    *,
    assumed_year: int | None = None,
    default_timezone: tzinfo = timezone.utc,
) -> FailedAuthenticationAttempt | None:
    """Converte uma linha suportada em evento; retorna ``None`` caso contrário."""

    raw_line = line.rstrip("\r\n")
    envelope = _LOG_LINE.fullmatch(raw_line)
    if envelope is None:
        return None

    failure = _FAILED_PASSWORD.fullmatch(envelope.group("message"))
    if failure is None:
        return None

    try:
        source_ip = ip_address(failure.group("source_ip"))
        source_port = int(failure.group("source_port"))
    except ValueError:
        return None

    if not 1 <= source_port <= 65535:
        return None

    process_id_text = envelope.group("process_id")
    timestamp = envelope.group("timestamp")
    return FailedAuthenticationAttempt(
        timestamp=timestamp,
        occurred_at=normalize_timestamp(
            timestamp,
            assumed_year=assumed_year,
            default_timezone=default_timezone,
        ),
        hostname=envelope.group("hostname"),
        process_id=int(process_id_text) if process_id_text is not None else None,
        username=failure.group("username"),
        invalid_user=failure.group("invalid_user") is not None,
        source_ip=source_ip,
        source_port=source_port,
        authentication_method="password",
        raw_line=raw_line,
    )


def parse_lines(
    lines: Iterable[str],
    *,
    assumed_year: int | None = None,
    default_timezone: tzinfo = timezone.utc,
) -> Iterator[FailedAuthenticationAttempt]:
    """Produz, em ordem, somente os eventos reconhecidos em ``lines``."""

    for line in lines:
        if event := parse_line(
            line,
            assumed_year=assumed_year,
            default_timezone=default_timezone,
        ):
            yield event
