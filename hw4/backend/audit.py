"""Append-only audit trail for Campus Customs agent runs and tool calls.

Events are stored as a JSON array in ``output/audit_trail.json``. Each write loads the
existing array, appends the new events, and atomically replaces the file, so earlier
runs are never removed. A file that cannot be parsed is preserved under a new name
instead of being overwritten.
"""

from __future__ import annotations

import json
import logging
import os
import re
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
AUDIT_PATH = PROJECT_ROOT / "output" / "audit_trail.json"
MAX_TEXT_LENGTH = 300

logger = logging.getLogger(__name__)
_lock = threading.Lock()

# Defense in depth: previews must never store credentials or personal identifiers.
_REDACTIONS = [
    (re.compile(r"pbkdf2_sha256\$[^\s\"']+"), "[redacted-hash]"),
    (re.compile(r"\b(?:sk|pk)-[A-Za-z0-9_\-]{12,}"), "[redacted-key]"),
    (re.compile(r"[^\s@\"']+@[^\s@\"']+\.[A-Za-z]{2,}"), "[redacted-email]"),
    (re.compile(r"\b(?:\d[ -]?){13,19}\b"), "[redacted-number]"),
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def preview(value: Any, limit: int = MAX_TEXT_LENGTH) -> str:
    """Return a short, redacted, single-line text version of any value."""
    if hasattr(value, "model_dump"):
        value = value.model_dump()
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, default=str)
    for pattern, replacement in _REDACTIONS:
        text = pattern.sub(replacement, text)
    text = " ".join(text.split())
    return text if len(text) <= limit else f"{text[: limit - 1]}…"


def _load_existing() -> list[dict[str, Any]]:
    if not AUDIT_PATH.exists():
        return []
    try:
        entries = json.loads(AUDIT_PATH.read_text(encoding="utf-8") or "[]")
        if isinstance(entries, list):
            return entries
    except (json.JSONDecodeError, UnicodeDecodeError):
        pass
    preserved = AUDIT_PATH.with_name(f"audit_trail.unreadable-{int(time.time())}.json")
    AUDIT_PATH.replace(preserved)
    logger.warning("Audit trail was unreadable; preserved it as %s and started a new file", preserved.name)
    return []


def append_events(events: list[dict[str, Any]]) -> None:
    """Append events to the audit trail. Failures are logged and never break a chat."""
    if not events:
        return
    try:
        with _lock:
            AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
            entries = _load_existing()
            entries.extend(events)
            temporary = AUDIT_PATH.with_suffix(".json.tmp")
            temporary.write_text(json.dumps(entries, indent=2, ensure_ascii=False), encoding="utf-8")
            os.replace(temporary, AUDIT_PATH)
    except OSError:
        logger.exception("Could not write the agent audit trail")
