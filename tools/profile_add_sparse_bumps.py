#!/usr/bin/env python3
"""Add sparse zero-start interior bump degrees of freedom to a seed.

``profile_expand_bumps.py`` expands to a full tensor product of q and b^2
centers.  When topology scans identify only a few missing lobes, this helper
adds just those center pairs.  Existing coefficients are remapped by their old
center coordinates, and each requested pair is inserted with coefficient zero
for both F and G unless it already exists.
"""

from __future__ import annotations

import argparse
import copy
import json
from typing import Iterable


Coeff = tuple[int, int, float]


def load_data(path: str) -> dict[str, object]:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def float_key(value: float) -> float:
    return round(value, 14)


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


def parse_pairs(raw: str) -> list[tuple[float, float]]:
    pairs: list[tuple[float, float]] = []
    for item in raw.split(";"):
        if not item.strip():
            continue
        parts = [part.strip() for part in item.split(",") if part.strip()]
        if len(parts) != 2:
            raise argparse.ArgumentTypeError(f"bad pair {item!r}; expected q,b2")
        q = float(parts[0])
        b2 = float(parts[1])
        if not (0.0 < q < 1.0):
            raise argparse.ArgumentTypeError(f"q must lie in (0,1): {q}")
        if not (0.0 <= b2 < 1.0):
            raise argparse.ArgumentTypeError(f"b2 must lie in [0,1): {b2}")
        pairs.append((q, b2))
    if not pairs:
        raise argparse.ArgumentTypeError("at least one q,b2 pair is required")
    return pairs


def merge_centers(old: Iterable[float], additions: Iterable[float]) -> list[float]:
    values = {float_key(value): float(value) for value in old}
    for value in additions:
        values.setdefault(float_key(value), float(value))
    return [values[key] for key in sorted(values)]


def index_map(values: Iterable[float]) -> dict[float, int]:
    return {float_key(value): index for index, value in enumerate(values)}


def remap_old_coeffs(
    old_coeffs: list[Coeff],
    old_q_centers: list[float],
    old_b2_centers: list[float],
    new_q_index: dict[float, int],
    new_b2_index: dict[float, int],
) -> dict[tuple[int, int], float]:
    out: dict[tuple[int, int], float] = {}
    for i, j, value in old_coeffs:
        if i < 0 or i >= len(old_q_centers):
            raise ValueError(f"old q-index out of range: {i}")
        if j < 0 or j >= len(old_b2_centers):
            raise ValueError(f"old b2-index out of range: {j}")
        q_new = new_q_index[float_key(old_q_centers[i])]
        b2_new = new_b2_index[float_key(old_b2_centers[j])]
        out[(q_new, b2_new)] = out.get((q_new, b2_new), 0.0) + value
    return out


def serialize_coeffs(values: dict[tuple[int, int], float]) -> list[list[float]]:
    return [[i, j, values[(i, j)]] for i, j in sorted(values)]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed-json", required=True)
    parser.add_argument("--save-json", required=True)
    parser.add_argument(
        "--pairs",
        required=True,
        type=parse_pairs,
        help="Semicolon-separated q,b2 pairs to add as zero-start F/G bumps.",
    )
    parser.add_argument("--note", default="")
    args = parser.parse_args()

    data = load_data(args.seed_json)
    old_q_centers = as_float_list(data, "interior_bump_q_centers")
    old_b2_centers = as_float_list(data, "interior_bump_b2_centers")
    if not old_q_centers or not old_b2_centers:
        raise SystemExit("seed has no interior bump centers")

    new_q_centers = merge_centers(old_q_centers, (q for q, _b2 in args.pairs))
    new_b2_centers = merge_centers(old_b2_centers, (b2 for _q, b2 in args.pairs))
    q_index = index_map(new_q_centers)
    b2_index = index_map(new_b2_centers)
    pair_indices = [(q_index[float_key(q)], b2_index[float_key(b2)]) for q, b2 in args.pairs]

    out = copy.deepcopy(data)
    out["interior_bump_q_centers"] = new_q_centers
    out["interior_bump_b2_centers"] = new_b2_centers
    for key in ("f_interior_bump_coeffs", "g_interior_bump_coeffs"):
        values = remap_old_coeffs(
            coeffs(data, key),
            old_q_centers,
            old_b2_centers,
            q_index,
            b2_index,
        )
        for pair in pair_indices:
            values.setdefault(pair, 0.0)
        out[key] = serialize_coeffs(values)

    out["evidence"] = {
        "status": "sparse_expanded_tail_flat_interior_bump_seed",
        "source": args.seed_json,
        "old_q_centers": old_q_centers,
        "old_b2_centers": old_b2_centers,
        "new_q_centers": new_q_centers,
        "new_b2_centers": new_b2_centers,
        "added_pairs": args.pairs,
        "note": args.note,
    }

    with open(args.save_json, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print(f"saved sparse bump seed: {args.save_json}")
    print(f"q_centers: {old_q_centers} -> {new_q_centers}")
    print(f"b2_centers: {old_b2_centers} -> {new_b2_centers}")
    print(f"added_pairs={len(args.pairs)}")


if __name__ == "__main__":
    main()
