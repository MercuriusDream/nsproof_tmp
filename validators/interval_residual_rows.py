#!/usr/bin/env python3
"""Build outward-double interval ledgers for sampled residual rows.

This module consumes stored exact-residual audit summaries and/or two-chart row
caches.  It widens each available sampled scalar residual value by one double
ulp on both sides.  The result is proof-facing row data, not a continuous
interval residual proof.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import subprocess
from collections import Counter
from decimal import Decimal
from pathlib import Path
from statistics import median
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "nsproof-cert-v1"
CERTIFICATE_NAME = "interval_residual_rows"
STATUS = "OUTWARD_DOUBLE_INTERVAL_ROWS_NOT_DOMAIN_PROOF"
BACKEND = "python-math.nextafter-outward-double"

RESIDUAL_COMPONENT_KEYS = (
    "e_psi",
    "e_gamma",
    "e_Gamma",
    "E_psi",
    "E_Gamma",
)
ROW_CACHE_VALUE_KEYS = (
    "residual_raw",
    "residual_weighted_before_scaling",
    "residual_after_scaling",
)
ROW_CACHE_METADATA_KEYS = (
    "row_index",
    "row_id",
    "label",
    "row_type",
    "component",
    "q",
    "b",
    "x",
    "weight",
)


def resolve_path(path: str | os.PathLike[str]) -> Path:
    raw = Path(path)
    if raw.is_absolute():
        return raw
    direct = Path.cwd() / raw
    if direct.exists():
        return direct
    return ROOT_DIR / raw


def relpath(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT_DIR))
    except ValueError:
        return str(path)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_json_hash(value: Any) -> str:
    payload = json.dumps(value, allow_nan=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def repo_commit() -> str:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT_DIR,
            stderr=subprocess.DEVNULL,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return ""
    return out.strip()


def save_json(path: str | os.PathLike[str], data: dict[str, Any]) -> None:
    out_path = Path(path)
    if out_path.parent:
        out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, allow_nan=False, indent=2, sort_keys=True)
        fh.write("\n")


def code_hashes() -> dict[str, str]:
    files = (
        "validators/interval_residual_rows.py",
        "tools/validate_interval_residual_rows.py",
    )
    hashes: dict[str, str] = {}
    for item in files:
        path = ROOT_DIR / item
        if path.exists():
            hashes[item] = sha256_file(path)
    return hashes


def numeric_float(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    out = float(value)
    if not math.isfinite(out):
        return None
    return out


def outward_interval(value: float) -> dict[str, float]:
    if not math.isfinite(value):
        raise ValueError(f"cannot interval-wrap nonfinite value: {value!r}")
    interval = {
        "lo": math.nextafter(value, -math.inf),
        "hi": math.nextafter(value, math.inf),
    }
    validate_interval(interval)
    return interval


def validate_interval(interval: dict[str, Any]) -> None:
    lo = numeric_float(interval.get("lo"))
    hi = numeric_float(interval.get("hi"))
    if lo is None or hi is None:
        raise ValueError(f"interval endpoints must be finite floats: {interval!r}")
    if lo > hi:
        raise ValueError(f"interval is reversed: lo={lo!r} hi={hi!r}")


def interval_width(interval: dict[str, float]) -> float:
    return float(interval["hi"] - interval["lo"])


def interval_max_abs_upper(interval: dict[str, float]) -> float:
    return max(abs(float(interval["lo"])), abs(float(interval["hi"])))


def row_entry(
    *,
    source: str,
    row_family: str,
    row_id: str,
    value_role: str,
    value: float,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    interval = outward_interval(value)
    return {
        "source": source,
        "row_family": row_family,
        "row_id": row_id,
        "value_role": value_role,
        "sample_value": value,
        "interval": interval,
        "width": interval_width(interval),
        "max_abs_upper": interval_max_abs_upper(interval),
        "metadata": metadata or {},
    }


def read_json_source(kind: str, path_arg: str) -> tuple[dict[str, Any] | None, dict[str, Any], list[str]]:
    path = resolve_path(path_arg)
    source: dict[str, Any] = {
        "kind": kind,
        "path": relpath(path),
        "exists": path.exists(),
        "sha256": None,
        "schema_version": None,
        "certificate_name": None,
        "status": None,
        "pass": None,
        "profile": None,
        "profile_hash_sha256": None,
    }
    blockers: list[str] = []
    if not path.exists():
        blockers.append(f"{kind} input is missing: {source['path']}")
        return None, source, blockers
    source["sha256"] = sha256_file(path)
    try:
        with path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        blockers.append(f"{kind} input could not be parsed: {exc}")
        return None, source, blockers
    if not isinstance(data, dict):
        blockers.append(f"{kind} input root is not a JSON object")
        return None, source, blockers
    profile_hash = data.get("profile_hash_sha256")
    if not profile_hash and isinstance(data.get("input_hashes"), dict):
        profile_hash = data["input_hashes"].get("profile")
    source.update(
        {
            "schema_version": data.get("schema_version"),
            "certificate_name": data.get("certificate_name"),
            "status": data.get("status"),
            "pass": data.get("pass"),
            "profile": data.get("profile"),
            "profile_hash_sha256": profile_hash,
        }
    )
    return data, source, blockers


def compact_metadata(data: dict[str, Any], keys: tuple[str, ...]) -> dict[str, Any]:
    return {key: data[key] for key in keys if key in data}


def rows_from_exact_residual_audit(audit: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    blockers: list[str] = []
    scans = audit.get("residual_blocks", {}).get("scans", {})
    if isinstance(scans, dict):
        for scan_name in sorted(scans):
            scan = scans[scan_name]
            if not isinstance(scan, dict):
                continue
            worst = scan.get("worst")
            if not isinstance(worst, dict):
                blockers.append(f"residual scan {scan_name!r} has no stored worst sample")
                continue
            metadata = {
                "scan": scan_name,
                "chart": scan.get("chart"),
                "label": scan.get("label"),
                "residual_kind": scan.get("residual_kind"),
                **compact_metadata(worst, ("q", "b", "r", "z")),
            }
            for key in RESIDUAL_COMPONENT_KEYS:
                value = numeric_float(worst.get(key))
                if value is None:
                    continue
                rows.append(
                    row_entry(
                        source="exact_residual_audit",
                        row_family="residual_scan_worst",
                        row_id=f"scan:{scan_name}:{key}",
                        value_role=key,
                        value=value,
                        metadata=metadata,
                    )
                )
    else:
        blockers.append("exact residual audit has no residual_blocks.scans object")

    mortar_summary = audit.get("mortar", {}).get("summary", {})
    if isinstance(mortar_summary, dict):
        worst = mortar_summary.get("worst")
        if isinstance(worst, dict):
            value = numeric_float(worst.get("residual_tail_minus_origin"))
            value_role = "residual_tail_minus_origin"
            if value is None:
                value = numeric_float(worst.get("abs_residual"))
                value_role = "abs_residual"
            if value is not None:
                metadata = compact_metadata(
                    worst,
                    (
                        "row_index",
                        "component",
                        "coordinate",
                        "derivative",
                        "dq_order",
                        "dx_order",
                        "total_order",
                        "q",
                        "x",
                    ),
                )
                rows.append(
                    row_entry(
                        source="exact_residual_audit",
                        row_family="mortar_worst",
                        row_id="mortar:summary:worst",
                        value_role=value_role,
                        value=value,
                        metadata=metadata,
                    )
                )
        groups = mortar_summary.get("groups", [])
        if isinstance(groups, list):
            for index, group in enumerate(groups):
                if not isinstance(group, dict):
                    continue
                value = numeric_float(group.get("max_abs"))
                if value is None:
                    continue
                key = str(group.get("key", f"group:{index}"))
                metadata = compact_metadata(
                    group,
                    ("key", "component", "coordinate", "derivative", "dq_order", "dx_order", "count"),
                )
                rows.append(
                    row_entry(
                        source="exact_residual_audit",
                        row_family="mortar_group_max_abs",
                        row_id=f"mortar:group:{key}",
                        value_role="max_abs",
                        value=value,
                        metadata=metadata,
                    )
                )
    else:
        blockers.append("exact residual audit has no mortar.summary object")

    if rows and not any(row["row_family"] == "residual_scan_sample" for row in rows):
        blockers.append(
            "exact residual audit stores scan/mortar summaries, not full domain interval residual rows"
        )
    return rows, blockers


def row_cache_family(row: dict[str, Any]) -> str:
    text = " ".join(
        str(row.get(key, "")) for key in ("label", "row_type", "row_id", "component")
    ).lower()
    if "mortar" in text:
        return "row_cache_mortar"
    if "guard" in text:
        return "row_cache_guard"
    if "pde" in text or "residual" in text:
        return "row_cache_residual"
    return "row_cache_other"


def rows_from_row_cache(row_cache: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    blockers: list[str] = []
    raw_rows = row_cache.get("rows")
    if not isinstance(raw_rows, list):
        return rows, ["row cache has no rows array"]
    for index, row in enumerate(raw_rows):
        if not isinstance(row, dict):
            continue
        metadata = compact_metadata(row, ROW_CACHE_METADATA_KEYS)
        source_row_id = str(row.get("row_id", f"row:{index}"))
        family = row_cache_family(row)
        for key in ROW_CACHE_VALUE_KEYS:
            value = numeric_float(row.get(key))
            if value is None:
                continue
            rows.append(
                row_entry(
                    source="row_cache",
                    row_family=family,
                    row_id=f"{source_row_id}:{key}",
                    value_role=key,
                    value=value,
                    metadata=metadata,
                )
            )
    if not rows:
        blockers.append("row cache contains no finite residual scalar values")
    return rows, blockers


def width_stats(rows: list[dict[str, Any]]) -> dict[str, Any]:
    widths = [float(row["width"]) for row in rows]
    if not widths:
        return {"count": 0, "max": None, "median": None}
    return {
        "count": len(widths),
        "max": max(widths),
        "median": float(median(widths)),
    }


def max_abs_stats(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {
            "max_abs_upper": None,
            "worst_row_id": None,
            "per_source": {},
            "per_family": {},
        }
    worst = max(rows, key=lambda row: float(row["max_abs_upper"]))
    per_source: dict[str, float] = {}
    per_family: dict[str, float] = {}
    for row in rows:
        bound = float(row["max_abs_upper"])
        per_source[row["source"]] = max(per_source.get(row["source"], 0.0), bound)
        per_family[row["row_family"]] = max(per_family.get(row["row_family"], 0.0), bound)
    return {
        "max_abs_upper": float(worst["max_abs_upper"]),
        "worst_row_id": worst["row_id"],
        "per_source": per_source,
        "per_family": per_family,
    }


def profile_hash_report(sources: list[dict[str, Any]]) -> dict[str, Any]:
    by_source = {
        source["kind"]: source.get("profile_hash_sha256")
        for source in sources
        if source.get("profile_hash_sha256")
    }
    unique = sorted(set(by_source.values()))
    return {
        "profile_hash_sha256": unique[0] if len(unique) == 1 else None,
        "profile_hashes": unique,
        "by_source": by_source,
        "consistent": len(unique) <= 1,
    }


def build_interval_residual_row_ledger(
    *,
    exact_residual_audit: str = "",
    row_cache: str = "",
    command: list[str] | None = None,
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    sources: list[dict[str, Any]] = []
    blockers: list[str] = []
    input_hashes: dict[str, str | None] = {}

    if exact_residual_audit:
        audit, source, source_blockers = read_json_source("exact_residual_audit", exact_residual_audit)
        sources.append(source)
        input_hashes["exact_residual_audit"] = source.get("sha256")
        blockers.extend(source_blockers)
        if audit is not None:
            audit_rows, audit_blockers = rows_from_exact_residual_audit(audit)
            rows.extend(audit_rows)
            blockers.extend(audit_blockers)

    if row_cache:
        cache, source, source_blockers = read_json_source("row_cache", row_cache)
        sources.append(source)
        input_hashes["row_cache"] = source.get("sha256")
        blockers.extend(source_blockers)
        if cache is not None:
            cache_rows, cache_blockers = rows_from_row_cache(cache)
            rows.extend(cache_rows)
            blockers.extend(cache_blockers)

    if not sources:
        blockers.append("no exact residual audit or row cache input was supplied")
    if not rows:
        blockers.append("no finite sampled residual row values were available to interval-wrap")

    profile_hashes = profile_hash_report(sources)
    if not profile_hashes["consistent"]:
        blockers.append("input profile hashes are inconsistent")

    blockers.extend(
        [
            "domain Bernstein/Arb residual bounds are missing for compactified residual equations",
            "Z2/tail complement interval bound is missing",
            "sampled nextafter double intervals are row data only, not continuous-domain enclosures",
        ]
    )

    row_counts = Counter(row["row_family"] for row in rows)
    source_counts = Counter(row["source"] for row in rows)
    interval_bounds = max_abs_stats(rows)
    interval_widths = width_stats(rows)
    hashes = code_hashes()
    row_interval_hash = stable_json_hash(
        {
            "backend": BACKEND,
            "rows": rows,
            "sources": sources,
            "profile_hashes": profile_hashes,
        }
    )

    return {
        "schema_version": SCHEMA_VERSION,
        "certificate_name": CERTIFICATE_NAME,
        "status": STATUS,
        "status_detail": "outward-double interval row data only; not a final interval domain proof",
        "pass": False,
        "repo_commit": repo_commit(),
        "backend": BACKEND,
        "precision_bits": 53,
        "rounding_mode": "stored nearest-double samples widened with math.nextafter toward +/-inf",
        "mathematical_statement": (
            "Each stored sampled scalar residual or mortar row value is enclosed by "
            "one-ulp outward double endpoints. These rows do not bound the full "
            "compactified residual domain."
        ),
        "profile_hash_sha256": profile_hashes["profile_hash_sha256"],
        "profile_hash_report": profile_hashes,
        "input_hashes": input_hashes,
        "code_hashes": hashes,
        "dependency_hashes": {
            "row_interval_payload": row_interval_hash,
        },
        "sources": sources,
        "row_count": len(rows),
        "row_counts_by_source": dict(sorted(source_counts.items())),
        "row_counts_by_family": dict(sorted(row_counts.items())),
        "interval_bounds": interval_bounds,
        "interval_max_abs_upper_bound": interval_bounds["max_abs_upper"],
        "interval_widths": interval_widths,
        "rows": rows,
        "blockers": blockers,
        "failure_reason": "; ".join(blockers),
        "commands": [" ".join(command)] if command else [],
    }


def interval_contains_exact_float(interval: dict[str, float], value: float) -> bool:
    exact = Decimal.from_float(value)
    lo = Decimal.from_float(interval["lo"])
    hi = Decimal.from_float(interval["hi"])
    return lo <= exact <= hi


def self_test() -> dict[str, Any]:
    values = [
        0.0,
        -0.0,
        1.0,
        -2.5,
        math.ldexp(1.0, -1022),
        1.0 / 3.0,
    ]
    rows = [
        row_entry(
            source="self_test",
            row_family="manufactured",
            row_id=f"manufactured:{index}",
            value_role="exact_float",
            value=value,
            metadata={},
        )
        for index, value in enumerate(values)
    ]
    contains = [
        interval_contains_exact_float(row["interval"], float(row["sample_value"]))
        for row in rows
    ]
    reversed_rejected = False
    reversed_error = ""
    try:
        validate_interval({"lo": 1.0, "hi": 0.0})
    except ValueError as exc:
        reversed_rejected = True
        reversed_error = str(exc)
    return {
        "pass": all(contains) and reversed_rejected,
        "manufactured_case_count": len(values),
        "contains_manufactured_exact_values": contains,
        "reversed_interval_rejected": reversed_rejected,
        "reversed_interval_error": reversed_error,
        "interval_widths": width_stats(rows),
    }
