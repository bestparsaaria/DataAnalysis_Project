"""Shared, non-mutating contracts for Phase 1 audits (v2)."""
import hashlib
import json
import math
import re
from urllib.parse import urlsplit

CONTRACT_VERSION = "2.0.0"
SURROGATES = re.compile(r"[\ud800-\udfff]")


def valid_id(value):
    """Exact nonblank, Unicode-safe string; do not silently trim identifiers."""
    return (isinstance(value, str) and bool(value.strip())
            and value == value.strip() and not SURROGATES.search(value))


def usable_text(value):
    return isinstance(value, str) and bool(value.strip()) and not SURROGATES.search(value)


def finite_number(value):
    try:
        return type(value) in (int, float) and math.isfinite(value)
    except OverflowError:
        return False


def usable_url(value):
    if not usable_text(value) or any(c.isspace() for c in value):
        return False
    try:
        u = urlsplit(value)
        return u.scheme in ("https", "http") and bool(u.hostname)
    except ValueError:
        return False


def media_available(value, kind):
    keys = ("small_image_url", "medium_image_url", "large_image_url") if kind == "review" else ("thumb", "large", "hi_res")
    return isinstance(value, list) and any(isinstance(v, dict) and any(usable_url(v.get(k)) for k in keys) for v in value)


def text_list_available(value):
    return isinstance(value, list) and any(usable_text(v) for v in value)


def canonical(record):
    return json.dumps(record, sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False)


def fingerprint(record):
    text = canonical(record)
    return hashlib.sha256(text.encode()).digest(), text


def pct(n, d):
    return 100 * n / d if d else None


def markdown_table(rows, columns):
    """columns: sequence of (key, human-readable heading)."""
    def cell(v):
        if v is None: return "N/A"
        if isinstance(v, float): return f"{v:.4g}"
        return str(v).replace("|", "\\|").replace("\n", " ")
    return ["| " + " | ".join(label for _, label in columns) + " |",
            "| " + " | ".join("---" for _ in columns) + " |"] + [
                "| " + " | ".join(cell(r.get(k)) for k, _ in columns) + " |" for r in rows]