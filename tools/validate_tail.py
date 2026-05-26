#!/usr/bin/env python3
"""Check structural tail constraints of a transseries projection.

This is the first gate after `tools/profile_project_cheb.py`.  It is not the
final interval recurrence validator: it verifies that the projected data live in
the intended formal class and makes origin-regularity failures explicit.
"""

from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from validators.tail_transseries import validate_projection


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", required=True)
    parser.add_argument("--q1-tol", type=float, default=1e-14)
    parser.add_argument("--forced-tol", type=float, default=1e-8)
    parser.add_argument("--projection-tol", type=float, default=1e-5)
    parser.add_argument("--origin-tol", type=float, default=1e-3)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    report = validate_projection(
        args.profile,
        q1_tol=args.q1_tol,
        forced_tol=args.forced_tol,
        projection_tol=args.projection_tol,
        origin_tol=args.origin_tol,
    )
    print(f"profile={report.path}")
    print(f"gamma={report.gamma:.15g} B={report.B:.15g} p={report.p:.15g}")
    print(f"in_wedge={report.in_wedge}")
    print(f"ordinary_q1_F_max={report.q1_f_max:.12e}")
    print(f"ordinary_q1_G_max={report.q1_g_max:.12e}")
    print(f"forced_qp_lifted={report.forced_qp_lifted}")
    print(f"forced_qp_expected_F={list(report.forced_qp_expected_F)}")
    print(f"forced_qp_expected_G={list(report.forced_qp_expected_G)}")
    print(f"forced_qp_coeff_error={report.forced_qp_coeff_error:.12e}")
    print(f"projection_F_error={report.projection_f_error:.12e}")
    print(f"projection_G_error={report.projection_g_error:.12e}")
    print(f"origin_F_fit_error={report.origin_f_error:.12e}")
    print(f"origin_G_fit_error={report.origin_g_error:.12e}")
    print(f"tail_structural_ok={report.tail_ok}")
    print(f"projection_sampling_ok={report.projection_ok}")
    print(f"origin_taylor_ok={report.origin_ok}")
    print(f"all_ok={report.all_ok}")
    print("status=STRUCTURAL_CHECK_NOT_INTERVAL_VALIDATION")
    if args.strict and not report.all_ok:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
