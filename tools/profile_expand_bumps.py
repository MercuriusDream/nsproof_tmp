#!/usr/bin/env python3
"""Expand the tail-flat interior bump grid of a compactified profile seed.

The minimax profile continuations use localized bump coefficients indexed by
``interior_bump_q_centers`` and ``interior_bump_b2_centers``.  This helper adds
new centers while remapping existing coefficients by their old physical center
locations, so that an expanded seed starts from the same profile plus zero
coefficients for the new degrees of freedom.
"""

from __future__ import annotations

import argparse
import copy
import json
from typing import Iterable


Coeff = tuple[int, int, float]


def parse_float_list(raw: str) -> list[float]:
    values = [float(item) for item in raw.split(",") if item.strip()]
    if not values:
        raise argparse.ArgumentTypeError("at least one center is required")
    return sorted(values)


def load_data(path: str) -> dict[str, object]:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def as_float_list(data: dict[str, object], key: str) -> list[float]:
    raw = data.get(key, [])
    if not isinstance(raw, list):
        raise ValueError(f"{key} must be a list")
    return [float(value) for value in raw]


def coeffs(data: dict[str, object], key: str) -> list[Coeff]:
    raw = data.get(key, [])
    if not isinstance(raw, list):
        raise ValueError(f"{key} must be a list")
    return [(int(i), int(j), float(value)) for i, j, value in raw]


def center_index(values: Iterable[float]) -> dict[float, int]:
    return {round(value, 14): index for index, value in enumerate(values)}


def remap_coeffs(
    old_coeffs: list[Coeff],
    old_q_centers: list[float],
    old_b2_centers: list[float],
    new_q_centers: list[float],
    new_b2_centers: list[float],
) -> list[list[float]]:
    new_values: dict[tuple[int, int], float] = {
        (i, j): 0.0
        for i in range(len(new_q_centers))
        for j in range(len(new_b2_centers))
    }
    q_lookup = center_index(new_q_centers)
    b2_lookup = center_index(new_b2_centers)

    for i, j, value in old_coeffs:
        if i < 0 or i >= len(old_q_centers):
            raise ValueError(f"old q-index out of range: {i}")
        if j < 0 or j >= len(old_b2_centers):
            raise ValueError(f"old b2-index out of range: {j}")
        q_key = round(old_q_centers[i], 14)
        b2_key = round(old_b2_centers[j], 14)
        if q_key not in q_lookup:
            raise ValueError(f"new q-centers do not preserve old center {old_q_centers[i]}")
        if b2_key not in b2_lookup:
            raise ValueError(f"new b2-centers do not preserve old center {old_b2_centers[j]}")
        new_key = (q_lookup[q_key], b2_lookup[b2_key])
        new_values[new_key] = new_values.get(new_key, 0.0) + value

    return [[i, j, new_values[(i, j)]] for i, j in sorted(new_values)]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed-json", required=True)
    parser.add_argument("--save-json", required=True)
    parser.add_argument("--q-centers", required=True, type=parse_float_list)
    parser.add_argument("--b2-centers", required=True, type=parse_float_list)
    parser.add_argument("--note", default="")
    args = parser.parse_args()

    data = load_data(args.seed_json)
    old_q_centers = as_float_list(data, "interior_bump_q_centers")
    old_b2_centers = as_float_list(data, "interior_bump_b2_centers")
    if not old_q_centers or not old_b2_centers:
        raise SystemExit("seed has no interior bump centers to expand")

    old_q_set = set(round(value, 14) for value in old_q_centers)
    new_q_set = set(round(value, 14) for value in args.q_centers)
    missing_q = sorted(old_q_set - new_q_set)
    if missing_q:
        raise SystemExit(f"new q-centers must include old centers: {missing_q}")

    old_b2_set = set(round(value, 14) for value in old_b2_centers)
    new_b2_set = set(round(value, 14) for value in args.b2_centers)
    missing_b2 = sorted(old_b2_set - new_b2_set)
    if missing_b2:
        raise SystemExit(f"new b2-centers must include old centers: {missing_b2}")

    out = copy.deepcopy(data)
    out["interior_bump_q_centers"] = args.q_centers
    out["interior_bump_b2_centers"] = args.b2_centers
    for key in ("f_interior_bump_coeffs", "g_interior_bump_coeffs"):
        out[key] = remap_coeffs(
            coeffs(data, key),
            old_q_centers,
            old_b2_centers,
            args.q_centers,
            args.b2_centers,
        )
    out["evidence"] = {
        "status": "expanded_tail_flat_interior_bump_seed",
        "source": args.seed_json,
        "old_q_centers": old_q_centers,
        "old_b2_centers": old_b2_centers,
        "new_q_centers": args.q_centers,
        "new_b2_centers": args.b2_centers,
        "note": args.note,
    }

    with open(args.save_json, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print(f"saved expanded bump seed: {args.save_json}")
    print(f"q_centers: {old_q_centers} -> {args.q_centers}")
    print(f"b2_centers: {old_b2_centers} -> {args.b2_centers}")


if __name__ == "__main__":
    main()
