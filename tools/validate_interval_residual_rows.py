#!/usr/bin/env python3
"""Emit a sampled residual-row interval certificate ledger."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from validators.interval_residual_rows import (  # noqa: E402
    build_interval_residual_row_ledger,
    save_json,
    self_test,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exact-residual-audit", default="")
    parser.add_argument("--row-cache", default="")
    parser.add_argument("--out", default="certs/profile/interval_residual_rows.json")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        result = self_test()
        print(f"self_test_pass={result['pass']}")
        print(f"manufactured_case_count={result['manufactured_case_count']}")
        print(f"reversed_interval_rejected={result['reversed_interval_rejected']}")
        print(f"width_max={result['interval_widths']['max']:.17g}")
        return 0 if result["pass"] else 1

    if not args.exact_residual_audit and not args.row_cache:
        parser.error("supply --exact-residual-audit and/or --row-cache, or use --self-test")

    cert = build_interval_residual_row_ledger(
        exact_residual_audit=args.exact_residual_audit,
        row_cache=args.row_cache,
        command=sys.argv,
    )
    save_json(args.out, cert)
    print(f"pass={cert['pass']} status={cert['status']}")
    print(f"row_count={cert['row_count']}")
    print(f"interval_max_abs_upper_bound={cert['interval_max_abs_upper_bound']}")
    print(f"interval_width_max={cert['interval_widths']['max']}")
    print(f"saved={args.out}")
    print(f"failure_reason={cert['failure_reason']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
