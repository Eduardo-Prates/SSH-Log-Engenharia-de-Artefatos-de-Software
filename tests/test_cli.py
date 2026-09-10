from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

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


if __name__ == "__main__":
    unittest.main()
