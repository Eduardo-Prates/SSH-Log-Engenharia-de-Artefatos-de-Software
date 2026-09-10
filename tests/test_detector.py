import unittest
from datetime import UTC, datetime, timedelta
from ipaddress import ip_address

from ssh_log_sentinel.detector import detect_brute_force
from ssh_log_sentinel.models import FailedAuthenticationAttempt

_BASE_TIME = datetime(2026, 9, 10, 12, 0, tzinfo=UTC)


def _event(
    seconds: int,
    *,
    source_ip: str = "192.0.2.10",
    username: str = "admin",
    normalized: bool = True,
) -> FailedAuthenticationAttempt:
    occurred_at = _BASE_TIME + timedelta(seconds=seconds) if normalized else None
    return FailedAuthenticationAttempt(
        timestamp=occurred_at.isoformat() if occurred_at else "Sep 10 12:00:00",
        occurred_at=occurred_at,
        hostname="server",
        process_id=1234,
        username=username,
        invalid_user=True,
        source_ip=ip_address(source_ip),
        source_port=51000,
        authentication_method="password",
        raw_line="linha de teste",
    )


class DetectBruteForceTests(unittest.TestCase):
    def test_alerts_when_source_reaches_threshold_inside_window(self) -> None:
        events = [_event(0, username="root"), _event(30), _event(60)]

        alerts = list(
            detect_brute_force(events, threshold=3, window=timedelta(seconds=60))
        )

        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0].source_ip, ip_address("192.0.2.10"))
        self.assertEqual(alerts[0].attempt_count, 3)
        self.assertEqual(alerts[0].window_started_at, _BASE_TIME)
        self.assertEqual(alerts[0].detected_at, _BASE_TIME + timedelta(seconds=60))
        self.assertEqual(alerts[0].usernames, ("root", "admin"))

    def test_does_not_mix_sources_or_alert_outside_window(self) -> None:
        events = [
            _event(0),
            _event(10, source_ip="192.0.2.20"),
            _event(40),
            _event(80),
        ]

        alerts = list(
            detect_brute_force(events, threshold=3, window=timedelta(seconds=60))
        )

        self.assertEqual(alerts, [])

    def test_emits_only_one_alert_per_continuous_burst(self) -> None:
        events = [_event(0), _event(10), _event(20), _event(30), _event(40)]

        alerts = list(
            detect_brute_force(events, threshold=3, window=timedelta(seconds=60))
        )

        self.assertEqual(len(alerts), 1)

    def test_rearms_after_quiet_interval(self) -> None:
        events = [_event(0), _event(10), _event(100), _event(110)]

        alerts = list(
            detect_brute_force(events, threshold=2, window=timedelta(seconds=60))
        )

        self.assertEqual(len(alerts), 2)

    def test_rejects_event_without_normalized_timestamp(self) -> None:
        with self.assertRaisesRegex(ValueError, "occurred_at"):
            list(detect_brute_force([_event(0, normalized=False)]))

    def test_rejects_out_of_order_events_from_same_source(self) -> None:
        with self.assertRaisesRegex(ValueError, "fora de ordem"):
            list(detect_brute_force([_event(10), _event(5)]))

    def test_rejects_invalid_configuration(self) -> None:
        with self.assertRaisesRegex(ValueError, "threshold"):
            list(detect_brute_force([], threshold=0))
        with self.assertRaisesRegex(ValueError, "window"):
            list(detect_brute_force([], window=timedelta(0)))


if __name__ == "__main__":
    unittest.main()
