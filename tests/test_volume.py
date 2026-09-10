import unittest
from datetime import UTC, datetime, timedelta
from ipaddress import ip_address

from ssh_log_sentinel.detector import detect_brute_force
from ssh_log_sentinel.parser import parse_lines


def _synthetic_log(total_lines: int):
    started_at = datetime(2026, 1, 1, tzinfo=UTC)
    for line_number in range(total_lines):
        occurred_at = started_at + timedelta(seconds=line_number)
        timestamp = occurred_at.isoformat()
        if line_number % 10 == 0:
            attempt_number = line_number // 10
            source_ip = f"192.0.2.{attempt_number % 10 + 1}"
            username = f"user{attempt_number % 4}"
            port = 40000 + attempt_number
            yield (
                f"{timestamp} host sshd[{line_number + 1}]: "
                f"Failed password for invalid user {username} from {source_ip} "
                f"port {port} ssh2\n"
            )
        else:
            yield (
                f"{timestamp} host sshd[{line_number + 1}]: "
                "Accepted password for alice from 198.51.100.10 port 50000 ssh2\n"
            )


class SyntheticVolumeTests(unittest.TestCase):
    def test_processes_ten_thousand_mixed_lines_without_mixing_sources(self) -> None:
        events = list(parse_lines(_synthetic_log(10_000)))

        alerts = list(
            detect_brute_force(
                events,
                threshold=5,
                window=timedelta(seconds=400),
            )
        )

        self.assertEqual(len(events), 1_000)
        self.assertEqual(len(alerts), 10)
        self.assertEqual(
            {alert.source_ip for alert in alerts},
            {ip_address(f"192.0.2.{index}") for index in range(1, 11)},
        )


if __name__ == "__main__":
    unittest.main()
