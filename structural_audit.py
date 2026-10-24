#!/usr/bin/env python3
"""Phase 1, tasks 1-2: source provenance and raw JSONL structure (Python 3.10+).

Standard library only. Raw files are read-only. No cleaning, model fitting,
record deduplication, quality/outlier analysis, or pandas type inference.
Identifier counts use a temporary SQLite database, not in-memory sets of users.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import math
import platform
import sqlite3
import sys
import tempfile
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from itertools import combinations
from pathlib import Path

UTC = timezone.utc
EPOCH = datetime(1970, 1, 1, tzinfo=UTC)
OFFICIAL_PAGE = "https://amazon-reviews-2023.github.io/"
COLLECTION_PAPER = "https://arxiv.org/html/2403.03952v2#A2"
HF = "https://huggingface.co/datasets/McAuley-Lab/Amazon-Reviews-2023"
PROJECT_CATEGORIES = [
    "All_Beauty", "Appliances", "Electronics", "Beauty_and_Personal_Care"
]
DEFAULT_CATEGORIES = ["All_Beauty", "Appliances"]
SCALES = {"s": 1, "ms": 1_000, "us": 1_000_000, "ns": 1_000_000_000}

# Local input files. With no command-line arguments these exact paths are used.
DATA_DIR = Path("/Users/parsaanvari/Downloads/DataAnalysis")
DATASETS = {
    "All_Beauty": DATA_DIR / "All_Beauty.jsonl",
    "Appliances": DATA_DIR / "Appliances.jsonl",
    "meta_All_Beauty": DATA_DIR / "meta_All_Beauty.jsonl",
    "meta_Appliances": DATA_DIR / "meta_Appliances.jsonl",
}

# Absolute default: the output location does not depend on the VS Code terminal's
# working directory or on where a copy of this script is saved.
OUTPUT_DIR = Path(
    "/Users/parsaanvari/Documents/ChatGPT/Data Analysis Project"
) / "reports" / "phase1" / "source_structure"

# These describe expected NON-NULL raw JSON types, not pandas dtypes.
# Presence, explicit null, empty containers and wrong types are counted separately.
REVIEW_SCHEMA = {
    "rating": (("integer", "number"), "ordinal", "Review star rating"),
    "title": (("string",), "text", "Review headline"),
    "text": (("string",), "text", "Review body"),
    "images": (("array",), "nested", "Reviewer image descriptors"),
    "asin": (("string",), "identifier", "Variant/product identifier"),
    "parent_asin": (("string",), "join_key", "Parent product identifier"),
    "user_id": (("string",), "identifier", "Reviewer identifier"),
    "timestamp": (("integer",), "temporal", "Review Unix epoch value"),
    "helpful_vote": (("integer",), "count", "Accumulated helpful-vote count"),
    "verified_purchase": (("boolean",), "binary", "Purchase verification flag"),
}
META_SCHEMA = {
    "main_category": (("string",), "categorical", "Product-page category"),
    "title": (("string",), "text", "Product title, not review title"),
    "average_rating": (("integer", "number"), "numeric", "Product-page mean rating"),
    "rating_number": (("integer",), "count", "Product-page number of ratings"),
    "features": (("array",), "nested", "Product feature statements"),
    "description": (("array",), "nested", "Product description elements"),
    "price": (("integer", "number"), "numeric", "USD price at crawl time"),
    "images": (("array",), "nested", "Product image descriptors"),
    "videos": (("array",), "nested", "Product video descriptors"),
    "store": (("string",), "categorical", "Store label"),
    "categories": (("array",), "nested", "Product category hierarchy"),
    "details": (("object",), "nested", "Variable product attributes"),
    "parent_asin": (("string",), "candidate_primary_key", "Parent product identifier"),
    "bought_together": (("array",), "nested", "Bundle relations if provided"),
}


def raw_type(value):
    """bool must be checked before int: isinstance(True, int) is True."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    raise TypeError(type(value).__name__)


def reject_non_json_constant(value):
    raise ValueError(f"Non-standard JSON constant: {value}")


def percent(numerator, denominator):
    return round(100 * numerator / denominator, 6) if denominator else None


def parse_utc(text):
    value = datetime.fromisoformat(text.replace("Z", "+00:00"))
    if value.tzinfo is None:
        raise ValueError("Use an explicit timezone, for example +00:00 or Z")
    return value.astimezone(UTC)


def parse_epoch(value, unit):
    """Explicit unit only; do not reinterpret strings or silently guess units."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None, "wrong_raw_type"
    if isinstance(value, float) and not math.isfinite(value):
        return None, "non_finite"
    try:
        seconds, remainder = divmod(value, SCALES[unit])
        result = EPOCH + timedelta(
            seconds=seconds, microseconds=remainder * (1_000_000 / SCALES[unit])
        )
        return result, None
    except (ValueError, OverflowError):
        return None, "outside_datetime_range"


def sha256_file(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def write_json(path, value):
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def write_csv(path, rows):
    if not rows:
        path.write_text("", encoding="utf-8-sig")
        return
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


class IdentifierIndex:
    """Disk-backed exact identifier and variant-parent counts, bounded batch size."""

    def __init__(self, path):
        self.db = sqlite3.connect(path)
        self.db.execute("PRAGMA cache_size=-32768")
        self.db.execute("PRAGMA temp_store=FILE")
        self.db.executescript("""
            CREATE TABLE ids (
                dataset TEXT, field TEXT, value TEXT, n INTEGER NOT NULL,
                PRIMARY KEY(dataset, field, value)
            ) WITHOUT ROWID;
            CREATE TABLE edges (
                dataset TEXT, asin TEXT, parent TEXT,
                PRIMARY KEY(dataset, asin, parent)
            ) WITHOUT ROWID;
        """)
        self.buffer = Counter()
        self.edges = set()

    def add(self, dataset, record, kind):
        fields = ("user_id", "asin", "parent_asin") if kind == "review" else ("parent_asin",)
        for field in fields:
            value = record.get(field)
            if isinstance(value, str) and value.strip():
                # Preserve the original identifier. Whitespace is not silently cleaned.
                self.buffer[(dataset, field, value)] += 1
        asin, parent = record.get("asin"), record.get("parent_asin")
        if kind == "review" and all(isinstance(v, str) and v.strip() for v in (asin, parent)):
            self.edges.add((dataset, asin, parent))

    def flush(self):
        self.db.executemany(
            "INSERT INTO ids VALUES (?, ?, ?, ?) "
            "ON CONFLICT(dataset, field, value) DO UPDATE SET n=n+excluded.n",
            ((*key, n) for key, n in self.buffer.items()),
        )
        self.db.executemany("INSERT OR IGNORE INTO edges VALUES (?, ?, ?)", self.edges)
        self.db.commit()
        self.buffer.clear()
        self.edges.clear()

    def scalar(self, query, params=()):
        return self.db.execute(query, params).fetchone()[0]

    def identifiers(self, dataset, kind, total_rows):
        fields = ("user_id", "asin", "parent_asin") if kind == "review" else ("parent_asin",)
        rows = []
        for field in fields:
            count, occurrences, repeated = self.db.execute(
                "SELECT COUNT(*), COALESCE(SUM(n),0), COALESCE(SUM(n>1),0) "
                "FROM ids WHERE dataset=? AND field=?", (dataset, field)
            ).fetchone()
            rows.append({
                "dataset": dataset, "field": field,
                "valid_nonblank_string_occurrences": occurrences,
                "rows_without_valid_identifier": total_rows - occurrences,
                "distinct_valid_values": count,
                "values_occurring_more_than_once": repeated,
                "repeated_occurrences_after_first": occurrences - count,
                "interpretation": (
                    "Candidate metadata key; repeats can multiply a join"
                    if kind == "meta" else "Repeated identifiers are not duplicate records"
                ),
            })
        return rows

    def variant_mapping(self, dataset):
        multi_parent = self.scalar(
            "SELECT COUNT(*) FROM (SELECT asin FROM edges WHERE dataset=? "
            "GROUP BY asin HAVING COUNT(*)>1)", (dataset,)
        )
        multi_variant = self.scalar(
            "SELECT COUNT(*) FROM (SELECT parent FROM edges WHERE dataset=? "
            "GROUP BY parent HAVING COUNT(*)>1)", (dataset,)
        )
        return {
            "distinct_asin_parent_pairs": self.scalar(
                "SELECT COUNT(*) FROM edges WHERE dataset=?", (dataset,)
            ),
            "asins_linked_to_multiple_parents": multi_parent,
            "parents_linked_to_multiple_asins": multi_variant,
        }

    def relationship(self, review, meta):
        matched_parents, matched_rows, ambiguous_rows, left_rows = self.db.execute("""
            SELECT COALESCE(SUM(m.value IS NOT NULL),0),
                   COALESCE(SUM(CASE WHEN m.value IS NOT NULL THEN r.n ELSE 0 END),0),
                   COALESCE(SUM(CASE WHEN m.n>1 THEN r.n ELSE 0 END),0),
                   COALESCE(SUM(r.n * COALESCE(m.n,1)),0)
            FROM ids r LEFT JOIN ids m
              ON m.dataset=? AND m.field='parent_asin' AND m.value=r.value
            WHERE r.dataset=? AND r.field='parent_asin'
        """, (meta["name"], review["name"])).fetchone()
        r_ids = review["identifiers"][-1]
        m_ids = meta["identifiers"][-1]
        meta_only = self.scalar("""
            SELECT COUNT(*) FROM ids m WHERE m.dataset=? AND m.field='parent_asin'
              AND NOT EXISTS (SELECT 1 FROM ids r WHERE r.dataset=?
                AND r.field='parent_asin' AND r.value=m.value)
        """, (meta["name"], review["name"]))
        return {
            "category": review["category"], "review_dataset": review["name"],
            "meta_dataset": meta["name"], "join_key": "parent_asin",
            "review_rows": review["object_rows"],
            "review_distinct_valid_parents": r_ids["distinct_valid_values"],
            "metadata_rows": meta["object_rows"],
            "metadata_distinct_valid_parents": m_ids["distinct_valid_values"],
            "metadata_parent_key_unique_and_complete": (
                m_ids["rows_without_valid_identifier"] == 0
                and m_ids["values_occurring_more_than_once"] == 0
                and meta["object_rows"] > 0
            ),
            "matched_review_parents": matched_parents,
            "unmatched_review_parents": r_ids["distinct_valid_values"] - matched_parents,
            "matched_review_rows": matched_rows,
            "unmatched_rows_with_valid_parent": r_ids["valid_nonblank_string_occurrences"] - matched_rows,
            "rows_without_valid_parent": r_ids["rows_without_valid_identifier"],
            "matched_percent_of_all_review_rows": percent(matched_rows, review["object_rows"]),
            "matched_percent_of_valid_review_parents": percent(matched_parents, r_ids["distinct_valid_values"]),
            "metadata_only_parents": meta_only,
            "review_rows_matching_multiple_metadata_rows": ambiguous_rows,
            "projected_left_join_rows_no_null_key_matching": left_rows + r_ids["rows_without_valid_identifier"],
            "local_files_fully_audited": review["complete"] and meta["complete"],
        }

    def overlaps(self, reviews):
        rows = []
        for a, b in combinations(reviews, 2):
            for field in ("parent_asin", "user_id", "asin"):
                shared = self.scalar("""
                    SELECT COUNT(*) FROM ids a JOIN ids b ON a.value=b.value
                    WHERE a.dataset=? AND b.dataset=? AND a.field=? AND b.field=?
                """, (a["name"], b["name"], field, field))
                rows.append({
                    "dataset_a": a["name"], "dataset_b": b["name"],
                    "identifier": field, "shared_distinct_values": shared,
                    "note": "Identifier overlap, not a count of duplicate review records",
                })
        return rows


def audit_file(category, kind, path, index, args, as_of, supplied_provenance):
    name = category if kind == "review" else f"meta_{category}"
    schema = REVIEW_SCHEMA if kind == "review" else META_SCHEMA
    start = datetime.now(UTC)
    before = path.stat()
    fingerprint = sha256_file(path)  # Exact stored bytes, including gzip if compressed.
    fields = defaultdict(Counter)
    types = defaultdict(Counter)
    nested = defaultdict(Counter)
    item_types = defaultdict(Counter)
    child_types = defaultdict(Counter)
    category_values = Counter()
    monthly = Counter()
    time_status = Counter()
    t_min = t_max = plausible_min = plausible_max = None
    low = parse_utc(args.reference_start)
    high = parse_utc(args.reference_end_exclusive)
    lines = objects = blanks = parse_errors = non_objects = 0
    key_widths = Counter()
    issues = []
    opener = gzip.open if path.suffix == ".gz" else open
    reached_eof = False
    with opener(path, "rb") as stream:
        while args.max_lines is None or lines < args.max_lines:
            raw = stream.readline()
            if not raw:
                reached_eof = True
                break
            lines += 1
            if not raw.strip():
                blanks += 1
                continue
            try:
                encoding = "utf-8-sig" if lines == 1 else "utf-8"
                record = json.loads(raw.decode(encoding), parse_constant=reject_non_json_constant)
            except (ValueError, UnicodeError, RecursionError) as error:
                parse_errors += 1
                if len(issues) < 10:
                    issues.append({"line": lines, "reason": type(error).__name__})
                continue
            if not isinstance(record, dict):
                non_objects += 1
                continue
            objects += 1
            key_widths[len(record)] += 1
            for field, value in record.items():
                stat = fields[field]
                stat["present"] += 1
                typ = raw_type(value)
                types[field][typ] += 1
                if value is None:
                    stat["null"] += 1
                elif isinstance(value, str):
                    stat["blank_string"] += int(not value.strip())
                    if field in ("asin", "parent_asin", "user_id"):
                        stat["surrounding_whitespace"] += int(value != value.strip())
                elif isinstance(value, list):
                    stat["empty_array"] += int(not value)
                elif isinstance(value, dict):
                    stat["empty_object"] += int(not value)
                if value is not None and field in schema and typ not in schema[field][0]:
                    stat["incompatible_nonnull_type"] += 1
                if isinstance(value, (list, dict)):
                    info = nested[field]
                    info["container_rows"] += 1
                    info["total_elements_or_keys"] += len(value)
                    info["max_length"] = max(info["max_length"], len(value))
                    if isinstance(value, list):
                        for item in value:
                            item_types[field][raw_type(item)] += 1
                            if isinstance(item, dict):
                                for key, child in item.items():
                                    child_types[(field, "array_object", key)][raw_type(child)] += 1
                    else:
                        for key, child in value.items():
                            child_types[(field, "object", key)][raw_type(child)] += 1
            index.add(name, record, kind)
            if kind == "meta" and isinstance(record.get("main_category"), str):
                category_values[record["main_category"]] += 1
            if kind == "review":
                if "timestamp" not in record:
                    time_status["absent"] += 1
                elif record["timestamp"] is None:
                    time_status["null"] += 1
                else:
                    date, reason = parse_epoch(record["timestamp"], args.timestamp_unit)
                    if reason:
                        time_status[reason] += 1
                    else:
                        time_status["convertible"] += 1
                        t_min = date if t_min is None else min(t_min, date)
                        t_max = date if t_max is None else max(t_max, date)
                        monthly[date.strftime("%Y-%m")] += 1
                        time_status["after_as_of"] += int(date > as_of)
                        if low <= date < high:
                            time_status["within_reference_window"] += 1
                            plausible_min = date if plausible_min is None else min(plausible_min, date)
                            plausible_max = date if plausible_max is None else max(plausible_max, date)
                        else:
                            time_status["outside_reference_window"] += 1
            if objects % args.batch_size == 0:
                index.flush()
            if args.progress_every and objects % args.progress_every == 0:
                print(f"{name}: {objects:,} JSON objects read", flush=True)
        if args.max_lines is not None and not reached_eof:
            reached_eof = not bool(stream.readline())
    index.flush()
    after = path.stat()
    unchanged = (before.st_size, before.st_mtime_ns) == (after.st_size, after.st_mtime_ns)
    directory = "review_categories" if kind == "review" else "meta_categories"
    logical_filename = path.name.removesuffix(".gz")
    supplied = supplied_provenance.get(path.name, {})
    all_fields = sorted(set(schema) | set(fields))
    field_rows = []
    for field in all_fields:
        s = fields[field]
        expected, role, description = schema.get(field, ((), "undocumented", "Observed extra field"))
        absent = objects - s["present"]
        field_rows.append({
            "dataset": name, "field": field, "logical_role": role,
            "description": description, "documented_field": field in schema,
            "expected_nonnull_raw_types": "|".join(expected),
            "observed_raw_types": json.dumps(dict(types[field]), sort_keys=True),
            "object_rows_denominator": objects,
            "present_rows": s["present"], "absent_key_rows": absent,
            "explicit_null_rows": s["null"], "blank_string_rows": s["blank_string"],
            "empty_array_rows": s["empty_array"], "empty_object_rows": s["empty_object"],
            "absent_or_null_percent": percent(absent + s["null"], objects),
            "incompatible_nonnull_type_rows": s["incompatible_nonnull_type"],
            "identifier_surrounding_whitespace_rows": s["surrounding_whitespace"],
        })
    temporal = {"status": "not_applicable_no_documented_review_timestamp"}
    if kind == "review":
        temporal = {
            "status": "computed_from_raw_review_records", "declared_unit": args.timestamp_unit,
            "timezone": "UTC", "counts": dict(time_status),
            "min_convertible_utc": t_min.isoformat() if t_min else None,
            "max_convertible_utc": t_max.isoformat() if t_max else None,
            "span_days": (t_max - t_min).total_seconds() / 86400 if t_min else None,
            "reference_start_inclusive": low.isoformat(),
            "reference_end_exclusive": high.isoformat(),
            "min_within_reference_utc": plausible_min.isoformat() if plausible_min else None,
            "max_within_reference_utc": plausible_max.isoformat() if plausible_max else None,
            "as_of_utc": as_of.isoformat(),
            "note": "Conversion is not proof of unit correctness; reference window is a flag, not a filter.",
        }
    return {
        "name": name, "category": category, "kind": kind,
        "complete": reached_eof and unchanged,
        "source": {
            "local_path": str(path.resolve()), "bytes_on_disk": before.st_size,
            "sha256_stored_bytes": fingerprint,
            "format": "JSONL.gz" if path.suffix == ".gz" else "JSONL",
            "encoding": "UTF-8; optional BOM on first line",
            "filesystem_mtime_utc_not_download_date": datetime.fromtimestamp(before.st_mtime, UTC).isoformat(),
            "audit_started_utc": start.isoformat(),
            "official_dataset_page": OFFICIAL_PAGE,
            "published_candidate_file_url": f"{HF}/resolve/main/raw/{directory}/{logical_filename}",
            "actual_download_url": supplied.get("actual_download_url"),
            "actual_downloaded_at_utc": supplied.get("actual_downloaded_at_utc"),
            "source_revision": supplied.get("source_revision"),
            "source_url_note": "Published URL is a reference; local origin/remote equality has not been independently verified.",
            "local_file_unchanged_during_audit": unchanged,
        },
        "physical_lines_scanned": lines, "blank_lines": blanks,
        "unreadable_or_invalid_json_lines": parse_errors, "non_object_json_lines": non_objects,
        "parse_issue_examples_no_review_content": issues,
        "object_rows": objects,
        "observed_column_union_count": len([f for f in fields if fields[f]["present"]]),
        "keys_per_record_distribution": dict(sorted(key_widths.items())),
        "documented_fields_never_observed": [f for f in schema if not fields[f]["present"]],
        "undocumented_fields_observed": sorted(set(fields) - set(schema)),
        "fields": field_rows,
        "nested": [
            {"field": f, **dict(nested[f]), "array_item_types": dict(item_types[f])}
            for f in sorted(nested)
        ],
        "nested_child_types": [
            {"field": f, "container_kind": container, "child_key": key,
             "raw_type_occurrences": dict(counts)}
            for (f, container, key), counts in sorted(child_types.items())
        ],
        "main_category_counts": dict(category_values.most_common()),
        "temporal": temporal,
        "monthly_counts": [{"month_utc": month, "rows": n} for month, n in sorted(monthly.items())],
        "identifiers": index.identifiers(name, kind, objects),
        "variant_mapping": index.variant_mapping(name) if kind == "review" else None,
    }


def provenance_context():
    return {
        "dataset": "Amazon Reviews'23", "collector": "McAuley Lab",
        "data_design": "observational; no randomized allocation or controlled intervention",
        "collection_method": (
            "Authors describe sampling user IDs from public Amazon pages and collecting associated review pages; "
            "this does not establish random sampling of buyers/products."
        ),
        "observation_units": {
            "review": "One collected review record; not one guaranteed distinct purchase",
            "meta": "One collected product metadata record; uniqueness is audited, not assumed",
        },
        "limits": [
            "Review writing and helpful voting are self-selected user activities.",
            "Item review histories may be incomplete, including recently posted reviews before cutoff.",
            "Helpful counts have unequal exposure and accumulation time; impressions/vote event times are absent.",
            "Metadata is a crawl-time snapshot; price and rating aggregates are not historical versions.",
            "File-category membership and metadata main_category are distinct fields.",
            "Collected review counts do not measure all purchases, returns, defects, or causal effects.",
        ],
        "global_documented_review_period": "May 1996 to September 2023; local ranges are measured separately",
        "sources": [OFFICIAL_PAGE, COLLECTION_PAPER, HF],
        "metadata_time_range": "Not derivable from these files without a documented timestamp/version history",
    }


def build_readable_report(result):
    lines = [
        "# منشأ و ساختار داده: All_Beauty و Appliances", "",
        "این خروجی فقط دو گام منشأ و ممیزی ساختار را پوشش می‌دهد. داده خام تغییر نکرده است.", "",
        "داده مشاهده‌ای و گردآوری‌کننده McAuley Lab است. نویسندگان، گردآوری کاربرمحور از صفحات عمومی را توصیف می‌کنند؛ انتخاب تصادفی خریداران یا آزمایش کنترل‌شده مستند نشده است.", "",
        "هر ردیف نقد یک نقد گردآوری‌شده است و تعداد خریدها را نشان نمی‌دهد. پوشش تاریخچه محصول ممکن است ناقص باشد؛ فرصت دریافت رأی مفید برابر نیست؛ فراداده نمایی در زمان خزش است.", "",
        "تاریخ دریافت واقعی نامعلوم با null ثبت می‌شود. mtime فایل تاریخ دریافت اثبات‌شده نیست. SHA-256 فقط نسخه محلی را مشخص می‌کند و به‌تنهایی تطابق با فایل منتشرشده را اثبات نمی‌کند.", "",
        "| فایل | ردیف JSON object | ستون مشاهده‌شده | کل فایل خوانده شد |", "|---|---:|---:|---|",
    ]
    for d in result["datasets"]:
        lines.append(f"| {d['name']} | {d['object_rows']:,} | {d['observed_column_union_count']} | {d['complete']} |")
    for d in result["datasets"]:
        lines.extend(["", f"## {d['name']}", ""])
        if d["kind"] == "review":
            t = d["temporal"]
            lines.append(f"بازه قابل تبدیل UTC: `{t['min_convertible_utc']}` تا `{t['max_convertible_utc']}`؛ واحد صریح: `{t['declared_unit']}`.")
            lines.append("این بازه مربوط به نقدهای گردآوری‌شده است؛ زمان خرید یا مدت خزش نیست. تبدیل‌پذیری و سازگاری نوع خام جداگانه گزارش شده‌اند.")
        else:
            lines.append("timestamp نقد برای فراداده انتظار نمی‌رود؛ بازه زمانی تاریخی این جدول از فایل قابل استخراج نیست.")
            lines.append("فراوانی main_category در JSON آمده است؛ با نام فایل یکی فرض نمی‌شود.")
        lines.append("شناسه‌ها: " + "; ".join(
            f"{row['field']} = {row['distinct_valid_values']:,} مقدار یکتا"
            for row in d["identifiers"]
        ))
    lines.extend(["", "## اتصال نقد و فراداده", ""])
    for r in result["relationships"]:
        lines.append(
            f"- {r['category']}: {r['matched_review_rows']:,} ردیف نقد با فراداده متناظر؛ "
            f"{r['metadata_only_parents']:,} parent فقط در فراداده؛ "
            f"{r['review_rows_matching_multiple_metadata_rows']:,} ردیف نقد با بیش از یک تطابق فراداده."
        )
    lines.extend([
        "", "```mermaid", "flowchart LR",
        '  AR["All_Beauty reviews"] -->|"parent_asin: validate many-to-one"| AM["All_Beauty metadata"]',
        '  PR["Appliances reviews"] -->|"parent_asin: validate many-to-one"| PM["Appliances metadata"]',
        "```", "",
        "title و images در نقد و فراداده معنای متفاوت دارند؛ در اتصال با پیشوند review_/product_ نگهداری شوند. عدد rating_number با تعداد ردیف نقد جمع‌آوری‌شده یکی فرض نمی‌شود.", "",
        "در schema.csv، absent_key و explicit_null و ظرف خالی جدا هستند؛ [] در images می‌تواند نبود پیوست را نشان دهد و خودبه‌خود خطای کیفیت نیست. نوع null بدون شواهد دیگر float نامیده نمی‌شود.", "",
        "repeated_occurrences_after_first تعداد تکرار شناسه است، نه تکرار رکورد و نه تعداد کاربران دارای چند نقد. فراوانی main_category نیز جامعه فایل را خودکار تغییر نمی‌دهد.", "",
        "صفر اختلاف نوع خام فقط درباره رکوردهای JSON قابل خواندن است. در صورت خطای خواندن، شمارش‌ها جای کل محتوای نامعلوم را نمی‌گیرند.", "",
        f"منابع: [صفحه رسمی]({OFFICIAL_PAGE})، [گردآوری داده]({COLLECTION_PAPER}).", "",
        "وضعیت فایل‌های غایب و خطاها: " + json.dumps(result["file_issues"], ensure_ascii=False), "",
    ])
    return "\n".join(lines)


def input_path(category, kind, override_dir=None):
    """Use DATASETS directly; --data-dir is an optional explicit override."""
    name = category if kind == "review" else f"meta_{category}"
    if override_dir is not None:
        path = override_dir / f"{name}.jsonl"
    else:
        path = Path(DATASETS.get(name, DATA_DIR / f"{name}.jsonl"))
    path = path.expanduser().resolve()
    if not path.exists() and path.suffix != ".gz":
        compressed = path.with_name(path.name + ".gz")
        if compressed.is_file():
            return compressed
    return path


def build_terminal_report(result):
    """Full audit presentation, including every nested path and monthly count.

    The exact same text is printed and saved as terminal_report.txt. Tables are
    not truncated; no rows or nested details are hidden by display settings.
    """
    parts = []

    def heading(title):
        parts.extend(["", "=" * 100, title, "=" * 100])

    def dump(title, value):
        parts.extend(["", title, json.dumps(value, ensure_ascii=False, indent=2)])

    def table(title, rows, columns=None):
        parts.extend(["", title])
        if not rows:
            parts.append("(none / موردی ثبت نشده است)")
            return
        columns = columns or [(key, key) for key in rows[0]]
        cells = []
        for row in rows:
            values = []
            for key, _ in columns:
                value = row.get(key)
                if isinstance(value, (dict, list)):
                    value = json.dumps(value, ensure_ascii=False, sort_keys=True)
                elif value is None:
                    value = "null"
                else:
                    value = str(value)
                values.append(value.replace("\n", "\\n").replace("\r", "\\r"))
            cells.append(values)
        widths = [max(len(label), *(len(row[i]) for row in cells)) for i, (_, label) in enumerate(columns)]
        parts.append(" | ".join(label.ljust(widths[i]) for i, (_, label) in enumerate(columns)))
        parts.append("-+-".join("-" * width for width in widths))
        parts.extend(" | ".join(value.ljust(widths[i]) for i, value in enumerate(row)) for row in cells)

    heading("PHASE 1: SOURCE PROVENANCE AND DATA STRUCTURE / منشأ و ساختار داده")
    parts.extend([
        f"Status: {result['status']}",
        f"Audit reference UTC: {result['audit_as_of_utc']}",
        "تمام نتایج این دو بخش در ادامه چاپ می‌شوند و عین همین متن در terminal_report.txt ذخیره می‌شود.",
        "بخش منشأ از منابع مستند ثبت شده؛ شمارش‌ها و ساختار از فایل‌های محلی محاسبه شده‌اند.",
        "داده مشاهده‌ای است؛ تخصیص تصادفی کاربران به محصول یا کنترل شرایط آزمایشی انجام نشده است.",
        "روش مستند: انتخاب شناسه کاربران از صفحات عمومی آمازون و گردآوری صفحات نقد مرتبط با آنان.",
        "واحد نقد: یک نقد گردآوری‌شده؛ واحد فراداده: یک رکورد محصول که یکتایی کلید آن بررسی می‌شود.",
        "محدودیت‌ها: خودانتخابی نقدنویسان؛ پوشش بالقوه ناقص نقدهای محصول؛ فرصت متفاوت دریافت رأی مفید؛ ثبت فراداده در زمان خزش.",
        "تاریخ دریافت واقعیِ نامعلوم با null ثبت می‌شود؛ زمان ویرایش فایل مدرک تاریخ دریافت نیست.",
    ])
    dump("[1] DOCUMENTED SOURCE CONTEXT / منشأ، واحد مشاهده و محدودیت‌ها", result["provenance_context"])
    table("[2] FILE OVERVIEW / نمای کلی چهار فایل", result["datasets"], [
        ("name", "dataset"), ("kind", "kind"), ("object_rows", "rows"),
        ("observed_column_union_count", "column_union"), ("complete", "fully_scanned"),
    ])
    for d in result["datasets"]:
        heading(f"DATASET: {d['name']}")
        dump("[A] FILE PROVENANCE / مسیر محلی، منبع و اثر انگشت فایل", d["source"])
        dump("[B] RECORD STRUCTURE / ساختار و خوانایی رکوردها", {
            key: d[key] for key in (
                "category", "kind", "complete", "physical_lines_scanned", "blank_lines",
                "unreadable_or_invalid_json_lines", "non_object_json_lines", "object_rows",
                "observed_column_union_count", "keys_per_record_distribution",
                "documented_fields_never_observed", "undocumented_fields_observed",
                "parse_issue_examples_no_review_content",
            )
        })
        table("[C1] FIELD TYPES AND MEANINGS / نوع خام و نقش متغیرها", d["fields"], [
            ("field", "field"), ("logical_role", "role"), ("description", "meaning"),
            ("documented_field", "documented"),
            ("expected_nonnull_raw_types", "expected_nonnull"),
            ("observed_raw_types", "observed_type_counts"),
        ])
        table("[C2] FIELD PRESENCE / غیبت، null و مقدار خالی به‌صورت جداگانه", d["fields"], [
            ("field", "field"), ("object_rows_denominator", "total_rows"),
            ("present_rows", "present"), ("absent_key_rows", "absent_key"),
            ("explicit_null_rows", "null"), ("blank_string_rows", "blank_string"),
            ("empty_array_rows", "empty_array"), ("empty_object_rows", "empty_object"),
            ("absent_or_null_percent", "absent_or_null_%"),
            ("incompatible_nonnull_type_rows", "wrong_nonnull_type"),
            ("identifier_surrounding_whitespace_rows", "id_whitespace"),
        ])
        table("[D] IDENTIFIERS / یکتایی و تکرار شناسه‌ها", d["identifiers"])
        parts.append("Repeated identifiers are not duplicate records / تکرار شناسه معادل تکرار رکورد نیست.")
        dump("[E] ASIN TO PARENT MAPPING / ارتباط گونه‌ها و محصول والد", d["variant_mapping"])
        dump("[F] TEMPORAL VARIABLES / بازه زمانی محاسبه‌شده از نقدها", d["temporal"])
        parts.append("Review date range is not purchase time or collection duration / بازه نقدها زمان خرید یا مدت خزش نیست.")
        table("[G] ALL MONTHLY COUNTS / تعداد نقدها در تمام ماه‌های مشاهده‌شده", d["monthly_counts"])
        table("[H1] NESTED CONTAINERS / ساختار فهرست‌ها و دیکشنری‌ها", d["nested"])
        table("[H2] ALL NESTED CHILD TYPES / تمام کلیدها و نوع‌های تو‌در‌تو", d["nested_child_types"])
        table("[I] MAIN CATEGORY VALUES / فراوانی برچسب‌های فراداده", [
            {"main_category": key, "rows": n} for key, n in d["main_category_counts"].items()
        ])
        parts.append("main_category null/absent counts are in C2 / مقادیر null یا غایب main_category در C2 هستند.")
    heading("RELATIONSHIPS AND OVERLAPS / ارتباط فایل‌ها و هم‌پوشانی‌ها")
    for relationship in result["relationships"]:
        dump(f"JOIN: {relationship['category']}", relationship)
    table("CROSS-CATEGORY IDENTIFIER OVERLAPS", result["cross_category_overlaps"])
    parts.extend([
        "", "Data flow / جریان داده:",
        "Local JSONL -> raw JSON records -> schema / identifiers / review timestamps",
        "Reviews -- parent_asin (many-to-one only after validation) --> Product metadata",
        "Files from different categories -> shared identifier counts",
        "title/images in reviews differ from title/images in product metadata.",
    ])
    dump("FILE ISSUES / فایل‌های غایب یا مشکلات ثبت‌شده", result["file_issues"])
    dump("RUN CONFIGURATION / تنظیمات اجرای ممیزی", result["configuration"])
    dump("RUNTIME / مشخصات محیط و نسخه کد", result["runtime"])
    heading("OUTPUT FILES: ABSOLUTE PATHS / آدرس کامل تک‌تک فایل‌های خروجی")
    parts.append("برای بازکردن هر فایل، مسیر کامل زیر را در VS Code یا Finder وارد کن.")
    for filename, path in result["output_files"].items():
        parts.extend([f"{filename}:", f"  {path}"])
    return "\n".join(parts) + "\n"


def save_and_display_results(result, output_dir):
    """Save machine-readable results and a complete terminal transcript."""
    output_dir = Path(output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    filenames = [
        "source_structure.json", "provenance_manifest.json", "schema.csv",
        "identifiers.csv", "monthly_counts.csv", "relationships.csv", "overlaps.csv",
        "report_fa.md", "terminal_report.txt",
    ]
    result["output_files"] = {name: str(output_dir / name) for name in filenames}
    write_json(output_dir / "source_structure.json", result)
    write_json(output_dir / "provenance_manifest.json", {
        "context": result["provenance_context"], "audit_as_of_utc": result["audit_as_of_utc"],
        "files": [{"dataset": d["name"], **d["source"]} for d in result["datasets"]],
        "file_issues": result["file_issues"],
    })
    write_csv(output_dir / "schema.csv", [r for d in result["datasets"] for r in d["fields"]])
    write_csv(output_dir / "identifiers.csv", [r for d in result["datasets"] for r in d["identifiers"]])
    write_csv(output_dir / "monthly_counts.csv", [
        {"dataset": d["name"], **r} for d in result["datasets"] for r in d["monthly_counts"]
    ])
    write_csv(output_dir / "relationships.csv", result["relationships"])
    write_csv(output_dir / "overlaps.csv", result["cross_category_overlaps"])
    (output_dir / "report_fa.md").write_text(build_readable_report(result), encoding="utf-8")
    terminal_text = build_terminal_report(result)
    (output_dir / "terminal_report.txt").write_text(terminal_text, encoding="utf-8")
    print(terminal_text, end="", flush=True)
    print(f"Saved: {output_dir} | status={result['status']}", flush=True)


def run(args):
    if args.batch_size < 1 or (args.max_lines is not None and args.max_lines < 1):
        raise ValueError("batch-size and max-lines must be positive")
    if parse_utc(args.reference_start) >= parse_utc(args.reference_end_exclusive):
        raise ValueError("Reference start must precede reference end")
    args.output_dir = args.output_dir.expanduser().resolve()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    provenance = json.loads(args.provenance_json.read_text()) if args.provenance_json else {}
    as_of = parse_utc(args.as_of) if args.as_of else datetime.now(UTC)
    result = {
        "scope": "Phase 1 source provenance and structural audit only",
        "project_categories": PROJECT_CATEGORIES, "assigned_categories": args.categories,
        "audit_as_of_utc": as_of.isoformat(),
        "runtime": {"python": sys.version, "platform": platform.platform(),
                    "sqlite": sqlite3.sqlite_version,
                    "script_sha256": sha256_file(Path(__file__))},
        "provenance_context": provenance_context(),
        "configuration": {k: str(v) if isinstance(v, Path) else v for k, v in vars(args).items()},
        "datasets": [], "relationships": [], "cross_category_overlaps": [], "file_issues": [],
    }
    result["configuration"]["resolved_input_files"] = {
        (category if kind == "review" else f"meta_{category}"): str(input_path(category, kind, args.data_dir))
        for category in args.categories for kind in ("review", "meta")
    }
    print(f"INPUT DIRECTORY: {args.data_dir or DATA_DIR}", flush=True)
    print(f"OUTPUT DIRECTORY (absolute): {args.output_dir}", flush=True)
    with tempfile.TemporaryDirectory(prefix="phase1-structure-") as temp:
        index = IdentifierIndex(Path(temp) / "identifiers.sqlite")
        try:
            for category in args.categories:
                for kind in ("review", "meta"):
                    name = category if kind == "review" else f"meta_{category}"
                    path = input_path(category, kind, args.data_dir)
                    if not path.is_file():
                        result["file_issues"].append({"dataset": name, "status": "file_missing"})
                        print(f"MISSING: {name}", flush=True)
                        continue
                    print(f"START: {path.name}", flush=True)
                    d = audit_file(category, kind, path, index, args, as_of, provenance)
                    result["datasets"].append(d)
                    print(f"DONE: {name}: {d['object_rows']:,} objects, complete={d['complete']}", flush=True)
            by_name = {d["name"]: d for d in result["datasets"]}
            for category in args.categories:
                if category in by_name and f"meta_{category}" in by_name:
                    result["relationships"].append(index.relationship(by_name[category], by_name[f"meta_{category}"]))
            reviews = [d for d in result["datasets"] if d["kind"] == "review"]
            result["cross_category_overlaps"] = index.overlaps(reviews)
        finally:
            index.db.close()
    all_complete = not result["file_issues"] and all(d["complete"] for d in result["datasets"])
    all_readable = all(
        d["unreadable_or_invalid_json_lines"] == 0 and d["non_object_json_lines"] == 0
        for d in result["datasets"]
    )
    result["status"] = "complete" if all_complete and all_readable else "incomplete_or_flagged"
    save_and_display_results(result, args.output_dir)
    return result


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--data-dir", type=Path, default=None,
                   help="Optional override; otherwise use the DATA_DIR/DATASETS paths at the top of the script")
    p.add_argument("--output-dir", type=Path, default=OUTPUT_DIR,
                   help="Absolute default is defined by OUTPUT_DIR; independent of terminal working directory")
    p.add_argument("--categories", nargs="+", choices=PROJECT_CATEGORIES, default=DEFAULT_CATEGORIES)
    p.add_argument("--timestamp-unit", choices=SCALES, default="ms")
    p.add_argument("--as-of", help="Fixed timezone-aware date/time for reproducible future-time flags")
    p.add_argument("--reference-start", default="1996-01-01T00:00:00+00:00")
    p.add_argument("--reference-end-exclusive", default="2023-10-01T00:00:00+00:00")
    p.add_argument("--provenance-json", type=Path, help="Optional known download facts by filename")
    p.add_argument("--max-lines", type=int, help="Debug only: partial-file audit, explicitly marked incomplete")
    p.add_argument("--batch-size", type=int, default=5000)
    p.add_argument("--progress-every", type=int, default=250000)
    return p


if __name__ == "__main__":
    try:
        report = run(parser().parse_args())
        sys.exit(0 if report["status"] == "complete" else 2)
    except (OSError, EOFError, ValueError, sqlite3.Error) as error:
        print(f"Audit failed; do not treat existing outputs as a new successful run: {error}", file=sys.stderr)
        sys.exit(1)

