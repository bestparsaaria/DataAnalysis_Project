#!/usr/bin/env python3
"""Read-only, full-file univariate EDA for Amazon Reviews'23.

Run: python univariate_eda.py
Dependencies: python -m pip install -r requirements_univariate.txt
All report prose, tables and figures are regenerated on each run. No raw data
are changed or used to train a model. Exact deduplication is a derived sensitivity view.
"""
from __future__ import annotations

import argparse
import bisect
import csv
import gzip
import hashlib
import json
import math
import os
import platform
import shutil
import sys
import textwrap
import time
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np

from audit_shared import valid_id as identifier, CONTRACT_VERSION
import eda_extensions as ext

VERSION = "2.0.0"
ROOT = Path(__file__).resolve().parent
DATA_DIR = Path("/Users/parsaanvari/Downloads/DataAnalysis")
DATASETS = {name: DATA_DIR / f"{name}.jsonl" for name in (
    "All_Beauty", "Appliances", "meta_All_Beauty", "meta_Appliances")}
OUTPUT_DIR = ROOT / "reports" / "phase1" / "univariate"
SOURCE_URL = "https://amazon-reviews-2023.github.io/"
UTC = timezone.utc
EPOCH = datetime(1970, 1, 1, tzinfo=UTC)
REVIEW_FIELDS = "rating title text images asin parent_asin user_id timestamp helpful_vote verified_purchase".split()
META_FIELDS = "main_category title average_rating rating_number features description price images videos store categories details parent_asin bought_together".split()
STATES = ("absent", "null", "blank_string", "empty_array", "empty_object", "present_nonempty")
BLUE, GOLD, GRAY = "#1565a7", "#c76a14", "#526477"

# A metric is admitted only when its own input is usable. No whole-row complete-case filter.
REVIEW_METRICS = {
    "rating": ("Review star rating", "stars", "review"),
    "helpful_vote": ("Helpful votes", "votes", "review"),
    "title_characters": ("Review title length", "Unicode characters", "review"),
    "text_characters": ("Review body length", "Unicode characters", "review"),
    "text_whitespace_words": ("Review body length", "whitespace-separated tokens", "review"),
    "images_count": ("Review image entries", "array entries", "review"),
    "reviews_per_parent": ("Observed reviews per parent product", "raw review records", "parent product"),
    "reviews_per_user": ("Observed reviews per reviewer", "raw review records", "reviewer ID"),
}
META_METRICS = {
    "average_rating": ("Displayed product average rating", "stars", "metadata record"),
    "rating_number": ("Displayed product rating count", "ratings", "metadata record"),
    "price": ("Product price at crawl time", "USD", "metadata record"),
    "title_characters": ("Product title length", "Unicode characters", "metadata record"),
    "features_count": ("Product feature entries", "array entries", "metadata record"),
    "features_characters": ("Product feature text length", "Unicode characters", "metadata record"),
    "description_count": ("Product description entries", "array entries", "metadata record"),
    "description_characters": ("Product description text length", "Unicode characters", "metadata record"),
    "images_count": ("Product image entries", "array entries", "metadata record"),
    "videos_count": ("Product video entries", "array entries", "metadata record"),
    "categories_count": ("Category entries", "top-level array entries", "metadata record"),
    "details_count": ("Product detail attributes", "dictionary keys", "metadata record"),
    "bought_together_count": ("Recommended bundle entries", "array entries", "metadata record"),
}


def pct(n, d):
    return 100 * n / d if d else None


def fmt(x, digits=3):
    if x is None:
        return "not available"
    if isinstance(x, int):
        return f"{x:,}"
    return f"{x:,.{digits}f}"


def file_sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(8 * 1024**2), b""):
            h.update(block)
    return h.hexdigest()


def strict_object(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise ValueError("duplicate JSON object key")
        out[key] = value
    return out


def finite_float(value):
    result = float(value)
    if not math.isfinite(result):
        raise ValueError("non-finite JSON number")
    return result


def reject_constant(value):
    raise ValueError(f"nonstandard JSON constant: {value}")


def parse_line(raw, line_number):
    return json.loads(raw.decode("utf-8-sig" if line_number == 1 else "utf-8"),
                      object_pairs_hook=strict_object, parse_float=finite_float,
                      parse_constant=reject_constant)


def number(value):
    if type(value) not in (int, float):
        return False
    try:
        return math.isfinite(value)
    except OverflowError:
        return False


def field_state(value):
    if value is None:
        return "null"
    if isinstance(value, str) and not value.strip():
        return "blank_string"
    if isinstance(value, list) and not value:
        return "empty_array"
    if isinstance(value, dict) and not value:
        return "empty_object"
    return "present_nonempty"


def timestamp(value, as_of):
    if type(value) is not int:
        return None
    try:
        date = EPOCH + timedelta(milliseconds=value)
        return date if date <= as_of else None
    except (ValueError, OverflowError):
        return None


def quantile(values, counts, q):
    """Exact expanded-sample linear quantile; only frequency tables are stored."""
    total = int(sum(counts))
    if not total:
        return None
    position = (total - 1) * q
    lo, hi = math.floor(position), math.ceil(position)
    cumulative = np.cumsum(counts)
    left = float(values[bisect.bisect_right(cumulative, lo)])
    right = float(values[bisect.bisect_right(cumulative, hi)])
    return left + (position - lo) * (right - left)


def describe(hist):
    """Population moments, exact quantiles and concentration from all values."""
    pairs = sorted((v, c) for v, c in hist.items() if c > 0)
    n = sum(c for _, c in pairs)
    if not n:
        return {"n": 0}
    x = np.array([v for v, _ in pairs], dtype=float)
    c = np.array([c for _, c in pairs], dtype=np.int64)
    weights = c / n
    scale = float(max(abs(x.min()), abs(x.max()), 1))
    z = x / scale  # prevent intermediate overflow in moments
    mu = float(np.sum(z * weights))
    centered = z - mu
    m2 = float(np.sum(centered**2 * weights))
    sd_scaled = math.sqrt(max(0, m2))
    qs = {label: quantile(x, c, q) for label, q in (
        ("p05", .05), ("q1", .25), ("median", .5), ("q3", .75),
        ("p95", .95), ("p99", .99), ("p999", .999))}
    # Constant data have undefined skewness/kurtosis, not zero.
    constant = len(pairs) == 1
    skew = None if constant or not m2 else float(np.sum((centered / sd_scaled)**3 * weights))
    kurt = None if constant or not m2 else float(np.sum((centered / sd_scaled)**4 * weights) - 3)
    mean, sd = mu * scale, sd_scaled * scale
    variance = sd * sd
    iqr = qs["q3"] - qs["q1"]
    deviation = Counter()
    for v, count in pairs:
        deviation[abs(v - qs["median"])] += count
    dp = sorted(deviation.items())
    mode_count = int(c.max())
    modes = [v for v, count in pairs if count == mode_count]
    top_k = max(1, math.ceil(.01 * n))
    needed, top_sum_scaled = top_k, 0.0
    for v, count in reversed(pairs):
        take = min(needed, count)
        top_sum_scaled += (v / scale) * take
        needed -= take
        if not needed:
            break
    total_scaled = mu * n
    gini = None
    if x.min() >= 0 and total_scaled > 0:
        cumulative_counts = np.cumsum(c)
        # Sum of (2*rank-n-1)*x for the expanded ordered observations.
        gini = float(np.sum(c * (2*cumulative_counts-c-n) * z) / (n * total_scaled))
        gini = min(1., max(0., gini))
    return dict(n=n, unique_values=len(pairs), minimum=float(x.min()), maximum=float(x.max()),
                mean=mean, population_std=sd, population_variance=variance if math.isfinite(variance) else None,
                **qs, iqr=iqr,
                median_absolute_deviation=quantile([v for v, _ in dp], [c for _, c in dp], .5),
                mode_values=modes[:10], mode_ties=len(modes), mode_count=mode_count,
                mode_percent=pct(mode_count, n), zero_count=int(hist.get(0, 0)),
                zero_percent=pct(hist.get(0, 0), n),
                skewness_population=skew, excess_kurtosis_population=kurt,
                bowley_skewness=(qs["q3"]+qs["q1"]-2*qs["median"])/iqr if iqr else None,
                coefficient_of_variation=sd/mean if mean > 0 else None,
                above_p99_count=sum(count for v, count in pairs if v > qs["p99"]),
                above_p99_percent=pct(sum(count for v, count in pairs if v > qs["p99"]), n),
                gini_nonnegative=gini, top_one_percent_count=top_k,
                top_one_percent_value_share_percent=100*top_sum_scaled/total_scaled if total_scaled > 0 and x.min() >= 0 else None)


def categorical_summary(hist, rows):
    n = sum(hist.values())
    ranked = sorted(hist.items(), key=lambda a: (-a[1], a[0]))
    entropy = -sum((v/n)*math.log(v/n) for v in hist.values()) if n else None
    k = len(hist)
    return dict(valid_count=n, excluded_count=rows-n, denominator_object_rows=rows,
                distinct_levels=k, mode=ranked[0][0] if n else None,
                mode_count=ranked[0][1] if n else 0,
                mode_percent=pct(ranked[0][1], n) if n else None,
                top10_share_percent=pct(sum(v for _, v in ranked[:10]), n),
                normalized_entropy=entropy/math.log(k) if k > 1 else (0. if k == 1 else None),
                frequencies=[dict(level=key, count=v, percent_of_valid=pct(v, n),
                                  percent_of_objects=pct(v, rows)) for key, v in ranked])


def scan_file(name, path, args, as_of):
    is_meta = name.startswith("meta_")
    specs = META_METRICS if is_meta else REVIEW_METRICS
    hist = {key: Counter() for key in specs}
    dedup = ext.DedupSensitivity(is_meta)
    text_audit = None if is_meta else ext.TextAudit(getattr(args,"detector",None),getattr(args,"short_max_words",5),getattr(args,"long_min_words",500))
    categories = {key: Counter() for key in (("main_category", "store") if is_meta else ("verified_purchase",))}
    fields = defaultdict(Counter)
    for key in META_FIELDS if is_meta else REVIEW_FIELDS:
        fields[key]
    parent, user, years, months = Counter(), Counter(), Counter(), Counter()
    temporal_hist = Counter()
    read_errors = Counter()
    count = lines = 0
    before = path.stat()
    sha = file_sha(path)
    opener = gzip.open if path.suffix == ".gz" else open
    print(f"START: {name} | {path}", flush=True)
    with opener(path, "rb") as handle:
        while args.max_lines is None or lines < args.max_lines:
            raw = handle.readline()
            if not raw:
                break
            lines += 1
            if not raw.strip():
                read_errors["blank_line"] += 1
                continue
            try:
                record = parse_line(raw, lines)
            except (ValueError, UnicodeError, RecursionError):
                read_errors["invalid_json_or_encoding_or_duplicate_key"] += 1
                continue
            if not isinstance(record, dict):
                read_errors["non_object_json"] += 1
                continue
            count += 1
            dedup.add(record)
            if text_audit is not None: text_audit.add(record)
            for key, value in record.items():
                fields[key][field_state(value)] += 1
            if isinstance(record.get("title"), str):
                hist["title_characters"][len(record["title"])] += 1
            if is_meta:
                v = record.get("average_rating")
                if number(v) and 1 <= v <= 5:
                    hist["average_rating"][v] += 1
                v = record.get("rating_number")
                if type(v) is int and number(v) and v >= 0:
                    hist["rating_number"][v] += 1
                v = record.get("price")
                if number(v) and v >= 0:
                    hist["price"][v] += 1
                for key in ("features", "description", "images", "videos", "categories", "bought_together"):
                    v = record.get(key)
                    if isinstance(v, list):
                        hist[key+"_count"][len(v)] += 1
                        if key in ("features", "description") and all(isinstance(s, str) for s in v):
                            hist[key+"_characters"][sum(len(s) for s in v)] += 1
                if isinstance(record.get("details"), dict):
                    hist["details_count"][len(record["details"])] += 1
                for key in categories:
                    v = record.get(key)
                    if isinstance(v, str) and v.strip():
                        categories[key][v] += 1  # exact labels, no silent harmonization
            else:
                v = record.get("rating")
                if number(v) and 1 <= v <= 5 and v % 1 == 0:
                    hist["rating"][int(v)] += 1
                v = record.get("helpful_vote")
                if type(v) is int and number(v) and v >= 0:
                    hist["helpful_vote"][v] += 1
                if isinstance(record.get("text"), str):
                    hist["text_characters"][len(record["text"])] += 1
                    hist["text_whitespace_words"][len(record["text"].split())] += 1
                if isinstance(record.get("images"), list):
                    hist["images_count"][len(record["images"])] += 1
                if type(record.get("verified_purchase")) is bool:
                    categories["verified_purchase"][str(record["verified_purchase"])] += 1
                if identifier(record.get("parent_asin")):
                    parent[record["parent_asin"]] += 1
                if identifier(record.get("user_id")):
                    user[record["user_id"]] += 1
                date = timestamp(record.get("timestamp"), as_of)
                if date is not None:
                    temporal_hist[record["timestamp"]] += 1
                    years[str(date.year)] += 1
                    months[f"{date.year:04d}-{date.month:02d}"] += 1
            if args.progress_every and count % args.progress_every == 0:
                print(f"{name}: {count:,} JSON objects profiled", flush=True)
        reached_eof = not bool(handle.read(1))
    if not is_meta:
        hist["reviews_per_parent"] = Counter(parent.values())
        hist["reviews_per_user"] = Counter(user.values())
    metrics = {}
    for key, spec in specs.items():
        summary = describe(hist[key])
        denominator = len(parent) if key == "reviews_per_parent" else len(user) if key == "reviews_per_user" else count
        metrics[key] = dict(title=spec[0], unit=spec[1], observation_unit=spec[2],
                            eligible_denominator=denominator, excluded_count=denominator-summary["n"],
                            population_note="Valid nonblank exact IDs only; raw review copies retained." if key.startswith("reviews_per_") else "Field-wise valid values; raw copies retained.",
                            summary=summary)
    if not is_meta:
        for key, counter in (("reviews_per_parent", parent), ("reviews_per_user", user)):
            metrics[key]["source_review_rows_with_valid_id"] = sum(counter.values())
            metrics[key]["source_review_rows_without_valid_id"] = count-sum(counter.values())
        del parent, user
    field_rows = []
    for key, states in sorted(fields.items()):
        states["absent"] = count-sum(states.values())
        field_rows.append(dict(field=key, denominator=count, **{s:states[s] for s in STATES},
                               unavailable_or_empty_percent=pct(count-states["present_nonempty"],count)))
    temporal = None
    if not is_meta:
        temporal = dict(n=sum(temporal_hist.values()), excluded_count=count-sum(temporal_hist.values()),
                        timezone="UTC", years=dict(sorted(years.items())), months=dict(sorted(months.items())))
        if temporal_hist:
            # Date quantiles on integer epoch ms; no skewness of an arbitrary epoch origin.
            ordered = sorted(temporal_hist.items())
            tx, tc = zip(*ordered)
            def iso(ms):
                return (EPOCH+timedelta(milliseconds=ms)).isoformat()
            temporal.update(earliest_utc=iso(tx[0]), latest_utc=iso(tx[-1]),
                q1_utc=iso(quantile(tx,tc,.25)), median_utc=iso(quantile(tx,tc,.5)),
                q3_utc=iso(quantile(tx,tc,.75)),
                iqr_days=(quantile(tx,tc,.75)-quantile(tx,tc,.25))/86400000,
                span_days=(tx[-1]-tx[0])/86400000,
                outside_documented_release_window_count=sum(c for v,c in ordered if v < 830908800000 or v >= 1696118400000))
    after = path.stat()
    unchanged = (before.st_size,before.st_mtime_ns)==(after.st_size,after.st_mtime_ns)
    result = dict(name=name, kind="metadata" if is_meta else "reviews", object_rows=count,
                  physical_lines=lines, parse_failures=dict(read_errors),
                  complete=reached_eof and unchanged, source=dict(path=str(path.resolve()),bytes=before.st_size,
                  sha256=sha, unchanged_size_and_mtime=unchanged),
                  fields=field_rows, metrics=metrics,
                  categorical={k:categorical_summary(v,count) for k,v in categories.items()}, temporal=temporal)
    result["deduplication_sensitivity"]=dedup.finish(describe,hist)
    if text_audit is not None: result["text_audit"]=text_audit.finish(describe)
    if not is_meta and hist["rating"]:
        h = hist["rating"]; n = sum(h.values())
        result["rating_balance"] = dict(denominator=n, low_1_2_count=h[1]+h[2], neutral_3_count=h[3], high_4_5_count=h[4]+h[5],
             low_1_2_percent=pct(h[1]+h[2],n), neutral_3_percent=pct(h[3],n), high_4_5_percent=pct(h[4]+h[5],n),
             five_star_percent=pct(h[5],n), class_counts={str(k):h[k] for k in range(1,6)},
             absent_classes=[k for k in range(1,6) if h[k]==0], absent_class_count=sum(h[k]==0 for k in range(1,6)),
             all_five_class_ratio=max(h[k] for k in range(1,6))/min(h[k] for k in range(1,6)) if all(h[k]>0 for k in range(1,6)) else None,
             largest_to_smallest_observed_class_ratio=max(h.values())/min(v for v in h.values() if v>0),
             normalized_entropy=-sum(v/n*math.log(v/n) for v in h.values() if v>0)/math.log(5))
    print(f"DONE: {name} | {count:,} objects | complete={result['complete']}", flush=True)
    return result, hist


def init_plotting(output):
    # Local cache avoids permissions problems without changing the user's global setup.
    os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".matplotlib_cache"))
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.family":"DejaVu Sans", "font.size":10,
                         "axes.spines.top":False, "axes.spines.right":False,
                         "axes.titleweight":"bold", "savefig.facecolor":"white"})
    return matplotlib, plt


def save_figure(fig, out, name, plt):
    folder = out / "figures"
    folder.mkdir(exist_ok=True)
    paths = []
    for ext in ("png", "svg"):
        path = folder / f"{name}.{ext}"
        fig.savefig(path, dpi=160, bbox_inches="tight")
        paths.append(str(path.relative_to(out)))
    plt.close(fig)
    return paths


def weighted_bins(x, weights, lower, upper, summary):
    if lower == upper:
        return np.array([lower-.5, upper+.5])
    if upper <= 30 and np.all(x == np.floor(x)):
        # Avoid suggesting fractional values for small discrete counts.
        return np.arange(math.floor(lower)-.5, math.ceil(upper)+1.5)
    width = 2 * summary["iqr"] / summary["n"]**(1/3)
    bins = math.ceil((upper-lower)/width) if width > 0 else math.ceil(math.log2(summary["n"])+1)
    return np.linspace(lower, upper, min(60,max(12,bins))+1)


def plot_numeric(name, key, metric, hist, out, plt):
    s = metric["summary"]
    title = f"{name} | {metric['title']}"
    if not s["n"]:
        fig, ax = plt.subplots(figsize=(9,3))
        ax.axis("off")
        ax.text(.5,.6,"No valid observations for this metric",ha="center",fontsize=16)
        ax.text(.5,.35,f"Excluded: {metric['excluded_count']:,} of {metric['eligible_denominator']:,}; no distribution can be estimated.",ha="center")
        fig.suptitle(title,fontweight="bold")
        return save_figure(fig,out,f"{name}__{key}",plt)
    items = sorted(hist.items()); x=np.array([v for v,c in items],float); c=np.array([c for v,c in items])
    cumulative = np.cumsum(c)/s["n"]*100
    if key in ("rating", "average_rating"):
        fig, axes = plt.subplots(1,2,figsize=(12,4.3),layout="constrained")
        bx = np.arange(1,6) if key=="rating" else x
        by = [100*hist.get(float(v),0)/s["n"] for v in bx]
        axes[0].bar(bx,by,width=.7 if key=="rating" else .075,color=BLUE)
        if key=="rating":
            for a,b in zip(bx,by): axes[0].text(a,b+.6,f"{b:.1f}%",ha="center",fontsize=9)
        axes[0].set(xlabel="Stars",ylabel="Percent of valid observations",title="Exact frequency distribution",xlim=(.7,5.3))
        axes[0].set_ylim(0,max(by)*1.15+1)
        axes[1].step(np.r_[1,x,5], np.r_[0,cumulative,100],where="post",color=BLUE)
        axes[1].set(xlabel="Stars",ylabel="Cumulative percent",title="Empirical cumulative distribution",ylim=(0,103))
        footer=f"n={s['n']:,} | mean={s['mean']:.3f} | median={s['median']:.3f} | SD={s['population_std']:.3f} | IQR={s['iqr']:.3f}"
    else:
        fig, axes = plt.subplots(2,2,figsize=(12,7.6),layout="constrained")
        a,b,d,e = axes.flat
        cutoff=s["p99"]; mask=x<=cutoff
        bins=weighted_bins(x,c,float(x.min()),cutoff,s)
        a.hist(x[mask],bins=bins,weights=c[mask]/s["n"]*100,color=BLUE,edgecolor="white",linewidth=.3)
        a.set(xlabel=metric["unit"],ylabel="Percent of ALL valid observations",title=f"Linear view through P99 = {fmt(cutoff)}")
        a.text(.98,.96,f"Above view: {s['above_p99_count']:,} ({s['above_p99_percent']:.2f}%)",ha="right",va="top",transform=a.transAxes,fontsize=9)
        lx=np.log1p(x)
        b.hist(lx,bins=40 if len(x)>1 else 1,weights=c/s["n"]*100,color=BLUE,edgecolor="white",linewidth=.3)
        b.set(xlabel=f"ln(1 + {metric['unit']})",ylabel="Percent of valid observations",title="Full range, including zeros and extremes")
        d.step(np.r_[0,x],np.r_[0,cumulative],where="post",color=BLUE)
        d.set_xscale("symlog",linthresh=1)
        d.set(xlabel=f"{metric['unit']} (symlog axis; linear near 0)",ylabel="Cumulative percent",ylim=(0,103),title="Full empirical cumulative distribution")
        d.axhline(50,color=GRAY,ls=":",lw=1)
        d.axhline(95,color=GOLD,ls=":",lw=1)
        e.bxp([dict(med=s["median"],q1=s["q1"],q3=s["q3"],whislo=s["p05"],whishi=s["p95"],fliers=[])],
              orientation="horizontal",showfliers=False,patch_artist=True,boxprops={"facecolor":"#bad7ec"})
        e.set(xlabel=metric["unit"],yticks=[],title="Box: Q1 to Q3; whiskers: P5 to P95")
        e.text(.02,.95,f"Minimum {fmt(s['minimum'])} | maximum {fmt(s['maximum'])}\nWhiskers are percentiles, not deletion thresholds.",transform=e.transAxes,va="top",fontsize=9)
        footer=f"n={s['n']:,} | median={fmt(s['median'])} | mean={fmt(s['mean'])} | SD={fmt(s['population_std'])} | zero={s['zero_percent']:.2f}%"
    for ax in np.asarray(axes).flat:
        ax.grid(axis="y",alpha=.15)
    fig.suptitle(title+"\n"+footer,fontsize=13)
    return save_figure(fig,out,f"{name}__{key}",plt)


def plot_categories(name,key,data,out,plt):
    rows=data["frequencies"]; shown=rows[:12]
    labels=[textwrap.fill(r["level"],38) for r in shown]
    values=[r["percent_of_valid"] for r in shown]
    if len(rows)>12:
        labels.append(f"Other ({len(rows)-12:,} distinct labels)")
        values.append(sum(r["percent_of_valid"] for r in rows[12:]))
    fig,ax=plt.subplots(figsize=(11,max(3.6,.48*len(labels)+1.4)),layout="constrained")
    if labels:
        ax.barh(labels[::-1],values[::-1],color=BLUE)
        for i,v in enumerate(values[::-1]): ax.text(v+.3,i,f"{v:.2f}%",va="center",fontsize=9)
        ax.set_xlim(0,max(values)*1.19+1)
    else:
        ax.text(.5,.5,"No valid category values",transform=ax.transAxes,ha="center")
    ax.set(xlabel="Percent of valid nonempty values",title=f"{name} | {key}\nvalid n={data['valid_count']:,}; excluded={data['excluded_count']:,}")
    return save_figure(fig,out,f"{name}__{key}",plt)


def plot_states(data,out,plt):
    rows=data["fields"]; n=data["object_rows"]
    fig,ax=plt.subplots(figsize=(12,max(4,.38*len(rows)+1.5)),layout="constrained")
    left=np.zeros(len(rows)); colors=["#b64141","#df9257","#d3b150","#8e86bc","#88bdb5","#276e9c"]
    for state,color in zip(STATES,colors):
        values=np.array([r[state]/n*100 if n else 0 for r in rows])
        ax.barh([r["field"] for r in rows],values,left=left,label=state.replace("_"," "),color=color)
        left+=values
    ax.set(xlim=(0,100),xlabel="Percent of all parsed object rows",title=f"{data['name']} | Field content states (n={n:,})")
    ax.legend(loc="upper center",bbox_to_anchor=(.5,-.13),ncol=3,fontsize=9)
    return save_figure(fig,out,f"{data['name']}__field_states",plt)


def plot_time(data,out,plt):
    t=data["temporal"]; fig,axes=plt.subplots(2,1,figsize=(12,6.5),layout="constrained")
    if not t["n"]:
        for ax in axes: ax.text(.5,.5,"No valid timestamps",transform=ax.transAxes,ha="center")
    else:
        years=list(range(int(min(t["years"])),int(max(t["years"]))+1))
        axes[0].bar(years,[t["years"].get(str(y),0) for y in years],color=BLUE)
        axes[0].set(xlabel="UTC year",ylabel="Observed review records",title="Annual counts; first and last years may be partial")
        first,last=min(t["months"]),max(t["months"])
        y,m=map(int,first.split("-")); labels=[]
        while f"{y:04d}-{m:02d}"<=last:
            labels.append(f"{y:04d}-{m:02d}"); m+=1
            if m==13: y+=1; m=1
        axes[1].plot(range(len(labels)),[t["months"].get(k,0) for k in labels],color=BLUE,lw=1.3)
        ticks=np.unique(np.linspace(0,len(labels)-1,min(10,len(labels)),dtype=int))
        axes[1].set_xticks(ticks,[labels[i] for i in ticks],rotation=30,ha="right")
        axes[1].set(xlabel="UTC calendar month (zero-count months included)",ylabel="Observed review records",title="Monthly counts; no smoothing or exposure adjustment")
    fig.suptitle(f"{data['name']} | Timestamp distribution; n={t['n']:,}",fontsize=13)
    return save_figure(fig,out,f"{data['name']}__timestamp",plt)


def write_csv(path,rows):
    rows=list(rows)
    if not rows:
        path.write_text("",encoding="utf-8"); return
    keys=list(dict.fromkeys(k for r in rows for k in r))
    with path.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=keys); w.writeheader()
        for row in rows:
            w.writerow({k:json.dumps(v,ensure_ascii=True) if isinstance(v,(list,dict)) else v for k,v in row.items()})


def write_json(path,value):
    path.write_text(json.dumps(value,indent=2,ensure_ascii=True,allow_nan=False)+"\n",encoding="utf-8")


def interpret_numeric(key,metric):
    s=metric["summary"]
    if not s["n"]:
        return "No valid values are available. A mean, spread or distribution shape cannot be inferred; the empty-data panel documents this limitation. Missing is not zero."
    mode="; ".join(fmt(v) for v in s["mode_values"])
    text=(f"The valid population contains {s['n']:,} {metric['observation_unit']} observations; "
          f"{metric['excluded_count']:,} are excluded from this metric's denominator. "
          f"The median is {fmt(s['median'])} {metric['unit']} and the mean is {fmt(s['mean'])}. "
          f"The middle half lies between {fmt(s['q1'])} and {fmt(s['q3'])} (IQR {fmt(s['iqr'])}); "
          f"population SD is {fmt(s['population_std'])} and unscaled median absolute deviation is {fmt(s['median_absolute_deviation'])}. "
          f"The range is {fmt(s['minimum'])} to {fmt(s['maximum'])}; P95 is {fmt(s['p95'])} and P99 is {fmt(s['p99'])}. "
          f"The modal value(s), up to ten, are {mode}; there are {s['mode_ties']:,} tied modes, each representing {s['mode_percent']:.2f}% of valid observations. ")
    if s["unique_values"]==1:
        text+="All valid values are identical. The distribution is a point mass, its spread is zero, and skewness/kurtosis are undefined. "
    else:
        skew=s["skewness_population"]
        direction="positive (a longer/heavier upper tail by the third-moment measure)" if skew>0 else "negative (a longer/heavier lower tail by the third-moment measure)" if skew<0 else "zero"
        text+=(f"Moment skewness is {fmt(skew)}, {direction}. Excess kurtosis is {fmt(s['excess_kurtosis_population'])}; "
               "this fourth-moment statistic is sensitive to extreme values and is not a normality test. "
               f"Quartile-based Bowley skewness is {fmt(s['bowley_skewness'])}. ")
        if not s["iqr"]:
            text+="The middle 50% collapses to one value even though other values exist; zero IQR does not mean the whole distribution is constant. "
    if s["zero_count"]:
        text+=f"There is an observed mass at zero: {s['zero_count']:,} observations ({s['zero_percent']:.2f}%). "
    if key not in ("rating","average_rating"):
        text+=(f"In the figure, the linear histogram ends at P99 and explicitly leaves {s['above_p99_count']:,} observations "
               f"({s['above_p99_percent']:.2f}%) above its display limit. The log1p histogram and full ECDF retain the entire valid range; "
               "the ECDF steps indicate repeated values, and its horizontal stretches indicate gaps. The box describes the middle half, "
               "with percentile whiskers P5/P95, so it should not be read as a Tukey outlier rule. ")
    if key=="rating":
        text+="Stars are ordered categories. Median and class percentages are primary; mean/SD are conventional summaries that treat adjacent star steps as equally spaced. This is a raw review distribution, not the future ten-review product target."
    elif key=="average_rating":
        text+="The bar chart uses each observed displayed value. Rounding/heaping can create peaks; this snapshot average is not recomputed from the available reviews and must not be treated as historically available at the fifth review."
    elif key=="helpful_vote":
        text+="Zero votes mean no helpful votes recorded, not an unhelpful review. These cumulative snapshot counts mix age, exposure and voting behaviour, so their shape does not measure intrinsic review quality or future helpfulness."
    elif key=="price":
        text+="These summaries describe observed, valid crawl-time USD prices only. Missing prices are excluded without imputation. Their distribution cannot be assumed to represent all products or prices at review time; zero, if observed, remains a recorded value rather than an imputed price."
    elif key=="rating_number":
        text+="This is the product-page rating count at collection, not the number of review records in this file, sales volume, or a historical count at prediction time."
    elif key.startswith("reviews_per_"):
        text+=(f"Each {metric['observation_unit']} contributes once to this distribution. Gini is {fmt(s['gini_nonnegative'])}; "
               f"the largest {s['top_one_percent_count']:,} groups (ceil(1% of groups)) account for {fmt(s['top_one_percent_value_share_percent'])}% "
               "of counted review rows. This measures concentration within the observed file, including extra raw copies; it is not market share or all-time user activity.")
    elif key.endswith("characters") or key.endswith("words"):
        text+="Length measures volume, not sentiment, informativeness or language. Raw HTML, Unicode and whitespace conventions remain; no token model, language filter or text cleaning was applied."
    else:
        text+="This counts container entries or keys, not verified usable content. For example, multiple image sizes inside one entry are not separate images, and a nonempty image list does not prove successful image download."
    return text


def make_report(result):
    lines=["# Univariate Exploratory Data Analysis: Methods, Results and Interpretation", "",
           f"**Run status:** `{result['status']}`. **Started (UTC):** {result['started_utc']}. **Module:** `univariate_eda.py` v{VERSION}.", "",
           "## 1. Purpose and scope", "",
           "This report describes one-variable distributions for All_Beauty and Appliances review files and their metadata. "
           "It answers how values are distributed, where their centre lies, how dispersed they are, and whether values or classes are concentrated. "
           "It includes a limited text-by-rating comparison required by Track B, plus exact-duplicate sensitivity; it is not a cleaning pipeline, causal analysis or predictive evaluation. "
           "The original files remain unchanged. Exact duplicate copies are retained, so the estimand is the distribution of raw collected records.", "",
           "## 2. Reproducible methods and statistical reasoning", "",
           "### 2.1 Input and population rules", "",
           f"The [official dataset documentation]({SOURCE_URL}) identifies reviews and item metadata as distinct sources and defines the fields. "
           "Collection is observational. Price is a crawl-time USD value; product averages and rating counts are snapshots. "
           "The program reads local JSONL (or JSONL.gz) sequentially, rejects malformed JSON/duplicate keys/nonobjects with counts, and profiles every parsed object. "
           "It computes file SHA-256 and checks size/mtime stability. A debug line cap is labelled partial and cannot be presented as a full-file study.", "",
           "The shared audit_shared.py contract rejects blank, padded or surrogate-containing identifiers without modifying them. "
           "Each metric uses its own valid inputs, not a table-wide complete-case filter. Missing, null, blank and empty containers are recorded separately. "
           "Numeric strings and booleans are not silently converted. Review ratings must be integral 1–5; product average ratings may be fractional 1–5; "
           "helpful votes and rating counts require nonnegative JSON integers; prices require finite nonnegative numbers. "
           "A valid numeric zero is retained. Empty lists have a valid entry count of zero, but a null list does not. "
           "Text lengths include empty strings and whitespace-only text. Identifier activity uses exact nonblank strings without surrounding whitespace; "
           "excluded identifier rows are reported. No user IDs or review text are exported in frequency tables.", "",
           "### 2.2 Variables and derived measurements", "",
           "Reviews: star rating, helpful votes, verified purchase, title/body character counts, whitespace token count, image-entry count, "
           "timestamp frequency, and raw reviews per product/reviewer. Metadata: average rating, rating number, price, title length, main category and store; "
           "entry counts for features, descriptions, images, videos, categories and bundles; total feature/description characters; and detail-key count. "
           "Feature/description text length sums strings without inserting separators and excludes arrays containing non-string items. "
           "Category entry count is not asserted to be hierarchy depth. Empty nested structures mean absent content, not broken records. "
           "All observed fields receive a content-state chart/table, including sparse extra fields. IDs themselves have no numeric centre; "
           "Mixed-unit dimensions, image pixels and sentiment remain outside scope. Language, scripts, unusual characters and text length by rating are audited explicitly below.", "",
           "### 2.3 Centre, spread, shape and imbalance", "",
           "All numeric summaries use full frequency tables, not samples. Quantiles use linear interpolation at (n−1)q, matching an expanded sorted sample. "
           "Centre is described by mean, median and modes; spread by minimum/maximum, population SD and variance (divisor n), quartiles/IQR, "
           "unscaled median absolute deviation, P5/P95/P99/P99.9 and coefficient of variation where the mean is positive. "
           "Modes are exact observed values, not histogram peaks; only the first ten tied modes are printed, with the full tie count. "
           "Population skewness is m3/m2^(3/2); excess kurtosis is m4/m2²−3. Bowley skewness is (Q3+Q1−2 median)/IQR. "
           "These are descriptive empirical statistics, not fitted distribution parameters or tests of normality. "
           "No normal, lognormal, Poisson or power-law model is assumed or fitted. Zero variance makes moment shape undefined; zero IQR makes Bowley undefined. "
           "The mean can be pulled by extreme values, so median/IQR are always provided. Ordinal stars are primarily interpreted through their class counts.", "",
           "Numeric imbalance includes the mass at zero and modal share. Review class imbalance reports all five stars, low (1–2), neutral (3) and high (4–5) groups, "
           "the largest-to-smallest observed class ratio, and Shannon entropy divided by log(5). "
           "Categorical summaries include exact label counts, modal share, top-ten share and entropy/log(number of observed levels); entropy is zero for a single level. "
           "Nominal category means/SDs are not meaningful. Product/user activity concentration also uses Gini and the fraction of review rows in the largest ceil(1% of groups). "
           "No significance tests or confidence intervals are added to this census of the supplied files; a larger population would require sampling and dependence assumptions.", "",
           "### 2.4 Why these figures", "",
           "Ratings use exact frequency bars and an empirical cumulative distribution (ECDF), preserving their discrete/rounded nature. "
           "Other numeric panels pair a raw linear histogram through P99 with a full-range log1p histogram, a full ECDF on a symlog axis and a box summary. "
           "Small integer-valued counts (display limit at most 30) use integer-centred bins. Otherwise the central histogram uses a Freedman–Diaconis width, bounded to 12–60 bins; zero IQR falls back to a Sturges-style count. "
           "Its y denominator remains ALL valid observations, and the omitted upper-tail count is printed. "
           "The log histogram uses 40 equal-width bins in ln(1+x), retaining zeros; its bars are percentages per transformed bin, not raw-unit density. "
           "The ECDF includes every distinct observed value and reaches 100%; it is not a fitted curve. "
           "The box covers Q1–Q3 with median and P5–P95 whiskers; omitted extremes remain in other panels and the min/max annotation. "
           "No plot limit deletes data. Displayed category charts show the top 12 levels plus Other; full counts are saved. "
           "Empty metrics receive an explicit no-data panel instead of fabricated statistics.", "",
           "### 2.5 Time and interpretation limits", "",
           "Timestamps are integer Unix milliseconds converted to UTC; impossible/future values relative to the recorded reference time are excluded. "
           "The median date, date quartiles, span and IQR in days are reported; epoch-dependent means and skewness are not interpreted. "
           "Annual/monthly counts describe timing of observed reviews, not sales, exposure-normalized review rates or causal trends. "
           "Missing months inside the observed interval are plotted as zero. Boundary months/years are partial, so a final-year drop cannot establish declining demand. "
           "Metadata has no common historical timestamp. Empty media arrays do not imply failed downloads; category labels need not equal the downloaded file category. "
           "Text encoding and probable language are audited below. Image network retrieval is not tested; local URL availability is linked from the matching quality audit. "
           "If learned imputations, scaling, vocabulary, or outlier thresholds enter a predictor later, fit them on training data only; "
           "this whole-file descriptive EDA is not a license to tune using a final test.", "",
           "## 3. Execution evidence", "",
           "| Dataset | Parsed objects | Physical lines | Parse failures | Full, unchanged scan |", "|---|---:|---:|---:|---|"]
    for d in result["datasets"]:
        lines.append(f"| {d['name']} | {d['object_rows']:,} | {d['physical_lines']:,} | {sum(d['parse_failures'].values()):,} | {d['complete']} |")
    lines += ["", "The recorded input hashes and comparison with the earlier quality audit are saved in `univariate_eda.json`. "
              "`complete` means the requested files were fully scanned unchanged; it does not mean they are error-free. "
              "Missing/unreadable files or parsing warnings are explicitly reported below.", "", f"Errors: `{json.dumps(result['errors'])}`", "",
              "## 4. Dataset-by-dataset results"]
    highlights = ["## Key measured findings", "",
                  "These are marginal descriptions of separate files, not controlled comparisons or causal effects.", ""]
    for d in result["datasets"]:
        if d["kind"] == "reviews" and "rating_balance" in d:
            b=d["rating_balance"]; votes=d["metrics"]["helpful_vote"]["summary"]
            length=d["metrics"]["text_characters"]["summary"]
            product=d["metrics"]["reviews_per_parent"]["summary"]
            highlights.append(f"- **{d['name']} reviews:** {b['five_star_percent']:.2f}% are five-star and {b['low_1_2_percent']:.2f}% are one-/two-star. "
                              + ext.rating_statement(b))
            if votes["n"]:
                highlights.append(f"- **{d['name']} helpful votes:** {votes['zero_percent']:.2f}% are zero, median {fmt(votes['median'])}, "
                                  f"mean {fmt(votes['mean'])}, maximum {fmt(votes['maximum'])}. " + ext.shape_statement(votes))
            if length["n"]:
                highlights.append(f"- **{d['name']} review length:** median {fmt(length['median'])} characters versus mean {fmt(length['mean'])}; "
                                  f"P99 {fmt(length['p99'])}, maximum {fmt(length['maximum'])}. "
                                  "Use the linear and full-range panels together to distinguish the bulk from unusually long reviews.")
            if product["n"]:
                highlights.append(f"- **{d['name']} product coverage:** median {fmt(product['median'])} observed reviews per parent, "
                                  f"mean {fmt(product['mean'])}; the largest 1% of parent groups hold {fmt(product['top_one_percent_value_share_percent'])}% of raw review rows. "
                                  "The later requirement of 15 usable reviews will select a subset; this module does not equate raw counts with final cohort eligibility.")
        if d["kind"] == "metadata":
            p=d["metrics"]["price"]["summary"]
            if p["n"]:
                highlights.append(f"- **{d['name']} prices:** {p['n']:,} valid prices ({100*p['n']/d['object_rows']:.2f}% of metadata records), "
                                  f"median USD {p['median']:.2f}, mean USD {p['mean']:.2f}, maximum USD {p['maximum']:.2f}. "
                                  + ext.shape_statement(p))
            cat=d["categorical"]["main_category"]
            if cat["valid_count"]:
                highlights.append(f"- **{d['name']} category labels:** `{cat['mode']}` is the most frequent label "
                                  f"({cat['mode_percent']:.2f}% of nonempty labels). Download-category membership must not be silently replaced by this field.")
    highlights += ["", "Read the method definitions before using these values as modelling inputs. All values describe raw collected records, including duplicate copies.", ""]
    lines[4:4] = highlights
    for d in result["datasets"]:
        lines += ["",f"### {d['name']}","", f"Unit: one {d['kind']} record unless a derived group metric states otherwise. "
                  f"This file contributes **{d['object_rows']:,} raw records**. Full numeric frequencies are in `{d['name']}__numeric_frequencies.csv.gz`.", "",
                  "#### Field coverage and denominators", "", "| Field | Absent | Null | Blank string | Empty array | Empty object | Nonempty |", "|---|---:|---:|---:|---:|---:|---:|"]
        for f in d["fields"]:
            lines.append("| "+f["field"]+" | "+" | ".join(f"{f[k]:,}" for k in STATES)+" |")
        lines += ["",f"![Field content states]({d['figures']['field_states'][0]})", "",
                  "The stacked bars separate absent content from nonempty content. Nonempty is not a quality certification. "
                  "Each row sums to the file's parsed-object count, so differences in denominators can be traced without dropping entire records."]
        for key,metric in d["metrics"].items():
            s=metric["summary"]
            lines += ["", f"#### {key}: {metric['title']}", "", interpret_numeric(key,metric), ""]
            if s["n"]:
                lines += ["| Valid n | Mean | Median | SD | Q1 | Q3 | IQR | P99 | Maximum | Skewness | Excess kurtosis |", "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
                          "| "+" | ".join(fmt(s[k]) for k in ("n","mean","median","population_std","q1","q3","iqr","p99","maximum","skewness_population","excess_kurtosis_population"))+" |", ""]
            lines += [f"![{metric['title']}]({d['figures'][key][0]})"]
        if "rating_balance" in d:
            b=d["rating_balance"]
            lines += ["", "#### Review rating imbalance", "",
                      f"Low-star reviews (1–2) account for **{b['low_1_2_percent']:.2f}%** ({b['low_1_2_count']:,}); "
                      f"three stars for {b['neutral_3_percent']:.2f}%; and 4–5 stars for {b['high_4_5_percent']:.2f}%. "
                      f"Five stars alone account for {b['five_star_percent']:.2f}%. The largest observed class is {b['largest_to_smallest_observed_class_ratio']:.2f} "
                      f"times the smallest observed class. Normalized entropy is {b['normalized_entropy']:.3f} (1 would indicate equal shares across five stars). "
                      "These quantify class imbalance without asserting that non-reviewing buyers have the same experience. "
                      "They do not substitute for the eventual distribution of the product-level future ten-review target. " + ext.rating_statement(b)]
        lines += ext.extended_report(d)
        for key,cat in d["categorical"].items():
            lines += ["", f"#### {key}: categorical distribution", "",
                      f"There are {cat['valid_count']:,} valid nonempty observations and {cat['excluded_count']:,} excluded values. "
                      f"The distribution contains {cat['distinct_levels']:,} exact observed labels. "
                      f"The most common label is `{cat['mode']}`, with {fmt(cat['mode_percent'])}% of valid values. "
                      f"Top-ten share is {fmt(cat['top10_share_percent'])}%; normalized entropy is {fmt(cat['normalized_entropy'])}. "
                      "A large Other bar is an aggregate of many labels, not an actual single label. All label frequencies and both valid/all-row denominators are saved.", "",
                      "| Label (top 12) | Count | % valid | % all objects |", "|---|---:|---:|---:|"]
            for row in cat["frequencies"][:12]:
                label=row["level"].replace("|","/").replace("\n"," ")
                lines.append(f"| {label} | {row['count']:,} | {row['percent_of_valid']:.3f} | {row['percent_of_objects']:.3f} |")
            lines += ["", f"![{key}]({d['figures'][key][0]})", ""]
            lines.append("Verified purchase is a platform flag. False does not establish a fake review, and true does not remove self-selection." if key=="verified_purchase" else
                         "Store names are unharmonized labels, not guaranteed unique seller identities. The distribution is metadata-record-weighted, not sales-weighted." if key=="store" else
                         "The file's selected download category and each record's main_category are different concepts. Other labels inside the file are not automatically classification errors.")
        if d["temporal"]:
            t=d["temporal"]
            lines += ["", "#### Timestamp distribution", ""]
            if t["n"]:
                peak=max(t["years"],key=t["years"].get)
                lines += [f"There are {t['n']:,} valid timestamp observations and {t['excluded_count']:,} excluded values. "
                          f"Observed coverage runs from `{t['earliest_utc']}` to `{t['latest_utc']}`. "
                          f"The median date is `{t['median_utc']}`; the middle half spans `{t['q1_utc']}` to `{t['q3_utc']}` "
                          f"(IQR {t['iqr_days']:.2f} days; full span {t['span_days']:.2f} days). "
                          f"The largest annual count occurs in {peak}: {t['years'][peak]:,} reviews ({100*t['years'][peak]/t['n']:.2f}% of valid timestamps). "
                          f"Outside the documented May 1996–September 2023 release window: {t['outside_documented_release_window_count']:,}. "
                          "The shape is a distribution of observed event times. It combines platform growth, coverage and review-writing behaviour; "
                          "a peak is not proof of a purchase peak. Boundary intervals are not complete periods.", "",
                          "| UTC year | Reviews | % valid timestamps |", "|---|---:|---:|"]
                for year in range(int(min(t["years"])),int(max(t["years"]))+1):
                    count=t["years"].get(str(year),0)
                    lines.append(f"| {year} | {count:,} | {100*count/t['n']:.3f} |")
            else: lines += ["No valid timestamps; no temporal distribution can be inferred."]
            lines += ["",f"![Timestamp distribution]({d['figures']['timestamp'][0]})"]
    lines += ["", "## 5. Initial analytical decisions and remaining work", "",
              "1. Preserve the raw files and this raw-record EDA as the reference. Extra exact copies can influence all review-weighted summaries; "
              "the derived exact-unique sensitivity below now quantifies this effect; further preprocessing remains a Phase 2 task.",
              "2. Retain zero votes and empty media containers as observed values. Keep missing prices separate; report valid-price denominators rather than filling with zero or an overall mean.",
              "3. Report median/IQR alongside mean/SD for asymmetric metrics. Log displays improve readability but do not establish lognormality or authorize deletion of large values.",
              "4. Do not drop a review from chronological ordering merely because its body is blank. Use validated parent IDs, ratings and timestamps when the later cohort is built.",
              "5. Preserve rare levels and sparse fields in the evidence. Any pooling, imputation, scaling or language restriction needs a separate justified rule and training-only fitting where applicable.",
              "6. Next tasks remain broader multivariate EDA, leakage-safe cohort/splits, and eventually reproducible preprocessing. "
              "This module does not calculate the first-five/next-ten target or demonstrate predictive improvement.", "",
              "## 6. Code-to-requirement map", "",
              "| Requirement | Code | Evidence |", "|---|---|---|",
              "| Full local scan and denominator control | `scan_file`, `parse_line`, `field_state` | JSON, field_states.csv, terminal |",
              "| Centre, dispersion, empirical shape | `describe`, `quantile` | numeric_summary.csv, numeric figure panels |",
              "| Class/category imbalance | `categorical_summary`, rating_balance in `scan_file` | categorical_frequencies.csv, bars, JSON |",
              "| Product/reviewer concentration | group counters in `scan_file`, `describe` | group distributions, Gini/top-1% share |",
              "| Temporal distribution | `timestamp`, `scan_file`, `plot_time` | temporal_frequencies.csv, annual/monthly figure |",
              "| Appropriate graphics | `plot_numeric`, `plot_categories`, `plot_states`, `plot_time` | figures/*.png and *.svg |",
              "| Interpretation and reproducibility | `interpret_numeric`, `make_report`, `run` | this regenerated report, source snapshot, manifest |", "",
              "## 7. Re-run and outputs", "", "Install requirements into the active Python environment, then run:", "",
              "```bash", "python -m pip install -r requirements_univariate.txt", "python univariate_eda.py", "```", "",
              "Defaults read the four files from `/Users/parsaanvari/Downloads/DataAnalysis` and write to `reports/phase1/univariate` beside the script. "
              "Use `--data-dir` and `--output-dir` to change locations. `--max-lines` is for smoke checks and creates partial results. "
              "Known output files in the selected directory are replaced on re-run; raw input files are never overwritten. "
              "The module regenerates this English report, every chart, `terminal_report.txt`, `univariate_eda.json`, numeric/categorical/field/temporal tables, "
              "compressed numeric frequencies and `univariate_eda_executed.py`. The manifest hashes all current run artifacts. "
              "Optional comparison with `../quality/quality_audit.json` uses source SHA-256 before comparing object counts. "
              "No quality result is invented when that file is absent. Numerical unit tests and full-run evidence checks are documented separately in validation.txt.", ""]
    lines += ["", "## 8. Entry counts versus usable multimodal content", "",
              "Entry-count metrics only describe array structure. The following evidence comes from the quality audit's validated left join and shared usability contracts. Source hashes, full scan counts, shared-contract version and reference time must match; otherwise no availability claim is imported.", ""]
    integrated=result.get("quality_availability_integration",{})
    if integrated.get("status")=="verified":
        for d in integrated["samples"]:
            lines += ["### "+d["category"], ""]
            lines += ext.markdown_table(d["rates"],[("modality","Facet"),("available","Available n"),("denominator","Reviews n"),("available_percent","Available %")])
    else: lines += ["Availability evidence was not integrated: "+str(integrated)+". Run quality_audit.py with matching files and --as-of, then rerun EDA."]
    lines += ["", "Image URL syntax is not image retrieval. Nonblank feature/description content is measured separately from entry count. Snapshot metadata availability does not establish availability at the fifth-review cutoff.", ""]
    return "\n".join(lines)


class Tee:
    def __init__(self,*streams): self.streams=streams
    def write(self,value):
        for stream in self.streams: stream.write(value); stream.flush()
        return len(value)
    def flush(self):
        for stream in self.streams: stream.flush()


def parser():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--data-dir",type=Path,default=DATA_DIR)
    p.add_argument("--output-dir",type=Path,default=OUTPUT_DIR)
    p.add_argument("--max-lines",type=int)
    p.add_argument("--progress-every",type=int,default=250000)
    p.add_argument("--as-of",default=None,help="ISO UTC reference for future timestamp checks; default current UTC")
    p.add_argument("--quality-json",type=Path,default=ROOT/"reports/phase1/quality/quality_audit.json")
    p.add_argument("--language-model",type=Path,default=ROOT/"models/lid.176.ftz")
    p.add_argument("--short-max-words",type=int,default=5)
    p.add_argument("--long-min-words",type=int,default=500)
    return p


def run(args):
    if args.max_lines is not None and args.max_lines<=0: raise ValueError("--max-lines must be positive")
    if args.progress_every<0: raise ValueError("--progress-every cannot be negative")
    reference_source="explicit --as-of" if args.as_of else "current UTC"
    reference=args.as_of
    if reference is None and args.quality_json.is_file():
        try:
            previous=json.loads(args.quality_json.read_text(encoding="utf-8"))
            if previous.get("runtime",{}).get("shared_contract")==CONTRACT_VERSION:
                reference=previous["audit_as_of_utc"]; reference_source="matching-contract quality audit reference"
        except (ValueError,KeyError,TypeError): pass
    as_of=datetime.fromisoformat(reference.replace("Z","+00:00")) if reference else datetime.now(UTC)
    if as_of.tzinfo is None: raise ValueError("--as-of requires a timezone")
    as_of=as_of.astimezone(UTC)
    out=args.output_dir.resolve(); out.mkdir(parents=True,exist_ok=True)
    if args.short_max_words<1 or args.long_min_words<=args.short_max_words: raise ValueError("Text thresholds must satisfy 1 <= short < long")
    args.detector=ext.LanguageDetector(args.language_model)
    started=datetime.now(UTC); clock=time.monotonic()
    original_stdout,original_stderr=sys.stdout,sys.stderr
    with (out/"terminal_report.txt").open("w",encoding="utf-8") as log:
        sys.stdout=Tee(original_stdout,log); sys.stderr=Tee(original_stderr,log)
        try:
            print(f"UNIVARIATE EDA v{VERSION} | reference={as_of.isoformat()}")
            matplotlib,plt=init_plotting(out)
            result=dict(version=VERSION,started_utc=started.isoformat(),reference_as_of_utc=as_of.isoformat(),reference_source=reference_source,
                 config=dict(data_dir=str(args.data_dir.resolve()),output_dir=str(out),max_lines=args.max_lines,progress_every=args.progress_every,short_max_words=args.short_max_words,long_min_words=args.long_min_words),
                 runtime=dict(python=sys.version,platform=platform.platform(),numpy=np.__version__,matplotlib=matplotlib.__version__),
                 source_code_sha256=file_sha(__file__),shared_contract=CONTRACT_VERSION,
                 helper_sha256={f:file_sha(ROOT/f) for f in ("audit_shared.py","eda_extensions.py")},
                 language_model=args.detector.manifest, datasets=[],errors=[],status="running")
            for name in DATASETS:
                path=args.data_dir/f"{name}.jsonl"
                if not path.exists() and path.with_suffix(".jsonl.gz").exists(): path=path.with_suffix(".jsonl.gz")
                if not path.exists(): result["errors"].append(f"Missing input: {path}"); continue
                data,hists=scan_file(name,path,args,as_of)
                with gzip.open(out/f"{name}__numeric_frequencies.csv.gz","wt",encoding="utf-8",newline="") as f:
                    w=csv.writer(f); w.writerow(["metric","value","count"])
                    for key,h in hists.items():
                        for value,count in sorted(h.items()): w.writerow([key,value,count])
                data["figures"]={}
                for key,metric in data["metrics"].items():
                    data["figures"][key]=plot_numeric(name,key,metric,hists[key],out,plt)
                for key,cat in data["categorical"].items(): data["figures"][key]=plot_categories(name,key,cat,out,plt)
                data["figures"]["field_states"]=plot_states(data,out,plt)
                if data["temporal"]: data["figures"]["timestamp"]=plot_time(data,out,plt)
                data["figures"].update(ext.plot_extensions(data,out,plt,save_figure))
                result["datasets"].append(data)
                print(f"FIGURES: {name}: {len(data['figures'])} panels saved as PNG and SVG",flush=True)
                del hists
            result["status"]="failed" if result["errors"] else "partial" if any(not d["complete"] for d in result["datasets"]) else "complete_with_parse_warnings" if any(d["parse_failures"] for d in result["datasets"]) else "complete"
            result["quality_availability_integration"]={"status":"unavailable"}
            result["prior_quality_comparison"]={"available":False}
            if args.quality_json.exists():
                try:
                    prior=json.loads(args.quality_json.read_text())
                    prior_data=prior.get("datasets",[])
                    if isinstance(prior_data,dict): prior_data=list(prior_data.values())
                    by_name={d["name"]:d for d in prior_data}
                    comparisons=[]
                    for d in result["datasets"]:
                        p=by_name.get(d["name"])
                        comparisons.append(dict(name=d["name"],prior_found=p is not None,
                            same_input_sha256=p is not None and d["source"]["sha256"]==p["source"]["sha256"],
                            same_object_count=p is not None and d["object_rows"]==p["object_rows"]))
                    result["prior_quality_comparison"]={"available":True,"file":str(args.quality_json),"comparisons":comparisons}
                    matched=(len(comparisons)==4 and all(c["same_input_sha256"] and c["same_object_count"] for c in comparisons)
                             and all(d["complete"] for d in result["datasets"]) and all(d.get("complete") for d in prior_data)
                             and prior.get("runtime",{}).get("shared_contract")==CONTRACT_VERSION
                             and prior.get("runtime",{}).get("helper_sha256",{}).get("audit_shared.py")==file_sha(ROOT/"audit_shared.py")
                             and prior.get("audit_as_of_utc")==as_of.isoformat())
                    result["quality_availability_integration"]=(dict(status="verified",quality_file_sha256=file_sha(args.quality_json),
                        samples=prior["multimodal"]["samples"]) if matched and "multimodal" in prior else dict(status="rejected_mismatching_or_incomplete_evidence"))
                except (ValueError,KeyError,TypeError) as e:
                    result["prior_quality_comparison"]={"available":False,"reason":str(e)}
            summary_rows=[]; cat_rows=[]; field_rows=[]; temporal_rows=[]
            for d in result["datasets"]:
                for key,m in d["metrics"].items():
                    summary_rows.append(dict(dataset=d["name"],metric=key,unit=m["unit"],observation_unit=m["observation_unit"],
                                             eligible_denominator=m["eligible_denominator"],excluded_count=m["excluded_count"],**m["summary"]))
                for key,cat in d["categorical"].items():
                    for row in cat["frequencies"]: cat_rows.append(dict(dataset=d["name"],field=key,**row))
                field_rows.extend(dict(dataset=d["name"],**r) for r in d["fields"])
                if d["temporal"]:
                    for granularity in ("years","months"):
                        for period,n in d["temporal"][granularity].items():
                            temporal_rows.append(dict(dataset=d["name"],granularity=granularity,period=period,count=n,percent_of_valid=pct(n,d["temporal"]["n"])))
            for filename,rows in (("numeric_summary.csv",summary_rows),("categorical_frequencies.csv",cat_rows),("field_states.csv",field_rows),("temporal_frequencies.csv",temporal_rows)):
                write_csv(out/filename,rows)
            write_json(out/"text_audit.json", {d["name"]:d["text_audit"] for d in result["datasets"] if "text_audit" in d})
            write_json(out/"deduplication_sensitivity.json", {d["name"]:d["deduplication_sensitivity"] for d in result["datasets"]})
            for f in ("audit_shared.py","eda_extensions.py"): shutil.copyfile(ROOT/f,out/f)
            shutil.copyfile(__file__,out/"univariate_eda_executed.py")
            result["finished_utc"]=datetime.now(UTC).isoformat(); result["elapsed_seconds"]=time.monotonic()-clock
            write_json(out/"univariate_eda.json",result)
            report=make_report(result)
            (out/"UNIVARIATE_EDA_REPORT_EN.md").write_text(report,encoding="utf-8")
            print("\n"+report)
            print("\nPRIOR QUALITY COMPARISON: "+json.dumps(result["prior_quality_comparison"]))
            print(f"\nSAVED: {out}\nSTATUS: {result['status']}\nELAPSED: {result['elapsed_seconds']:.1f} seconds")
        finally:
            sys.stdout=original_stdout; sys.stderr=original_stderr
    # Hash only artifacts generated by this run, never stale files from prior runs.
    names=["terminal_report.txt","univariate_eda.json","UNIVARIATE_EDA_REPORT_EN.md",
           "numeric_summary.csv","categorical_frequencies.csv","field_states.csv",
           "temporal_frequencies.csv","univariate_eda_executed.py", "audit_shared.py", "eda_extensions.py",
           "text_audit.json","deduplication_sensitivity.json"]
    names += [f"{d['name']}__numeric_frequencies.csv.gz" for d in result["datasets"]]
    names += [name for d in result["datasets"] for pair in d["figures"].values() for name in pair]
    paths=[out/name for name in names]
    write_json(out/"artifact_manifest.json",dict(source_code_sha256=result["source_code_sha256"],
               artifacts=[dict(path=str(p.relative_to(out)),bytes=p.stat().st_size,sha256=file_sha(p)) for p in sorted(paths)]))
    return 0 if result["status"].startswith("complete") else 2


if __name__=="__main__":
    raise SystemExit(run(parser().parse_args()))