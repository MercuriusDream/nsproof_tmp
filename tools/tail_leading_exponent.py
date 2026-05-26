#!/usr/bin/env python3
"""Report the first nonzero tail exponent in a projected profile.

The current admissible story expects the conical trace at q^0, forbids q^1,
and pins the first forced fractional correction at q^p.  This diagnostic makes
it explicit if an ordinary q^2 analytic trace appears before q^p.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from validators.tail_formal_recurrence import validate_tail_formal_recurrence


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", required=True)
    parser.add_argument("--tol", type=float, default=1e-12)
    parser.add_argument("--out", default="")
    args = parser.parse_args()

    report = validate_tail_formal_recurrence(
        args.profile,
        q2_policy="warn",
        q2_tol=args.tol,
    )
    entries = [
        {
            "name": "ordinary_q1",
            "exponent": 1.0,
            "max_abs": max(report.q1_f_max, report.q1_g_max),
            "status": "forbidden",
        },
        {
            "name": "ordinary_q2",
            "exponent": 2.0,
            "max_abs": max(report.q2_f_trace_max, report.q2_g_trace_max),
            "status": "unvalidated",
        },
        {
            "name": "forced_qp",
            "exponent": report.p,
            "max_abs": 0.0 if report.forced_qp_coeff_error <= args.tol else report.forced_qp_coeff_error,
            "status": "fixed_formal_trace",
        },
    ]
    nonzero = [entry for entry in entries if float(entry["max_abs"]) > args.tol]
    nonzero.sort(key=lambda entry: float(entry["exponent"]))
    if not nonzero:
        leading = None
        status = "NO_NONZERO_AUDITED_TAIL_CORRECTION"
    else:
        leading = nonzero[0]
        if leading["name"] == "ordinary_q1":
            status = "FORBIDDEN_Q1_IS_LEADING"
        elif leading["name"] == "ordinary_q2" and 2.0 < report.p:
            status = "FIRST_NONZERO_TRACE_IS_UNVALIDATED_Q2_BEFORE_FORCED_QP"
        elif leading["name"] == "ordinary_q2":
            status = "UNVALIDATED_Q2_TRACE_PRESENT"
        else:
            status = "LEADING_AUDITED_TRACE_IS_FORCED_QP"
    result = {
        "profile": report.path,
        "gamma": report.gamma,
        "B": report.B,
        "p": report.p,
        "tolerance": args.tol,
        "entries": entries,
        "leading_nonzero": leading,
        "status": status,
    }
    print(f"profile={report.path}")
    print(f"gamma={report.gamma:.15g} B={report.B:.15g} p={report.p:.15g}")
    for entry in entries:
        print(
            f"{entry['name']} exponent={float(entry['exponent']):.12g} "
            f"max_abs={float(entry['max_abs']):.12e} status={entry['status']}"
        )
    print(f"leading_nonzero={leading}")
    print(f"status={status}")
    if args.out:
        out_dir = os.path.dirname(args.out)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump(result, fh, indent=2, sort_keys=True)
            fh.write("\n")


if __name__ == "__main__":
    main()
