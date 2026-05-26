#!/usr/bin/env python3
"""Inspect the compactified profile trace at the far boundary q=0."""

from __future__ import annotations

import argparse

from compactified_profile import grid, load_seed_json_profile


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed-json", required=True)
    parser.add_argument("--b-min", type=float, default=-0.95)
    parser.add_argument("--b-max", type=float, default=0.95)
    parser.add_argument("--n-b", type=int, default=21)
    parser.add_argument("--q", type=float, default=0.0)
    args = parser.parse_args()

    gamma, B, profile = load_seed_json_profile(args.seed_json)
    max_f = (0.0, 0.0)
    max_g = (0.0, 0.0)
    print(f"seed={args.seed_json}")
    print(f"gamma={gamma} B={B} q={args.q:.6e}")
    print("b,F,F_minus_core,G,G_minus_core")
    for b in grid(args.b_min, args.b_max, args.n_b):
        f_value = profile.F_total(args.q, b)
        g_value = profile.G_total(args.q, b)
        f_delta = f_value - 0.5
        g_delta = g_value - B
        if abs(f_delta) > abs(max_f[1]):
            max_f = (b, f_delta)
        if abs(g_delta) > abs(max_g[1]):
            max_g = (b, g_delta)
        print(
            f"{b:.12e},{f_value:.12e},{f_delta:.12e},"
            f"{g_value:.12e},{g_delta:.12e}"
        )
    print(
        f"max_abs_F_minus_core b={max_f[0]:.12e} value={max_f[1]:.12e}"
    )
    print(
        f"max_abs_G_minus_core b={max_g[0]:.12e} value={max_g[1]:.12e}"
    )


if __name__ == "__main__":
    main()
