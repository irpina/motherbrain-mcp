"""PII and secret redaction for audit log payloads.

Recursively walks dicts and lists before they are written to the event log.
Any key whose name matches a sensitive pattern has its value replaced with
"[REDACTED]". The pattern list is configurable via the REDACT_FIELDS
environment variable (comma-separated, case-insensitive substrings).

Default patterns cover the most common credential field names. Operators
running Motherbrain in regulated environments can extend the list.
"""

import os
import re
from typing import Any

_DEFAULT_PATTERNS = [
    "password", "passwd", "secret", "token", "api_key", "apikey",
    "authorization", "credential", "private_key", "access_key",
    "bearer", "auth", "ssn", "credit_card", "card_number",
]

def _build_pattern() -> re.Pattern:
    extra = [p.strip() for p in os.getenv("REDACT_FIELDS", "").split(",") if p.strip()]
    terms = _DEFAULT_PATTERNS + extra
    return re.compile("|".join(re.escape(t) for t in terms), re.IGNORECASE)

_PATTERN: re.Pattern = _build_pattern()


def redact(data: Any, _depth: int = 0) -> Any:
    """Return a copy of data with sensitive field values replaced.

    Handles nested dicts and lists. Stops at depth 10 to guard against
    pathologically deep structures.
    """
    if _depth > 10:
        return data
    if isinstance(data, dict):
        return {
            k: "[REDACTED]" if _PATTERN.search(str(k)) else redact(v, _depth + 1)
            for k, v in data.items()
        }
    if isinstance(data, list):
        return [redact(item, _depth + 1) for item in data]
    return data
