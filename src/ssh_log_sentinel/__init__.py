"""SSH Log Sentinel: parsing de logs de autenticação OpenSSH."""

from .detector import detect_brute_force
from .models import BruteForceAlert, FailedAuthenticationAttempt
from .parser import normalize_timestamp, parse_line, parse_lines

__all__ = [
    "BruteForceAlert",
    "FailedAuthenticationAttempt",
    "detect_brute_force",
    "normalize_timestamp",
    "parse_line",
    "parse_lines",
]
__version__ = "0.2.0"
