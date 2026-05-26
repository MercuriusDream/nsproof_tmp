#!/usr/bin/env python3
"""Inventory two-chart coefficient variables.

This is a schema/accounting helper for the two-chart profile projection JSON.
It enumerates the stored tail Chebyshev coefficients and origin Taylor basis
entries as coefficient variables.  It does not evaluate residuals, update
coefficients, or make proof claims.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
TWOCHART_FORMAT = "twochart_profile_projection_v1"
STATUS = "TWOCHART_COEFFICIENT_INVENTORY_NOT_PROOF"

TAIL_BLOCKS: tuple[tuple[str, str, str], ...] = (
    ("F_an", "F", "analytic"),
    ("G_an", "G", "analytic"),
    ("F_frac", "F", "fractional"),
    ("G_frac", "G", "fractional"),
)
ORIGIN_BLOCKS: tuple[tuple[str, str], ...] = (
    ("F_origin_taylor", "F"),
    ("G_origin_taylor", "G"),
)


def load_json(path: str) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise ValueError(f"{path!r} must contain a JSON object")
    return data


def save_json(path: str, data: dict[str, Any]) -> None:
    out_dir = os.path.dirname(path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write("\n")


def relpath(path: str) -> str:
    if not path:
        return path
    return os.path.relpath(path, ROOT_DIR) if os.path.isabs(path) else path


def resolve_path(path: str) -> str:
    if os.path.isabs(path):
        return path
    direct = os.path.join(os.getcwd(), path)
    if os.path.exists(direct):
        return direct
    return os.path.join(ROOT_DIR, path)


def enforce_twochart_tail_gate(data: dict[str, Any], profile: str) -> None:
    if data.get("format") != TWOCHART_FORMAT:
        raise ValueError(f"{profile!r} is not a {TWOCHART_FORMAT} JSON file")
    tail = data.get("tail_legality")
    if not isinstance(tail, dict):
        raise ValueError("two-chart profile is missing tail_legality metadata")
    if not bool(tail.get("all_ok", False)):
        raise ValueError(f"tail_legality.all_ok is not true: status={tail.get('status')!r}")
    if tail.get("q2_policy") != "zero":
        raise ValueError(f"expected tail_legality.q2_policy='zero', got {tail.get('q2_policy')!r}")
    requested = data.get("requested_options")
    if isinstance(requested, dict) and requested.get("q2_policy") != "zero":
        raise ValueError(f"expected requested_options.q2_policy='zero', got {requested.get('q2_policy')!r}")
    if "q2_ok" in tail and not bool(tail.get("q2_ok")):
        raise ValueError("tail_legality.q2_ok is false under q2_policy=zero")


def require_dict(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    return value


def require_list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"{label} must be a list")
    return value


def coefficient_rows(coeffs: Any, label: str) -> list[list[Any]]:
    rows = require_list(coeffs, label)
    if not rows:
        raise ValueError(f"{label} must not be empty")
    width: int | None = None
    out: list[list[Any]] = []
    for kq, row in enumerate(rows):
        row_items = require_list(row, f"{label}[{kq}]")
        if width is None:
            width = len(row_items)
        elif len(row_items) != width:
            raise ValueError(f"{label} rows must have stable width")
        out.append(row_items)
    return out


def patch_record_base(
    block_name: str,
    component: str,
    block_kind: str,
    frac_index: int | None,
    patch_index: int,
    patch: dict[str, Any],
) -> dict[str, Any]:
    return {
        "chart": "tail",
        "component": component,
        "block": f"tail.{block_name}",
        "block_kind": block_kind,
        "frac_index": frac_index,
        "patch_index": patch_index,
        "q_interval": patch.get("q_interval"),
        "x_interval": patch.get("x_interval"),
    }


def tail_records(data: dict[str, Any]) -> list[dict[str, Any]]:
    tail = require_dict(data.get("tail_chart"), "tail_chart")
    blocks = require_dict(tail.get("blocks"), "tail_chart.blocks")
    records: list[dict[str, Any]] = []
    for block_name, component, block_kind in TAIL_BLOCKS:
        raw_block = require_list(blocks.get(block_name), f"tail_chart.blocks.{block_name}")
        if block_kind == "fractional":
            frac_blocks = raw_block
        else:
            frac_blocks = [raw_block]
        for frac_index, raw_patches in enumerate(frac_blocks):
            patches = require_list(raw_patches, f"tail_chart.blocks.{block_name}[{frac_index}]")
            stored_frac_index = frac_index if block_kind == "fractional" else None
            for patch_index, raw_patch in enumerate(patches):
                patch = require_dict(raw_patch, f"tail_chart.blocks.{block_name}[{frac_index}][{patch_index}]")
                coeffs = coefficient_rows(patch.get("coeffs"), f"{block_name}[{frac_index}][{patch_index}].coeffs")
                base = patch_record_base(block_name, component, block_kind, stored_frac_index, patch_index, patch)
                for kq, row in enumerate(coeffs):
                    for kx, value in enumerate(row):
                        record = dict(base)
                        record.update(
                            {
                                "kq": kq,
                                "kx": kx,
                                "coefficient": float(value),
                                "variable_id": variable_id(base, kq=kq, kx=kx),
                            }
                        )
                        records.append(record)
    return records


def origin_records(data: dict[str, Any]) -> list[dict[str, Any]]:
    origin = require_dict(data.get("origin_chart"), "origin_chart")
    blocks = require_dict(origin.get("blocks"), "origin_chart.blocks")
    records: list[dict[str, Any]] = []
    for block_name, component in ORIGIN_BLOCKS:
        block = require_dict(blocks.get(block_name), f"origin_chart.blocks.{block_name}")
        basis = require_list(block.get("basis"), f"origin_chart.blocks.{block_name}.basis")
        for index, raw_entry in enumerate(basis):
            entry = require_dict(raw_entry, f"origin_chart.blocks.{block_name}.basis[{index}]")
            r_power = int(entry["R_power"])
            z_power = int(entry["Z_power"])
            record = {
                "chart": "origin",
                "component": component,
                "block": f"origin.{block_name}",
                "block_kind": "taylor",
                "frac_index": None,
                "patch_index": None,
                "origin_basis_index": index,
                "R_power": r_power,
                "Z_power": z_power,
                "coefficient": float(entry["coeff"]),
            }
            record["variable_id"] = variable_id(record)
            records.append(record)
    return records


def variable_id(record: dict[str, Any], kq: int | None = None, kx: int | None = None) -> str:
    block = str(record["block"])
    if record["chart"] == "origin":
        return (
            f"{block}[{record['origin_basis_index']}]"
            f"[R^{record['R_power']},Z^{record['Z_power']}]"
        )
    frac_index = record.get("frac_index")
    patch = record["patch_index"]
    if frac_index is None:
        return f"{block}[patch={patch}][kq={kq},kx={kx}]"
    return f"{block}[frac={frac_index}][patch={patch}][kq={kq},kx={kx}]"


def increment_nested(counts: dict[str, Any], *keys: str) -> None:
    cursor = counts
    for key in keys[:-1]:
        cursor = cursor.setdefault(key, {})
    cursor[keys[-1]] = int(cursor.get(keys[-1], 0)) + 1


def count_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    counts: dict[str, Any] = {
        "total": len(records),
        "by_chart": {},
        "by_component": {},
        "by_block": {},
        "by_chart_component": {},
        "by_chart_component_block": {},
    }
    for record in records:
        chart = str(record["chart"])
        component = str(record["component"])
        block = str(record["block"])
        increment_nested(counts["by_chart"], chart)
        increment_nested(counts["by_component"], component)
        increment_nested(counts["by_block"], block)
        increment_nested(counts["by_chart_component"], chart, component)
        increment_nested(counts["by_chart_component_block"], chart, component, block)
    return counts


def deterministic_sample(records: list[dict[str, Any]], sample_size: int) -> list[dict[str, Any]]:
    if sample_size <= 0 or not records:
        return []
    if sample_size >= len(records):
        return records
    if sample_size == 1:
        return [records[0]]
    indexes = sorted({round(i * (len(records) - 1) / (sample_size - 1)) for i in range(sample_size)})
    return [records[index] for index in indexes]


def layout_summary(data: dict[str, Any]) -> dict[str, Any]:
    tail = require_dict(data.get("tail_chart"), "tail_chart")
    origin = require_dict(data.get("origin_chart"), "origin_chart")
    return {
        "tail_patch_layout": tail.get("patch_layout"),
        "tail_active_patch_counts": tail.get("active_patch_counts"),
        "origin_basis": origin.get("basis"),
    }


def build_inventory(profile_path: str, sample_size: int, include_records: bool) -> dict[str, Any]:
    resolved = resolve_path(profile_path)
    data = load_json(resolved)
    enforce_twochart_tail_gate(data, profile_path)
    records = tail_records(data) + origin_records(data)
    result = {
        "status": STATUS,
        "diagnostic_vs_proof": "coefficient inventory only; no residual, interval, or proof claim",
        "profile": relpath(resolved),
        "format": data.get("format"),
        "source_profile_json": data.get("source_profile_json"),
        "parameters": {
            "gamma": data.get("gamma"),
            "B": data.get("B"),
            "p": data.get("p"),
        },
        "tail_gate": {
            "all_ok": data["tail_legality"].get("all_ok"),
            "q2_policy": data["tail_legality"].get("q2_policy"),
            "q2_ok": data["tail_legality"].get("q2_ok"),
            "status": data["tail_legality"].get("status"),
        },
        "unknown_blocks": data.get("hard_newton_schema", {}).get("unknown_blocks", []),
        "layout": layout_summary(data),
        "counts": count_records(records),
        "sample_size_requested": sample_size,
        "sample": deterministic_sample(records, sample_size),
        "records_included": include_records,
    }
    if include_records:
        result["records"] = records
    else:
        result["records_note"] = "Full coefficient records omitted; rerun with --include-records to emit them."
    return result


def print_summary(inventory: dict[str, Any]) -> None:
    counts = inventory["counts"]
    print(f"profile={inventory['profile']}")
    print(f"status={inventory['status']}")
    gate = inventory["tail_gate"]
    print(f"tail_legality_all_ok={gate['all_ok']} q2_policy={gate['q2_policy']} q2_ok={gate['q2_ok']}")
    print(f"total_coefficients={counts['total']}")
    print(f"by_chart={json.dumps(counts['by_chart'], sort_keys=True)}")
    print(f"by_component={json.dumps(counts['by_component'], sort_keys=True)}")
    print(f"by_block={json.dumps(counts['by_block'], sort_keys=True)}")
    print(f"sample_count={len(inventory['sample'])}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", default="work/v117_twochart_init.json", help="twochart_profile_projection_v1 JSON")
    parser.add_argument("--out", default="", help="Optional coefficient inventory JSON output")
    parser.add_argument("--sample-size", type=int, default=12, help="Deterministic sample size to include")
    parser.add_argument("--include-records", action="store_true", help="Include the full coefficient record list.")
    args = parser.parse_args()

    if args.sample_size < 0:
        raise ValueError("--sample-size must be nonnegative")

    inventory = build_inventory(args.profile, args.sample_size, args.include_records)
    print_summary(inventory)
    if args.out:
        save_json(args.out, inventory)
        print(f"saved={args.out}")


if __name__ == "__main__":
    try:
        main()
    except BrokenPipeError:
        sys.exit(1)
