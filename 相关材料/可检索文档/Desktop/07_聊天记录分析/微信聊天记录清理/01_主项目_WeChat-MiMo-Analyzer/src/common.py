from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import unicodedata
from datetime import datetime
from pathlib import Path


SCHEMA_VERSION = "1.0"


def utc_now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def stable_hash(*parts: object, prefix: str = "") -> str:
    payload = "\x1f".join("" if part is None else str(part) for part in parts)
    return prefix + hashlib.sha256(payload.encode("utf-8", errors="replace")).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def json_text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def clean_text(value: object) -> str:
    text = json_text(value)
    text = unicodedata.normalize("NFC", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\x00", "")
    text = "".join(char for char in text if char in "\n\t" or unicodedata.category(char) != "Cc")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{4,}", "\n\n\n", text)
    return text.strip()


def normalize_timestamp(value: object) -> int:
    try:
        timestamp = int(float(value))
    except (TypeError, ValueError):
        return 0
    if timestamp > 10_000_000_000:
        timestamp //= 1000
    return timestamp if timestamp > 0 else 0


def display_time(timestamp: int) -> str:
    if not timestamp:
        return "未知时间"
    return datetime.fromtimestamp(timestamp).astimezone().strftime("%Y-%m-%d %H:%M:%S")


def connect_database(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA journal_mode = WAL")
    connection.execute("PRAGMA synchronous = NORMAL")
    connection.execute("PRAGMA temp_store = MEMORY")
    return connection


_PII_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("EMAIL", re.compile(r"(?i)(?<![\w.+-])[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}(?![\w.-])")),
    ("PHONE", re.compile(r"(?<!\d)(?:\+?86[- ]?)?1[3-9]\d{9}(?!\d)")),
    ("ID", re.compile(r"(?<!\d)\d{6}(?:18|19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{3}[0-9Xx](?!\d)")),
    ("BANK", re.compile(r"(?<!\d)(?:\d[ -]?){16,19}(?!\d)")),
    ("IP", re.compile(r"(?<!\d)(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|1?\d?\d)(?!\d)")),
)


def redact_for_model(text: str) -> tuple[str, int]:
    replacements = 0

    def replacement(label: str):
        def replace(match: re.Match[str]) -> str:
            nonlocal replacements
            replacements += 1
            token = stable_hash(match.group(0), prefix="")[:8]
            return f"<{label}:{token}>"

        return replace

    redacted = text
    for label, pattern in _PII_PATTERNS:
        redacted = pattern.sub(replacement(label), redacted)
    return redacted, replacements

