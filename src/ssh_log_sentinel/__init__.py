"""SSH Log Sentinel: parsing de logs de autenticação OpenSSH."""

from .detector import detect_brute_force
from .models import BruteForceAlert, FailedAuthenticationAttempt
from .parser import TimestampNormalizer, normalize_timestamp, parse_line, parse_lines

__all__ = [
    "BruteForceAlert",
    "FailedAuthenticationAttempt",
    "TimestampNormalizer",
    "detect_brute_force",
    "normalize_timestamp",
    "parse_line",
    "parse_lines",
]
__version__ = "0.5.1"
