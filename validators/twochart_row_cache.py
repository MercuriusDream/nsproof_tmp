#!/usr/bin/env python3
"""Serializable row cache helpers for two-chart Stage-0 diagnostics.

The cache records the floating rows actually passed to a sampled Stage-0
linear system.  It is intended for auditability and reuse by rank diagnostics;
it is not interval validation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from typing import Any


STATUS = "TWOCHART_ROW_CACHE_FLOATING_NOT_PROOF"


def sha256_file(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: str, data: dict[str, Any]) -> None:
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write("\n")


def variable_json(variable: Any, local_column: int) -> dict[str, Any]:
    if hasattr(variable, "as_json"):
        data = variable.as_json()
    else:
        data = {"label": str(variable)}
    data["local_column"] = local_column
    return data


def build_stage0_row_cache(
    *,
    profile_path: str,
    variables: list[Any],
    row_records: list[dict[str, Any]],
    residual_vector: list[float],
    jacobian_rows: list[list[float]],
    row_labels: list[str],
    row_scaling: dict[str, Any] | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if len(row_records) != len(residual_vector) or len(row_labels) != len(residual_vector):
        raise ValueError("row record, residual, and label counts must match")
    rows: list[dict[str, Any]] = []
    for index, record in enumerate(row_records):
        dense = jacobian_rows[index]
        rows.append(
            {
                **record,
                "row_id": record.get("row_id", f"row:{index}"),
                "row_index": index,
                "label": row_labels[index],
                "residual_after_scaling": float(residual_vector[index]),
                "jacobian_sparse_after_scaling": [
                    [column, float(value)] for column, value in enumerate(dense) if float(value) != 0.0
                ],
            }
        )
    profile_hash = sha256_file(profile_path) if profile_path and os.path.exists(profile_path) else ""
    return {
        "cache_schema": "twochart-row-cache-v1",
        "status": STATUS,
        "diagnostic_vs_proof": "floating sampled row cache only; no interval proof",
        "profile": profile_path,
        "profile_hash_sha256": profile_hash,
        "variables": [variable_json(variable, index) for index, variable in enumerate(variables)],
        "row_count": len(rows),
        "column_count": len(variables),
        "row_scaling": row_scaling or {},
        "extra": extra or {},
        "rows": rows,
    }


def self_test() -> dict[str, Any]:
    variables = ["x0", "x1"]
    row_records = [
        {"row_id": "mortar:0", "label": "mortar", "residual_raw": 10.0},
        {"row_id": "active_guard:0", "label": "active_guard", "residual_raw": 2.0},
    ]
    return build_stage0_row_cache(
        profile_path="",
        variables=variables,
        row_records=row_records,
        residual_vector=[10.0, 2.0],
        jacobian_rows=[[1.0, 0.0], [0.0, 1.0]],
        row_labels=["mortar", "active_guard"],
        extra={"self_test": True},
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--out", default="")
    args = parser.parse_args()
    if not args.self_test:
        parser.error("only --self-test is currently supported")
    cache = self_test()
    if args.out:
        write_json(args.out, cache)
    print(f"status={cache['status']}")
    print(f"rows={cache['row_count']} columns={cache['column_count']}")


if __name__ == "__main__":
    main()
