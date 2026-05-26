#!/usr/bin/env python3
"""Filter selected integer q-tail coefficients from a profile seed.

This is a diagnostic projection, not a solver.  It preserves the q=0 trace by
adding monomial counterterms at the requested positive q-orders so that the
total Taylor coefficient of F(q,b) and G(q,b) at those orders vanishes.

The purpose is to test whether finite-box residual improvements were bought by
forbidden integer tail coefficients.
"""

from __future__ import annotations

import argparse
import json

from profile_tail_series import expand_coefficients


def parse_orders(raw: str) -> list[int]:
    orders = [int(item) for item in raw.split(",") if item.strip()]
    if any(order <= 0 for order in orders):
        raise ValueError("tail-filter orders must be positive")
    return sorted(set(orders))


def coeff_key(kind: str) -> str:
    return "f_coeffs" if kind == "F" else "g_coeffs"


def apply_counterterms(
    data: dict[str, object],
    kind: str,
    orders: list[int],
    max_order: int,
) -> list[tuple[int, int, float]]:
    key = coeff_key(kind)
    series = expand_coefficients(data, key, max_order)
    existing: dict[tuple[int, int], float] = {}
    for i, j, value in data.get(key, []):  # type: ignore[union-attr]
        existing[(int(i), int(j))] = existing.get((int(i), int(j)), 0.0) + float(value)

    added: list[tuple[int, int, float]] = []
    for order in orders:
        for b_power, value in sorted(series.get(order, {}).items()):
            if b_power % 2:
                raise ValueError(f"unexpected odd b power {b_power}")
            j = b_power // 2
            delta = -value
            existing[(order, j)] = existing.get((order, j), 0.0) + delta
            added.append((order, j, delta))

    data[key] = [
        [i, j, value]
        for (i, j), value in sorted(existing.items())
        if abs(value) > 1e-14
    ]
    return added


def load_data(path: str) -> dict[str, object]:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed-json", required=True)
    parser.add_argument("--save-json", required=True)
    parser.add_argument("--orders", default="1")
    args = parser.parse_args()

    orders = parse_orders(args.orders)
    max_order = max(orders)
    data = load_data(args.seed_json)
    additions = {
        "F": apply_counterterms(data, "F", orders, max_order),
        "G": apply_counterterms(data, "G", orders, max_order),
    }
    data["tail_filter"] = {
        "source": args.seed_json,
        "zeroed_integer_q_orders": orders,
        "method": "added monomial counterterms to cancel total q-series coefficients",
        "added_counterterms": additions,
    }
    evidence = data.setdefault("evidence", {})
    if isinstance(evidence, dict):
        evidence["status"] = "diagnostic_tail_filtered_seed"

    with open(args.save_json, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print(f"saved filtered seed: {args.save_json}")
    for kind, rows in additions.items():
        print(f"{kind} counterterms={len(rows)}")


if __name__ == "__main__":
    main()
