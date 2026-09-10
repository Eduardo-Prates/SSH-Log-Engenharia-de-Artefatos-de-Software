"""Detecção de concentrações de falhas, independente da interface CLI."""

from collections import deque
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from ipaddress import IPv4Address, IPv6Address

from .models import BruteForceAlert, FailedAuthenticationAttempt


@dataclass(slots=True)
class _SourceState:
    attempts: deque[FailedAuthenticationAttempt] = field(default_factory=deque)
    last_seen_at: datetime | None = None
    alert_emitted_for_burst: bool = False


def detect_brute_force(
    events: Iterable[FailedAuthenticationAttempt],
    *,
    threshold: int = 5,
    window: timedelta = timedelta(minutes=5),
) -> Iterator[BruteForceAlert]:
    """Emite um alerta quando um IP atinge ``threshold`` falhas em ``window``.

    Um fluxo contínuo produz somente um alerta por IP. Um novo alerta pode ser
    emitido depois de um intervalo sem falhas desse IP maior que ``window``.
    Os eventos de cada IP devem estar em ordem cronológica e possuir
    ``occurred_at`` normalizado.
    """

    if threshold < 1:
        raise ValueError("threshold deve ser maior ou igual a 1")
    if window <= timedelta(0):
        raise ValueError("window deve ser positiva")

    states: dict[IPv4Address | IPv6Address, _SourceState] = {}

    for event in events:
        if event.occurred_at is None:
            raise ValueError("todos os eventos devem possuir occurred_at")

        state = states.setdefault(event.source_ip, _SourceState())
        if state.last_seen_at is not None and event.occurred_at < state.last_seen_at:
            raise ValueError("eventos do mesmo IP estão fora de ordem cronológica")

        if (
            state.last_seen_at is not None
            and event.occurred_at - state.last_seen_at > window
        ):
            state.attempts.clear()
            state.alert_emitted_for_burst = False

        state.last_seen_at = event.occurred_at
        cutoff = event.occurred_at - window
        while state.attempts and state.attempts[0].occurred_at < cutoff:
            state.attempts.popleft()
        state.attempts.append(event)

        if len(state.attempts) >= threshold and not state.alert_emitted_for_burst:
            usernames = tuple(dict.fromkeys(item.username for item in state.attempts))
            yield BruteForceAlert(
                source_ip=event.source_ip,
                window_started_at=state.attempts[0].occurred_at,
                detected_at=event.occurred_at,
                attempt_count=len(state.attempts),
                usernames=usernames,
            )
            state.alert_emitted_for_burst = True
