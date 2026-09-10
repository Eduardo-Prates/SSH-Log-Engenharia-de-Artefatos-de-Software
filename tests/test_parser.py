import unittest
from datetime import UTC, datetime, timedelta, timezone
from ipaddress import ip_address

from ssh_log_sentinel.parser import parse_line, parse_lines


class ParseLineTests(unittest.TestCase):
    def test_parses_failed_password_for_existing_user(self) -> None:
        line = (
            "Jan 10 12:34:56 server sshd[1234]: "
            "Failed password for alice from 192.0.2.10 port 51000 ssh2\n"
        )

        event = parse_line(line)

        self.assertIsNotNone(event)
        assert event is not None
        self.assertEqual(event.timestamp, "Jan 10 12:34:56")
        self.assertIsNone(event.occurred_at)
        self.assertEqual(event.hostname, "server")
        self.assertEqual(event.process_id, 1234)
        self.assertEqual(event.username, "alice")
        self.assertFalse(event.invalid_user)
        self.assertEqual(event.source_ip, ip_address("192.0.2.10"))
        self.assertEqual(event.source_port, 51000)
        self.assertEqual(event.authentication_method, "password")
        self.assertFalse(event.raw_line.endswith("\n"))

    def test_parses_invalid_user_with_ipv6_and_iso_timestamp(self) -> None:
        line = (
            "2026-09-10T09:15:00-03:00 gateway sshd[77]: "
            "Failed password for invalid user admin from 2001:db8::10 "
            "port 60123 ssh2 [preauth]"
        )

        event = parse_line(line)

        self.assertIsNotNone(event)
        assert event is not None
        self.assertEqual(event.username, "admin")
        self.assertTrue(event.invalid_user)
        self.assertEqual(event.source_ip, ip_address("2001:db8::10"))
        self.assertEqual(
            event.occurred_at,
            datetime(2026, 9, 10, 12, 15, tzinfo=UTC),
        )

    def test_normalizes_syslog_timestamp_with_explicit_context(self) -> None:
        line = (
            "Jan 10 12:34:56 server sshd[1234]: "
            "Failed password for alice from 192.0.2.10 port 51000 ssh2"
        )

        event = parse_line(
            line,
            assumed_year=2026,
            default_timezone=timezone(timedelta(hours=-3)),
        )

        self.assertIsNotNone(event)
        assert event is not None
        self.assertEqual(
            event.occurred_at,
            datetime(2026, 1, 10, 15, 34, 56, tzinfo=UTC),
        )

    def test_ignores_accepted_authentication(self) -> None:
        line = (
            "Jan 10 12:34:56 server sshd[1234]: "
            "Accepted password for alice from 192.0.2.10 port 51000 ssh2"
        )

        self.assertIsNone(parse_line(line))

    def test_ignores_invalid_ip(self) -> None:
        line = (
            "Jan 10 12:34:56 server sshd[1234]: "
            "Failed password for alice from 999.0.2.10 port 51000 ssh2"
        )

        self.assertIsNone(parse_line(line))

    def test_ignores_port_outside_valid_range(self) -> None:
        line = (
            "Jan 10 12:34:56 server sshd[1234]: "
            "Failed password for alice from 192.0.2.10 port 70000 ssh2"
        )

        self.assertIsNone(parse_line(line))

    def test_parse_lines_preserves_only_supported_events_in_order(self) -> None:
        lines = [
            "Jan 10 12:00:00 host sshd[1]: noise\n",
            (
                "Jan 10 12:00:01 host sshd[1]: "
                "Failed password for first from 192.0.2.1 port 50001 ssh2\n"
            ),
            (
                "Jan 10 12:00:02 host sshd[1]: "
                "Failed password for second from 192.0.2.2 port 50002 ssh2\n"
            ),
        ]

        events = list(parse_lines(lines))

        self.assertEqual([event.username for event in events], ["first", "second"])

    def test_parse_lines_advances_year_after_december_to_january_rollover(self) -> None:
        lines = [
            (
                "Dec 31 23:59:30 host sshd[1]: Failed password for admin "
                "from 192.0.2.10 port 50001 ssh2\n"
            ),
            (
                "Jan  1 00:00:00 host sshd[1]: Failed password for admin "
                "from 192.0.2.10 port 50002 ssh2\n"
            ),
        ]

        events = list(parse_lines(lines, assumed_year=2026))

        self.assertEqual(
            [event.occurred_at for event in events],
            [
                datetime(2026, 12, 31, 23, 59, 30, tzinfo=UTC),
                datetime(2027, 1, 1, 0, 0, tzinfo=UTC),
            ],
        )


if __name__ == "__main__":
    unittest.main()
