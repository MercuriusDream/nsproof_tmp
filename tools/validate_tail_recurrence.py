#!/usr/bin/env python3
"""Validate currently derived formal tail recurrence gates.

This is a conservative non-interval gate.  It validates q0/q1 and the first
forced q^(1/gamma) trace, then audits the ordinary q^2 analytic trace.  By
default, a nonzero q^2 trace fails because that channel has not yet been
validated by a formal recurrence theorem.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from validators.tail_formal_recurrence import (
    parse_fraction_or_float,
    validate_tail_formal_recurrence,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", required=True)
    parser.add_argument("--gamma", default="")
    parser.add_argument("--B", default="")
    parser.add_argument("--orders", default="0,p,2")
    parser.add_argument("--q1-tol", type=float, default=1e-14)
    parser.add_argument("--forced-tol", type=float, default=1e-12)
    parser.add_argument("--q2-tol", type=float, default=1e-12)
    parser.add_argument("--q2-policy", choices=("zero", "warn", "allow"), default="zero")
    parser.add_argument("--samples-per-patch", type=int, default=9)
    parser.add_argument("--out", default="")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    gamma = parse_fraction_or_float(args.gamma) if args.gamma else None
    B = parse_fraction_or_float(args.B) if args.B else None
    report = validate_tail_formal_recurrence(
        args.profile,
        gamma=gamma,
        B=B,
        q1_tol=args.q1_tol,
        forced_tol=args.forced_tol,
        q2_tol=args.q2_tol,
        q2_policy=args.q2_policy,
        samples_per_patch=args.samples_per_patch,
    )
    result = {
        "profile": report.path,
        "gamma": report.gamma,
        "B": report.B,
        "p": report.p,
        "orders_requested": args.orders,
        "ordinary_q1_F_max": report.q1_f_max,
        "ordinary_q1_G_max": report.q1_g_max,
        "forced_qp_coeff_error": report.forced_qp_coeff_error,
        "ordinary_q2_F_trace_max": report.q2_f_trace_max,
        "ordinary_q2_G_trace_max": report.q2_g_trace_max,
        "q2_policy": report.q2_policy,
        "q2_ok": report.q2_ok,
        "all_ok": report.all_ok,
        "status": report.status,
        "note": (
            "Nonzero q2 means the analytic q^2 trace is being used. "
            "It must be proved legal by a later recurrence theorem or removed "
            "from the proof ansatz."
        ),
    }
    print(f"profile={report.path}")
    print(f"gamma={report.gamma:.15g} B={report.B:.15g} p={report.p:.15g}")
    print(f"orders_requested={args.orders}")
    print(f"ordinary_q1_F_max={report.q1_f_max:.12e}")
    print(f"ordinary_q1_G_max={report.q1_g_max:.12e}")
    print(f"forced_qp_coeff_error={report.forced_qp_coeff_error:.12e}")
    print(f"ordinary_q2_F_trace_max={report.q2_f_trace_max:.12e}")
    print(f"ordinary_q2_G_trace_max={report.q2_g_trace_max:.12e}")
    print(f"q2_policy={report.q2_policy}")
    print(f"q2_ok={report.q2_ok}")
    print(f"all_ok={report.all_ok}")
    print(f"status={report.status}")
    if args.out:
        out_dir = os.path.dirname(args.out)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump(result, fh, indent=2, sort_keys=True)
            fh.write("\n")
    if args.strict and not report.all_ok:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
