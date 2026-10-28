#!/usr/bin/env python3
"""Read-only quality audit for two Amazon Reviews'23 review/metadata pairs.

Python 3.10+, NumPy for product-unit permutation comparisons. Full-file counts, SQLite-backed duplicate
checks, exact frequency-table quantiles. No cleaning or model fitting occurs.
See QUALITY_AUDIT_METHODS_EN.md for definitions, denominators and decisions.
"""
from __future__ import annotations

import argparse
import bisect
import csv
import gzip
import hashlib
import json
import math
import platform
import re
import shutil
import sqlite3
import sys
import tempfile
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlsplit

from audit_shared import valid_id, CONTRACT_VERSION, markdown_table
import quality_multimodal as multimodal

VERSION = "2.0.0"
UTC = timezone.utc
EPOCH = datetime(1970, 1, 1, tzinfo=UTC)
DATA_DIR = Path("/Users/parsaanvari/Downloads/DataAnalysis")
DATASETS = {name: DATA_DIR / (name + ".jsonl") for name in (
    "All_Beauty", "Appliances", "meta_All_Beauty", "meta_Appliances")}
OUTPUT_DIR = Path(__file__).resolve().parent / "reports" / "phase1" / "quality"
SOURCE_URL = "https://amazon-reviews-2023.github.io/"
NUM = ("integer", "number")
REVIEW_SCHEMA = {
    "rating": NUM, "title": ("string",), "text": ("string",),
    "images": ("array",), "asin": ("string",), "parent_asin": ("string",),
    "user_id": ("string",), "timestamp": ("integer",),
    "helpful_vote": ("integer",), "verified_purchase": ("boolean",),
}
META_SCHEMA = {
    "main_category": ("string",), "title": ("string",), "average_rating": NUM,
    "rating_number": ("integer",), "features": ("array",),
    "description": ("array",), "price": NUM, "images": ("array",),
    "videos": ("array",), "store": ("string",), "categories": ("array",),
    "details": ("object",), "parent_asin": ("string",),
    "bought_together": ("array",),
}
PLACEHOLDERS = {"null", "none", "nan", "n/a", "na", "unknown", "not available"}
ASIN_RE = re.compile(r"^[A-Z0-9]{10}$")
CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
SURROGATE_RE = re.compile(r"[\ud800-\udfff]")


def raw_type(v):
    if v is None: return "null"
    if isinstance(v, bool): return "boolean"
    if isinstance(v, int): return "integer"
    if isinstance(v, float): return "number"
    if isinstance(v, str): return "string"
    if isinstance(v, list): return "array"
    if isinstance(v, dict): return "object"
    raise TypeError(type(v).__name__)


def finite_number(v):
    return type(v) in (int, float) and (type(v) is int or math.isfinite(v))


def canonical(record):
    # Type-sensitive parsed-value equality; object order is ignored, list order kept.
    return json.dumps(record, sort_keys=True, ensure_ascii=True,
                      separators=(",", ":"), allow_nan=False)


def fingerprint(s):
    return hashlib.sha256(s.encode("utf-8", errors="surrogatepass")).digest()


def file_hash(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(8 * 1024 * 1024), b""): h.update(b)
    return h.hexdigest()


def percentage(n, d):
    return round(100 * n / d, 6) if d else None


def utc_date(s):
    dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
    if dt.tzinfo is None: raise ValueError("A timezone is required, e.g. Z or +00:00")
    return dt.astimezone(UTC)


def epoch_ms(v):
    if type(v) is not int: return None
    try:
        sec, ms = divmod(v, 1000)
        return EPOCH + timedelta(seconds=sec, milliseconds=ms)
    except (OverflowError, ValueError): return None


class DuplicateJSONKey(ValueError): pass


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result: raise DuplicateJSONKey("Duplicate JSON object key")
        result[key] = value
    return result


def finite_float(s):
    value = float(s)
    if not math.isfinite(value): raise ValueError("Non-finite numeric value")
    return value


def reject_constant(s):
    raise ValueError("Non-standard JSON constant")


def parse_record(raw, line):
    return json.loads(raw.decode("utf-8-sig" if line == 1 else "utf-8"),
                      object_pairs_hook=unique_object, parse_float=finite_float,
                      parse_constant=reject_constant)


def missing_decision(field, kind):
    if field in ("parent_asin", "rating", "timestamp") and (kind == "review" or field == "parent_asin"):
        return ("Quarantine from analyses requiring this field; recover from source if possible.",
                "The product key, observed target rating and chronology cannot be safely imputed.")
    if field in ("user_id", "asin"):
        return ("Retain with a flag; exclude from identity checks requiring this key.",
                "A missing secondary identifier does not by itself invalidate the product-level review.")
    if field in ("text", "title", "features", "description"):
        return ("Retain the review/product and flag unavailable text; no fabricated text.",
                "Dropping blank text would change the first-five review sequence and population.")
    if field == "price":
        return ("Keep missing and flag; do not replace with zero or a global mean.",
                "Unknown price is not free; current price is excluded from the historical predictor.")
    if field in ("images", "videos", "bought_together"):
        return ("Retain with an availability flag; empty collections are not parsing errors.",
                "No recorded media/link is not proof of corruption or successful online retrieval.")
    if field in ("rating_number", "average_rating"):
        return ("Keep missing; exclude this field from calculations that require it.",
                "Snapshot rating aggregates cannot be reconstructed from a potentially incomplete review file.")
    return ("Retain and report missingness; choose any later transformation on training data only.",
            "Missingness has field-specific meaning and does not justify blanket row deletion.")


# Every rule has a decision. Flags count affected records, not nested elements.
RULES = {
    "blank_line": ("parse", "warning", "Exclude the line from record counts; keep a file-level log.", "A blank line is not a JSON observation."),
    "invalid_json": ("parse", "error", "Quarantine the line and inspect/retrieve its source.", "Invalid UTF-8/JSON, non-finite literals or numeric overflow cannot be trusted as parsed records."),
    "duplicate_json_key": ("parse", "error", "Quarantine; inspect the raw line before resolving keys.", "Silently keeping the last repeated key loses information, including in nested objects."),
    "non_object_json": ("parse", "error", "Quarantine; expected one object per line.", "An array or scalar is not a review/product record."),
    "rating_out_of_range": ("value", "error", "Exclude this rating from target and sequence construction pending recovery.", "Review stars must lie in [1,5]."),
    "rating_fractional": ("value", "error", "Quarantine the review rating; do not round automatically.", "This project uses discrete one-to-five review stars."),
    "average_rating_out_of_range": ("value", "error", "Mark the aggregate unusable pending source inspection; retain the product.", "A displayed average outside [1,5] violates the adopted domain; zero may be a source sentinel."),
    "negative_count": ("value", "error", "Treat the affected count as invalid; retain other valid fields.", "Votes and rating counts cannot be negative."),
    "fractional_count": ("value", "error", "Inspect the count; do not round automatically.", "Counts describe whole events."),
    "negative_price": ("value", "error", "Flag price as invalid for price analysis; retain the product.", "A listed product price is expected to be nonnegative."),
    "zero_price": ("value", "warning", "Inspect as a possible free price, promotion or sentinel; do not delete automatically.", "Zero is suspicious in this setting but not logically impossible."),
    "numeric_exceeds_float_range": ("value", "warning", "Inspect the value; omit it from floating-point summaries without altering the raw record.", "An arbitrary-size JSON integer can be parsed but exceed supported statistical arithmetic."),
    "timestamp_unrepresentable": ("value", "error", "Quarantine chronology until unit/source is checked.", "An integer millisecond epoch must convert to a supported UTC datetime."),
    "timestamp_after_as_of": ("value", "error", "Quarantine chronology and investigate units/source.", "A review time after the declared audit reference is inconsistent with this snapshot audit."),
    "timestamp_outside_release_window": ("value", "warning", "Inspect the unit and release coverage; do not silently filter.", "The documented release window is a plausibility flag, not evidence that every outside value is corrupt."),
    "identifier_whitespace": ("identity", "warning", "Inspect and log any later trimming before rechecking collisions.", "Whitespace can break a join; silent normalization can merge distinct raw keys."),
    "asin_format_unusual": ("identity", "warning", "Inspect the identifier and retain unless invalidity is confirmed.", "Ten uppercase alphanumeric characters is a screening convention, not a proof of product identity."),
    "placeholder_string": ("text", "warning", "Review context before recoding as missing.", "Literal words such as 'none' can be meaningful review content."),
    "replacement_character": ("text", "warning", "Retain and inspect encoding; preserve the original text.", "U+FFFD can indicate decoding loss but is not a language label."),
    "control_character": ("text", "warning", "Inspect before a logged text-normalization step.", "Unusual controls may affect tokenization; tabs/newlines are not flagged."),
    "unpaired_surrogate": ("text", "error", "Inspect encoding; do not use this identifier until repaired.", "A lone surrogate is not a valid Unicode scalar and can break downstream encoders."),
    "wrong_nested_item_type": ("nested", "error", "Flag the affected collection; inspect malformed members individually.", "Text lists and media-object lists have different contracts."),
    "blank_nested_text": ("nested", "warning", "Retain the product; ignore blank text elements only in a documented derived view.", "A nonempty list may still contain unavailable text."),
    "no_usable_nested_text": ("nested", "warning", "Flag this nonempty text collection as unavailable for text features.", "List presence does not guarantee any usable string."),
    "empty_media_object": ("nested", "warning", "Retain the record and mark this media descriptor unavailable.", "An empty descriptor is not a usable image/video."),
    "wrong_media_child_type": ("nested", "error", "Inspect descriptor fields; do not coerce silently.", "Recognized media attributes are expected to be strings or explicit nulls."),
    "malformed_media_url": ("nested", "warning", "Flag URL for inspection; do not claim network availability.", "A nonblank URL must have an HTTP(S) scheme and host to pass syntax screening."),
    "media_without_usable_url": ("nested", "warning", "Mark that descriptor as locally unavailable; retain the review/product.", "No syntactically usable recognized URL was found; the network is not queried."),
    "no_usable_media_in_nonempty_list": ("nested", "warning", "Flag list availability separately from list presence.", "A populated list can contain only malformed or empty descriptors."),
    "blank_detail_key": ("nested", "warning", "Inspect the attribute dictionary; do not merge unnamed attributes.", "A blank attribute name cannot be interpreted reliably."),
    "detail_name_collision": ("nested", "warning", "Review keys before any mapping; preserve raw names/values.", "Case/whitespace normalization would merge keys inside this record."),
}


class IssueLog:
    def __init__(self):
        self.counts = Counter()
        self.examples = defaultdict(list)
        self.tested = set()

    def add_record(self, flags, line):
        for key in flags:  # set: each (rule,field) counted once per record
            self.counts[key] += 1
            if len(self.examples[key]) < 5: self.examples[key].append(line)

    def rows(self, name, n, lines):
        rows = []
        for rule, field in sorted(self.tested | set(self.counts)):
            family, severity, decision, reason = RULES[rule]
            denom = lines if family == "parse" else n
            count = self.counts[(rule, field)]
            rows.append(dict(dataset=name, rule=rule, field=field, dimension=family,
                             severity=severity, affected_rows=count, denominator=denom,
                             denominator_unit="physical lines" if family == "parse" else "parsed object records",
                             percent=percentage(count, denom), example_source_lines=self.examples[(rule, field)],
                             initial_decision=decision, rationale=reason))
        return rows


def url_usable(v):
    if not isinstance(v, str) or not v.strip(): return False
    try:
        parsed = urlsplit(v)
        return parsed.scheme.lower() in ("http", "https") and bool(parsed.hostname) and not any(c.isspace() for c in v)
    except ValueError: return False


def inspect_nested(record, kind, flags, tested):
    text_lists = ("features", "description", "categories", "bought_together") if kind == "meta" else ()
    for field in text_lists:
        for rule in ("wrong_nested_item_type", "blank_nested_text", "no_usable_nested_text"):
            tested.add((rule, field))
        v = record.get(field)
        if not isinstance(v, list): continue
        if any(not isinstance(x, str) for x in v): flags.add(("wrong_nested_item_type", field))
        if any(isinstance(x, str) and not x.strip() for x in v): flags.add(("blank_nested_text", field))
        if v and not any(isinstance(x, str) and x.strip() for x in v): flags.add(("no_usable_nested_text", field))
    for field in (("images", "videos") if kind == "meta" else ("images",)):
        for rule in ("wrong_nested_item_type", "empty_media_object", "wrong_media_child_type",
                     "malformed_media_url", "media_without_usable_url", "no_usable_media_in_nonempty_list"):
            tested.add((rule, field))
        v = record.get(field)
        if not isinstance(v, list): continue
        urls = ("url",) if field == "videos" else (("thumb", "large", "hi_res") if kind == "meta" else
                                                   ("small_image_url", "medium_image_url", "large_image_url"))
        text_children = (*urls, "title", "user_id") if field == "videos" else (*urls, "variant", "attachment_type")
        usable = False
        for item in v:
            if not isinstance(item, dict):
                flags.add(("wrong_nested_item_type", field)); continue
            if not item: flags.add(("empty_media_object", field))
            if any(k in item and item[k] is not None and not isinstance(item[k], str) for k in text_children):
                flags.add(("wrong_media_child_type", field))
            if any(isinstance(item.get(k), str) and item[k].strip() and not url_usable(item[k]) for k in urls):
                flags.add(("malformed_media_url", field))
            item_usable = any(url_usable(item.get(k)) for k in urls)
            if not item_usable: flags.add(("media_without_usable_url", field))
            usable |= item_usable
        if v and not usable: flags.add(("no_usable_media_in_nonempty_list", field))
    if kind == "meta":
        for rule in ("blank_detail_key", "detail_name_collision"): tested.add((rule, "details"))
        details = record.get("details")
        if isinstance(details, dict):
            if any(not k.strip() for k in details): flags.add(("blank_detail_key", "details"))
            keys = [k.strip().casefold() for k in details]
            if len(set(keys)) < len(keys): flags.add(("detail_name_collision", "details"))


def inspect_values(record, kind, flags, tested, hist, args, as_of):
    numeric_rules = {"rating": ("rating_out_of_range", "rating_fractional"),
                     "helpful_vote": ("negative_count", "fractional_count")} if kind == "review" else {
                     "average_rating": ("average_rating_out_of_range",),
                     "rating_number": ("negative_count", "fractional_count"), "price": ("negative_price", "zero_price")}
    schema = REVIEW_SCHEMA if kind == "review" else META_SCHEMA
    for field, rules in numeric_rules.items():
        tested.update((rule, field) for rule in rules)
        tested.add(("numeric_exceeds_float_range", field))
        v = record.get(field)
        if not finite_number(v): continue  # wrong types counted separately, never silently coerced
        if abs(v) > sys.float_info.max:
            flags.add(("numeric_exceeds_float_range", field))
        if field == "rating":
            if not 1 <= v <= 5: flags.add(("rating_out_of_range", field))
            if v % 1: flags.add(("rating_fractional", field))
        elif field == "average_rating":
            if not 1 <= v <= 5: flags.add(("average_rating_out_of_range", field))
        elif field in ("helpful_vote", "rating_number"):
            if v < 0: flags.add(("negative_count", field))
            if v % 1: flags.add(("fractional_count", field))
        else:
            if v < 0: flags.add(("negative_price", field))
            if v == 0: flags.add(("zero_price", field))
        if raw_type(v) in schema[field] and not any((r, field) in flags for r in (*rules, "numeric_exceeds_float_range")):
            if field not in ("rating", "average_rating"): hist[field][v] += 1
    date = None
    if kind == "review":
        tested.update((r, "timestamp") for r in ("timestamp_unrepresentable", "timestamp_after_as_of", "timestamp_outside_release_window"))
        v = record.get("timestamp")
        if type(v) is int:
            date = epoch_ms(v)
            if date is None: flags.add(("timestamp_unrepresentable", "timestamp"))
            else:
                if date > as_of: flags.add(("timestamp_after_as_of", "timestamp"))
                if not args.reference_start <= date < args.reference_end:
                    flags.add(("timestamp_outside_release_window", "timestamp"))
    for field in (("asin", "parent_asin", "user_id") if kind == "review" else ("parent_asin",)):
        tested.add(("identifier_whitespace", field))
        v = record.get(field)
        if isinstance(v, str) and v != v.strip(): flags.add(("identifier_whitespace", field))
        if field in ("asin", "parent_asin"):
            tested.add(("asin_format_unusual", field))
            if isinstance(v, str) and v.strip() and not ASIN_RE.fullmatch(v): flags.add(("asin_format_unusual", field))
    for field, v in record.items():
        if not isinstance(v, str): continue
        for r in ("placeholder_string", "replacement_character", "control_character", "unpaired_surrogate"): tested.add((r, field))
        if v.strip().casefold() in PLACEHOLDERS: flags.add(("placeholder_string", field))
        if "\ufffd" in v: flags.add(("replacement_character", field))
        if CONTROL_RE.search(v): flags.add(("control_character", field))
        if SURROGATE_RE.search(v): flags.add(("unpaired_surrogate", field))
    if isinstance(record.get("title"), str): hist["title_characters"][len(record["title"])] += 1
    if kind == "review" and isinstance(record.get("text"), str):
        hist["text_characters"][len(record["text"])] += 1
        hist["text_whitespace_words"][len(record["text"].split())] += 1
    return date


class DiskRecords:
    def __init__(self, path):
        self.path = path
        self.db = sqlite3.connect(path)
        self.db.execute("PRAGMA cache_size=-32768")
        self.db.execute("PRAGMA temp_store=FILE")
        self.db.execute("CREATE TABLE records(line INTEGER PRIMARY KEY, fp BLOB, canonical TEXT, parent TEXT, asin TEXT, user TEXT, ts INTEGER, rating REAL, textfp BLOB, mask INTEGER, main_category TEXT)")
        self.buffer = []

    def add(self, line, record, date, kind="review", as_of=None):
        s = canonical(record)
        text = record.get("text")
        norm = " ".join(text.casefold().split()) if isinstance(text, str) else ""
        rating = record.get("rating")
        self.buffer.append((line, fingerprint(s), s,
            *[record.get(k) if valid_id(record.get(k)) else None for k in ("parent_asin", "asin", "user_id")],
            record.get("timestamp") if date else None,
            rating if finite_number(rating) and 1 <= rating <= 5 and rating % 1 == 0 else None,
            fingerprint(norm) if norm else None, multimodal.local_mask(record,kind,date,as_of),
            record.get("main_category") if multimodal.usable_text(record.get("main_category")) else None))
        if len(self.buffer) >= 5000: self.flush()

    def flush(self):
        self.db.executemany("INSERT INTO records VALUES (?,?,?,?,?,?,?,?,?,?,?)", self.buffer)
        self.db.commit(); self.buffer.clear()

    def prepare(self, kind):
        self.flush()
        self.db.execute("CREATE INDEX idx_fp ON records(fp)")
        self.db.execute("CREATE INDEX idx_parent ON records(parent)")
        if kind == "review":
            self.db.execute("CREATE INDEX idx_event ON records(user,asin,ts)")
            self.db.execute("CREATE INDEX idx_pair ON records(user,parent)")
            self.db.execute("CREATE INDEX idx_text ON records(textfp)")
            self.db.execute("CREATE INDEX idx_time ON records(parent,ts)")
        self.db.commit()

    def scalar(self, sql, params=()): return self.db.execute(sql, params).fetchone()[0]

    def duplicate_results(self, name, kind, n):
        output = []
        exact_groups = exact_rows = excess = collisions = 0
        examples = []
        for (fp,) in self.db.execute("SELECT fp FROM records GROUP BY fp HAVING count(*)>1"):
            groups = self.db.execute("SELECT count(*),min(line) FROM records WHERE fp=? GROUP BY canonical", (fp,)).fetchall()
            if len(groups) > 1: collisions += 1
            for count, first in groups:
                if count > 1:
                    exact_groups += 1; exact_rows += count; excess += count - 1
                    if len(examples) < 5: examples.append(first)
        def add(check, groups, involved, beyond, denominator, unit, decision, reason, **extra):
            output.append(dict(dataset=name, check=check, groups=groups, involved_rows=involved,
                               rows_after_first_in_group=beyond, denominator_rows=denominator,
                               denominator_unit=unit, involved_percent=percentage(involved, denominator),
                               after_first_percent=percentage(beyond, denominator), initial_decision=decision, rationale=reason, **extra))
        add("exact_parsed_record_duplicates", exact_groups, exact_rows, excess, n, "all parsed object records",
            "Propose keeping the first source-line copy in a later derived dataset; no deletion in this audit.",
            "All parsed fields agree, including types and list order; whitespace/key order of JSON objects is ignored.",
            example_first_lines=examples, fingerprint_collision_groups=collisions)
        if kind == "meta":
            row = self.db.execute("SELECT count(*),coalesce(sum(n),0),coalesce(sum(n-1),0),coalesce(sum(v>1),0) FROM (SELECT count(*) n,count(DISTINCT canonical) v FROM records WHERE parent IS NOT NULL GROUP BY parent HAVING count(*)>1)").fetchone()
            add("repeated_metadata_parent", *row[:3], self.scalar("SELECT count(*) FROM records WHERE parent IS NOT NULL"), "records with nonblank string parent_asin",
                "Deduplicate identical copies later; quarantine conflicting parent versions from joins until reconciled.",
                "A metadata join needs one unambiguous row per parent. Never choose an arbitrary conflicting version.", conflicting_parent_groups=row[3])
        else:
            definitions = [
                ("candidate_review_event", "user,asin,ts", "user IS NOT NULL AND asin IS NOT NULL AND ts IS NOT NULL",
                 "Inspect non-identical records for the same user, variant and millisecond; do not automatically delete.",
                 "There is no documented review ID; this is a candidate event key, not guaranteed identity."),
                ("repeated_user_parent", "user,parent", "user IS NOT NULL AND parent IS NOT NULL",
                 "Retain unless a separate duplicate rule establishes identity.",
                 "A user can review variants or post different experiences; repeated keys are not exact duplicates."),
                ("normalized_text_repetition", "textfp", "textfp IS NOT NULL",
                 "Retain; inspect common phrases or potential template/reuse patterns separately.",
                 "Casefolded whitespace-collapsed body-text fingerprints are candidate similarity groups, not duplicate records."),
                ("same_parent_timestamp", "parent,ts", "parent IS NOT NULL AND ts IS NOT NULL",
                 "Inspect ordering after exact deduplication; apply frozen boundary rules when constructing the cohort.",
                 "Concurrent distinct reviews can make the fifth/sixth or fifteenth/sixteenth boundary ambiguous."),
            ]
            for check, cols, condition, decision, reason in definitions:
                detail = ",count(DISTINCT fp) v,count(DISTINCT rating) r" if check in ("candidate_review_event", "same_parent_timestamp") else ""
                query = f"SELECT count(*) n{detail} FROM records WHERE {condition} GROUP BY {cols} HAVING count(*)>1"
                groups = involved = beyond = nonidentical = rating_conflicts = 0
                for row in self.db.execute(query):
                    groups += 1; involved += row[0]; beyond += row[0]-1
                    if detail:
                        nonidentical += row[1] > 1; rating_conflicts += row[2] > 1
                extra = dict(nonidentical_fingerprint_groups=nonidentical, groups_with_different_valid_ratings=rating_conflicts) if detail else {}
                add(check, groups, involved, beyond, self.scalar(f"SELECT count(*) FROM records WHERE {condition}"),
                    "records with complete usable grouping keys", decision, reason, **extra)
        return output


def distribution(hist):
    pairs = sorted(hist.items())
    n = sum(hist.values())
    if not n: return dict(n=0)
    values = [x for x, _ in pairs]
    cumulative = []
    count = 0
    for _, f in pairs: count += f; cumulative.append(count)
    def quantile(q):
        pos = (n-1)*q; lo = math.floor(pos); hi = math.ceil(pos); frac = pos-lo
        a = values[bisect.bisect_right(cumulative, lo)]
        b = values[bisect.bisect_right(cumulative, hi)]
        return a*(1-frac)+b*frac
    scale = max(abs(values[0]), abs(values[-1])) or 1
    mean_scaled = math.fsum((x/scale)*(f/n) for x, f in pairs)
    variance_scaled = math.fsum(((x/scale)-mean_scaled)**2*(f/n) for x, f in pairs)
    return dict(n=n, zero_count=hist.get(0, 0), minimum=values[0], maximum=values[-1],
                mean=mean_scaled*scale, population_std=math.sqrt(variance_scaled)*scale,
                q1=quantile(.25), median=quantile(.5), q3=quantile(.75),
                p95=quantile(.95), p99=quantile(.99), p999=quantile(.999))


def outlier_result(hist, positive_log=False):
    reference = {x:f for x,f in hist.items() if x>0} if positive_log else hist
    transformed = Counter()
    for x, f in reference.items(): transformed[math.log1p(x) if positive_log else x] += f
    stats = distribution(transformed)
    multiplier = 3.0 if positive_log else 1.5
    result = dict(reference_n=stats["n"], multiplier=multiplier,
                  scale="log1p of strictly positive values" if positive_log else "raw values",
                  direction="upper tail only" if positive_log else "both tails")
    if stats["n"] < 4:
        return dict(result, status="unavailable_fewer_than_four_reference_values", flagged=None)
    iqr = stats["q3"] - stats["q1"]
    result.update(q1=stats["q1"], q3=stats["q3"], iqr=iqr)
    if iqr <= 0: return dict(result, status="unavailable_zero_iqr", flagged=None)
    lower = stats["q1"]-multiplier*iqr; upper=stats["q3"]+multiplier*iqr
    if not math.isfinite(lower) or not math.isfinite(upper):
        return dict(result, status="unavailable_fence_overflow", flagged=None)
    def beyond(x, boundary, upper_tail=True):
        # Algebraically equal log fences can differ by a few floating-point ULPs.
        # In particular log1p(31) and log(4)+3*(log(4)-log(2)) should be a tie.
        distance = (x-boundary) if upper_tail else (boundary-x)
        return distance > 8*max(math.ulp(x), math.ulp(boundary))
    flagged = sum(f for x,f in reference.items() if (beyond(math.log1p(x),upper) if positive_log else beyond(x,lower,False) or beyond(x,upper)))
    return dict(result, status="computed", lower_fence=None if positive_log else lower,
                upper_fence=upper, flagged=flagged, percent_of_reference=percentage(flagged, stats["n"]))


def numeric_rows(name, histograms):
    rows=[]
    for metric, hist in sorted(histograms.items()):
        stats=distribution(hist)
        raw=outlier_result(hist)
        pos=outlier_result(hist, True)
        count_like=metric in ("helpful_vote", "rating_number", "reviews_per_parent", "reviews_per_user")
        selected=pos if count_like else raw
        tail=sum(f for x,f in hist.items() if stats["n"] and x>stats["p99"])
        rows.append(dict(dataset=name, metric=metric, **stats, raw_iqr=raw, positive_log_iqr=pos,
                         primary_screen="positive_log_upper_3IQR" if count_like else "raw_two_sided_1.5IQR",
                         primary_flagged=selected["flagged"], primary_status=selected["status"],
                         primary_percent_of_all_valid=percentage(selected["flagged"],stats["n"]) if selected["flagged"] is not None else None,
                         strictly_above_p99=tail, above_p99_percent=percentage(tail, stats["n"]),
                         initial_decision="Retain flagged values; inspect context and use train-only transformations if later justified.",
                         rationale="Statistical extremes may be genuine. Degenerate IQR is not used to label every positive count as an error."))
    return rows


def inspect_file(name, path, db_path, args, as_of):
    kind="meta" if name.startswith("meta_") else "review"
    schema=META_SCHEMA if kind=="meta" else REVIEW_SCHEMA
    before=path.stat(); sha=file_hash(path)
    fields=defaultdict(Counter); types=defaultdict(Counter); hist=defaultdict(Counter)
    for f in (("price","rating_number","title_characters") if kind=="meta" else ("helpful_vote","text_characters","text_whitespace_words","title_characters")): hist[f]
    log=IssueLog(); log.tested.update((r,"<line>") for r in ("blank_line","invalid_json","duplicate_json_key","non_object_json"))
    disk=DiskRecords(db_path)
    n=lines=flagged_records=any_flagged_records=critical_unusable=0
    reached_eof=False
    opener=gzip.open if path.suffix==".gz" else open
    print(f"START: {name} | {path}",flush=True)
    try:
        with opener(path,"rb") as stream:
            while args.max_lines is None or lines<args.max_lines:
                raw=stream.readline()
                if not raw: reached_eof=True; break
                lines+=1
                if not raw.strip(): log.add_record({("blank_line","<line>")},lines); continue
                try: record=parse_record(raw,lines)
                except DuplicateJSONKey:
                    log.add_record({("duplicate_json_key","<line>")},lines); continue
                except (ValueError,UnicodeError,RecursionError):
                    log.add_record({("invalid_json","<line>")},lines); continue
                if not isinstance(record,dict): log.add_record({("non_object_json","<line>")},lines); continue
                n+=1; flags=set(); has_type_error=False
                for field,v in record.items():
                    s=fields[field]; typ=raw_type(v); types[field][typ]+=1; s["present"]+=1
                    if v is None: s["null"]+=1
                    elif isinstance(v,str): s["blank_string"]+=not v.strip()
                    elif isinstance(v,list): s["empty_array"]+=not v
                    elif isinstance(v,dict): s["empty_object"]+=not v
                    if v is not None and field in schema and typ not in schema[field]:
                        s["wrong_type"]+=1; has_type_error=True
                        if isinstance(v,str) and any(t in schema[field] for t in NUM):
                            try:
                                if math.isfinite(float(v)): s["numeric_string_candidate"]+=1
                            except (ValueError,OverflowError): pass
                date=inspect_values(record,kind,flags,log.tested,hist,args,as_of)
                inspect_nested(record,kind,flags,log.tested)
                log.add_record(flags,lines)
                flagged_records+=has_type_error or any(RULES[rule][0] in ("value","nested") for rule,field in flags)
                any_flagged_records+=bool(flags) or has_type_error
                if kind=="review":
                    rating=record.get("rating")
                    good_rating=finite_number(rating) and 1<=rating<=5 and rating%1==0
                    critical_unusable+=not (valid_id(record.get("parent_asin")) and good_rating and date is not None and date<=as_of)
                disk.add(lines,record,date,kind,as_of)
                if args.progress_every and n%args.progress_every==0: print(f"{name}: {n:,} objects checked",flush=True)
            if args.max_lines is not None and not reached_eof: reached_eof=not bool(stream.readline())
        print(f"{name}: building disk indexes and duplicate summaries",flush=True)
        disk.prepare(kind)
        duplicates=disk.duplicate_results(name,kind,n)
        if kind=="review":
            for col,metric in (("parent","reviews_per_parent"),("user","reviews_per_user")):
                hist[metric]
                for (count,) in disk.db.execute(f"SELECT count(*) FROM records WHERE {col} IS NOT NULL GROUP BY {col}"):
                    hist[metric][count]+=1
        frows=[]
        for f in sorted(set(schema)|set(fields)):
            s=fields[f]; absent=n-s["present"]; decision,reason=missing_decision(f,kind)
            frows.append(dict(dataset=name,field=f,documented_field=f in schema,
                expected_nonnull_types=list(schema.get(f,())),observed_raw_types=dict(types[f]),denominator_object_rows=n,
                present=s["present"],absent=absent,null=s["null"],blank_string=s["blank_string"],
                empty_array=s["empty_array"],empty_object=s["empty_object"],
                absent_or_null=absent+s["null"],absent_or_null_percent=percentage(absent+s["null"],n),
                absent_null_or_empty=absent+s["null"]+s["blank_string"]+s["empty_array"]+s["empty_object"],
                absent_null_or_empty_percent=percentage(absent+s["null"]+s["blank_string"]+s["empty_array"]+s["empty_object"],n),
                wrong_nonnull_type=s["wrong_type"],nonnull_present_denominator=s["present"]-s["null"],
                wrong_type_percent_of_objects=percentage(s["wrong_type"],n),
                wrong_type_percent_of_nonnull=percentage(s["wrong_type"],s["present"]-s["null"]),
                numeric_string_candidates=s["numeric_string_candidate"],
                missing_initial_decision=decision,missing_rationale=reason,
                type_initial_decision="Inspect a logged conversion or mark the field invalid; no silent coercion." if f in schema else "Profile only; no expected type contract for this extra field.",
                type_rationale="Preserve bool/number/string distinctions and verify meaning before conversion." if f in schema else "An extra field is not automatically an error."))
        after=path.stat(); unchanged=(before.st_size,before.st_mtime_ns)==(after.st_size,after.st_mtime_ns)
        result=dict(name=name,kind=kind,source=dict(path=str(path.resolve()),bytes=before.st_size,sha256=sha,
            unchanged_size_and_mtime=unchanged),complete=reached_eof and unchanged,
            physical_lines=lines,object_rows=n,records_with_value_nested_or_type_flag=flagged_records,
            records_with_any_content_or_type_flag=any_flagged_records,
            review_rows_unusable_for_ordering_before_dedup=critical_unusable if kind=="review" else None,
            fields=frows,issues=log.rows(name,n,lines),duplicates=duplicates,numeric=numeric_rows(name,hist))
        print(f"DONE: {name} | {n:,} objects | complete={result['complete']}",flush=True)
        return result
    finally: disk.db.close()


def cross_checks(results, paths):
    """Exact cross-file canonical equality and referential integrity; no raw output."""
    out=[]
    lookup={d["name"]:d for d in results}
    def connect(a,b):
        db=sqlite3.connect(paths[a]); db.execute("ATTACH DATABASE ? AS other",(str(paths[b]),)); return db
    for a,b in (("All_Beauty","Appliances"),("meta_All_Beauty","meta_Appliances")):
        if a not in lookup or b not in lookup: continue
        with connect(a,b) as db:
            row=db.execute("SELECT count(*),count(DISTINCT a.line),count(DISTINCT b.line) FROM records a JOIN other.records b ON a.fp=b.fp AND a.canonical=b.canonical").fetchone()
            groups=db.execute("SELECT count(*) FROM (SELECT a.fp,a.canonical FROM records a JOIN other.records b ON a.fp=b.fp AND a.canonical=b.canonical GROUP BY a.fp,a.canonical)").fetchone()[0]
        db.close()
        out.append(dict(check="cross_file_exact_duplicates",dataset_a=a,dataset_b=b,matching_pairs=row[0],
            involved_rows_a=row[1],involved_rows_b=row[2],distinct_shared_records=groups,
            denominator_a=lookup[a]["object_rows"],denominator_b=lookup[b]["object_rows"],
            percent_a=percentage(row[1],lookup[a]["object_rows"]),percent_b=percentage(row[2],lookup[b]["object_rows"]),
            complete=lookup[a]["complete"] and lookup[b]["complete"],
            initial_decision="Count identical cross-file copies once in a later global review table; retain category memberships.",
            rationale="Fingerprints narrow candidates; canonical strings are also compared, so a hash match alone is insufficient."))
    for cat in ("All_Beauty","Appliances"):
        meta="meta_"+cat
        if cat not in lookup or meta not in lookup: continue
        with connect(cat,meta) as db:
            missing=db.execute("SELECT count(*) FROM records r WHERE r.parent IS NOT NULL AND NOT EXISTS(SELECT 1 FROM other.records m WHERE m.parent=r.parent)").fetchone()[0]
            invalid=db.execute("SELECT count(*) FROM records WHERE parent IS NULL").fetchone()[0]
            multiple=db.execute("SELECT coalesce(sum(n),0) FROM (SELECT r.parent,count(*) n FROM records r WHERE r.parent IN (SELECT parent FROM other.records WHERE parent IS NOT NULL GROUP BY parent HAVING count(*)>1) GROUP BY r.parent)").fetchone()[0]
        db.close()
        out.append(dict(check="metadata_join_quality",category=cat,review_rows=lookup[cat]["object_rows"],
            missing_valid_parent_match=missing,invalid_parent_rows=invalid,review_rows_with_multiple_meta_matches=multiple,
            missing_valid_parent_match_percent_of_all_reviews=percentage(missing,lookup[cat]["object_rows"]),
            complete=lookup[cat]["complete"] and lookup[meta]["complete"],
            initial_decision="Use a validated left join; retain unmatched reviews with metadata flags. Resolve metadata duplicates before joining.",
            rationale="An inner join can drop reviews, and repeated metadata keys can inflate rows."))
    return out


def save_json(path,value):
    path.write_text(json.dumps(value,ensure_ascii=True,indent=2,allow_nan=False)+"\n",encoding="utf-8")


def save_csv(path,rows):
    columns=list(dict.fromkeys(k for row in rows for k in row))
    with path.open("w",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=columns); w.writeheader()
        for row in rows:
            w.writerow({k:json.dumps(v,ensure_ascii=True) if isinstance(v,(dict,list)) else v for k,v in row.items()})


def decision_rows(result):
    rows=[]
    for d in result["datasets"]:
        for f in d["fields"]:
            for dimension,count,decision,reason in (
                ("missing_or_empty",f["absent_null_or_empty"],f["missing_initial_decision"],f["missing_rationale"]),
                ("wrong_nonnull_type",f["wrong_nonnull_type"],f["type_initial_decision"],f["type_rationale"])):
                rows.append(dict(dataset=d["name"],dimension=dimension,field_or_check=f["field"],count=count,
                    denominator=f["denominator_object_rows"],percent=percentage(count,f["denominator_object_rows"]),
                    initial_decision=decision,rationale=reason,action_applied=False))
        for issue in d["issues"]:
            rows.append(dict(dataset=d["name"],dimension=issue["dimension"],field_or_check=issue["rule"]+":"+issue["field"],
                count=issue["affected_rows"],denominator=issue["denominator"],percent=issue["percent"],
                initial_decision=issue["initial_decision"],rationale=issue["rationale"],action_applied=False))
        for dup in d["duplicates"]:
            rows.append(dict(dataset=d["name"],dimension="duplicate_or_repeated_group",field_or_check=dup["check"],
                count=dup["involved_rows"],denominator=dup["denominator_rows"],percent=dup["involved_percent"],
                initial_decision=dup["initial_decision"],rationale=dup["rationale"],action_applied=False))
        for stat in d["numeric"]:
            rows.append(dict(dataset=d["name"],dimension="outlier_screen",field_or_check=stat["metric"],
                count=stat["primary_flagged"],denominator=stat["n"],percent=stat["primary_percent_of_all_valid"],
                initial_decision=stat["initial_decision"],rationale=stat["rationale"],action_applied=False))
    return rows


def render_report(result):
    lines=["# Quality Audit Results", "", f"Audit reference (UTC): {result['audit_as_of_utc']}", "",
           f"Execution status: **{result['status']}**. This is scan completion, not a declaration that data are clean.", "",
           "Raw files were read only. All decisions are proposals for a later logged transformation.", "",
           "## Summary", "", "| File | Objects | Extra exact copies | Critical review rows unusable before dedup |",
           "|---|---:|---:|---:|"]
    for d in result["datasets"]:
        dup=d["duplicates"][0]
        lines.append(f"| {d['name']} | {d['object_rows']:,} | {dup['rows_after_first_in_group']:,} | {d['review_rows_unusable_for_ordering_before_dedup']} |")
    lines += ["", "Critical review checks concern parent key, discrete stars and usable non-future timestamp. These checks do not establish an eligible prediction cohort.",
              "The narrow flagged-record counter is the union of value, nested and top-level type issues. The broader counter also includes identity and text rules. Neither is a deletion rule.", ""]
    for d in result["datasets"]:
        lines += ["## "+d["name"], "",
                  f"Value/nested/type union: **{d['records_with_value_nested_or_type_flag']:,}** of {d['object_rows']:,} objects. "
                  f"Any content/type flag union: **{d['records_with_any_content_or_type_flag']:,}**. "
                  "Missing-only cases, parse failures, duplicate status and statistical outliers have their own counts; they are not silently merged into these unions.", "",
                  "### Field coverage and type compatibility", ""]
        lines += markdown_table(d["fields"], [("field","Field"),("absent_null_or_empty","Missing/empty n"),("absent_null_or_empty_percent","Missing/empty %"),("wrong_nonnull_type","Wrong type n"),("missing_initial_decision","Initial missingness decision")])
        lines += ["", "### Nonzero validation flags", ""]
        lines += markdown_table([i for i in d["issues"] if i["affected_rows"]], [("rule","Rule"),("field","Field"),("dimension","Family"),("affected_rows","Affected n"),("denominator","Denominator"),("percent","%"),("initial_decision","Proposed decision")])
        lines += ["", "### Duplicate and repeated-key checks", ""]
        lines += markdown_table(d["duplicates"], [("check","Check"),("groups","Groups"),("involved_rows","Rows involved"),("rows_after_first_in_group","Rows beyond first"),("initial_decision","Proposed decision")])
        lines += ["", "### Statistical screening", ""]
        lines += markdown_table(d["numeric"], [("metric","Metric"),("n","Valid n"),("primary_flagged","Screened n"),("primary_percent_of_all_valid","% valid"),("initial_decision","Proposed decision")])
    lines += [""] + multimodal.report_lines(result.get("multimodal",{}))
    lines += ["", "## Interpretation and evidence", "",
              "Full exact pattern combinations, every zero/nonzero rule, denominators, example source lines, configuration, file hashes and rationales are preserved in quality_audit.json and the CSV tables. "
              "Issue totals overlap. A flag is a review request, not automatic row deletion. Missing URLs/prices do not invalidate the review. Statistical outliers may be genuine. "
              "Review ratings must be integral values 1–5 under the project contract (5.0 is accepted); product average_rating may be fractional. "
              "Identifiers must be exact nonblank strings without surrounding whitespace or lone surrogates in BOTH modules. "
              "Association tests cannot demonstrate MCAR, MAR or MNAR. Metadata fields are crawl-time observations, not automatically available at the historical prediction cutoff.", "",
              "Output paths:", ""]
    lines += [f"- `{path}`" for path in result["output_files"].values()]
    return "\n".join(lines)+"\n"


class Tee:
    def __init__(self,*streams): self.streams=streams
    def write(self,s):
        for stream in self.streams: stream.write(s)
        return len(s)
    def flush(self):
        for stream in self.streams: stream.flush()


def parser():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--data-dir",type=Path,help="Override DATASETS with four files in this folder; .jsonl.gz fallback supported.")
    p.add_argument("--output-dir",type=Path,default=OUTPUT_DIR)
    p.add_argument("--categories",nargs="+",choices=("All_Beauty","Appliances"),default=["All_Beauty","Appliances"])
    p.add_argument("--as-of",help="Fixed audit reference, explicit UTC/timezone ISO date-time; default current UTC.")
    p.add_argument("--reference-start",default="1996-05-01T00:00:00Z")
    p.add_argument("--reference-end",default="2023-10-01T00:00:00Z",help="Exclusive plausibility boundary.")
    p.add_argument("--max-lines",type=int,help="Debug cap PER FILE. Capped scans are labeled partial.")
    p.add_argument("--progress-every",type=int,default=250000)
    p.add_argument("--permutations",type=int,default=499,help="Product-unit exploratory permutations, fixed seed")
    p.add_argument("--work-dir",type=Path,help="Parent for temporary SQLite files; deleted after the run.")
    return p


def run(args):
    if args.max_lines is not None and args.max_lines<1: raise ValueError("max-lines must be positive")
    if args.progress_every<0: raise ValueError("progress-every must be nonnegative")
    if args.permutations<1: raise ValueError("permutations must be positive")
    as_of=utc_date(args.as_of) if args.as_of else datetime.now(UTC)
    args.reference_start=utc_date(args.reference_start); args.reference_end=utc_date(args.reference_end)
    if args.reference_start>=args.reference_end: raise ValueError("Invalid reference interval")
    out=args.output_dir.expanduser().resolve(); out.mkdir(parents=True,exist_ok=True)
    if args.work_dir: args.work_dir.mkdir(parents=True,exist_ok=True)
    names=list(dict.fromkeys(name for cat in args.categories for name in (cat,"meta_"+cat)))
    inputs={name:((args.data_dir/(name+".jsonl")) if args.data_dir else DATASETS[name]) for name in names}
    for name,path in inputs.items():
        if not path.exists() and Path(str(path)+".gz").exists(): inputs[name]=Path(str(path)+".gz")
    filenames=("terminal_report.txt","quality_audit.json","field_quality.csv","quality_issues.csv",
               "duplicate_summary.csv","numeric_summaries.csv","decision_register.csv",
               "cross_file_checks.json","QUALITY_AUDIT_REPORT_EN.md","quality_audit_executed.py",
               "modality_availability.json","conditional_missingness.csv","missingness_associations.csv",
               "audit_shared.py","quality_multimodal.py")
    output_files={f:str(out/f) for f in filenames}
    if Path(__file__).resolve()==(out/"quality_audit_executed.py").resolve():
        raise ValueError("Use a different output directory when running the preserved source snapshot")
    result=dict(scope="Phase 1 quality audit only; two review and two metadata files",audit_as_of_utc=as_of.isoformat(),
        runtime=dict(python=sys.version,platform=platform.platform(),sqlite=sqlite3.sqlite_version,
                     script_version=VERSION,script_sha256=file_hash(Path(__file__)),
                     shared_contract=CONTRACT_VERSION, helper_sha256={f:file_hash(Path(__file__).parent/f) for f in ("audit_shared.py","quality_multimodal.py")}),
        configuration=dict(input_paths={k:str(v.resolve()) for k,v in inputs.items()},timestamp_unit="ms",
                           reference_start=args.reference_start.isoformat(),reference_end_exclusive=args.reference_end.isoformat(),
                           max_lines=args.max_lines,progress_every=args.progress_every,permutations=args.permutations,
                           quantiles="exact frequency-weighted linear interpolation, index (n-1)*q",
                           source_url=SOURCE_URL),datasets=[],cross_file_checks=[],errors=[],output_files=output_files)
    original_stdout=sys.stdout
    with (out/"terminal_report.txt").open("w",encoding="utf-8") as terminal:
        sys.stdout=Tee(original_stdout,terminal)
        try:
            print(f"QUALITY AUDIT v{VERSION} | UTC reference {as_of.isoformat()}")
            print("Read-only inputs; no rows are changed or removed. Decisions are proposals.")
            with tempfile.TemporaryDirectory(prefix="amazon-quality-",dir=args.work_dir) as td:
                paths={name:Path(td)/(name+".sqlite") for name in names}
                for name,path in inputs.items():
                    if not path.is_file():
                        result["errors"].append(dict(dataset=name,error="input_file_not_found",path=str(path))); continue
                    try: result["datasets"].append(inspect_file(name,path,paths[name],args,as_of))
                    except (OSError,sqlite3.Error,ValueError,OverflowError) as e:
                        result["errors"].append(dict(dataset=name,error=type(e).__name__,message=str(e)))
                        print(f"FAILED: {name}: {type(e).__name__}: {e}",flush=True)
                print("Computing cross-file duplicate and metadata-match checks",flush=True)
                result["cross_file_checks"]=cross_checks(result["datasets"],paths)
                print("Computing joined availability and product-unit missingness associations",flush=True)
                result["multimodal"]=multimodal.joined_audit(result["datasets"],paths,out,args.permutations)
                for f in result["multimodal"]["files"]: result["output_files"][Path(f).name]=f
            result["status"]="failed" if result["errors"] else ("complete" if all(d["complete"] for d in result["datasets"]) else "partial")
            save_json(out/"quality_audit.json",result)
            save_json(out/"modality_availability.json",result["multimodal"])
            save_csv(out/"conditional_missingness.csv",result["multimodal"]["conditional_missingness"])
            save_csv(out/"missingness_associations.csv",result["multimodal"]["association_tests"])
            for f in ("audit_shared.py","quality_multimodal.py"): shutil.copyfile(Path(__file__).parent/f,out/f)
            for name,key in (("field_quality.csv","fields"),("quality_issues.csv","issues"),("duplicate_summary.csv","duplicates"),("numeric_summaries.csv","numeric")):
                save_csv(out/name,[r for d in result["datasets"] for r in d[key]])
            save_csv(out/"decision_register.csv",decision_rows(result))
            save_json(out/"cross_file_checks.json",result["cross_file_checks"])
            report=render_report(result)
            (out/"QUALITY_AUDIT_REPORT_EN.md").write_text(report,encoding="utf-8")
            shutil.copyfile(Path(__file__),out/"quality_audit_executed.py")
            print("\n"+report)
            print("OUTPUT FILES (absolute paths):")
            for name,path in output_files.items(): print(f"{name}: {path}")
            print(f"Saved: {out} | status={result['status']}")
        finally: sys.stdout=original_stdout
    return result


if __name__=="__main__":
    result=run(parser().parse_args())
    raise SystemExit(0 if result["status"]=="complete" else 2)
