"""Modelos de domínio produzidos pelo parser."""

from dataclasses import dataclass
from datetime import datetime
from ipaddress import IPv4Address, IPv6Address


@dataclass(frozen=True, slots=True)
class FailedAuthenticationAttempt:
    """Uma tentativa de autenticação por senha recusada pelo OpenSSH."""

    timestamp: str
    occurred_at: datetime | None
    hostname: str
    process_id: int | None
    username: str
    invalid_user: bool
    source_ip: IPv4Address | IPv6Address
    source_port: int
    authentication_method: str
    raw_line: str


@dataclass(frozen=True, slots=True)
class BruteForceAlert:
    """Concentração de falhas que atingiu o limiar configurado."""

    source_ip: IPv4Address | IPv6Address
    window_started_at: datetime
    detected_at: datetime
    attempt_count: int
    usernames: tuple[str, ...]
