"""Exact rational tail algebra for the fixed gamma=9/20, B=1 branch.

This module proves only the finite algebraic subclaims used by the current
tail ledgers: the strict gamma wedge, p=1/gamma, and the first forced q^p trace
coefficients.  It deliberately does not certify the infinite tail recurrence.
"""

from __future__ import annotations

import argparse
import json
from fractions import Fraction
from typing import Any


GAMMA = Fraction(9, 20)
B_VALUE = Fraction(1, 1)
P_VALUE = Fraction(1, 1) / GAMMA
DEFAULT_TOLERANCE = 1e-12


def _forced_qp_trace() -> dict[str, Fraction]:
    gamma = GAMMA
    gamma2 = gamma * gamma
    gamma3 = gamma2 * gamma
    B = B_VALUE
    f_denom_0 = 4 * (35 * gamma3 + 11 * gamma2 - 20 * gamma + 4)
    f_denom_2 = 4 * gamma * (7 * gamma2 + 5 * gamma - 2)
    f0 = (
        28 * B * B * gamma3
        + 20 * B * B * gamma2
        - 8 * B * B * gamma
        + 25 * gamma3
        + 30 * gamma2
        - 27 * gamma
        + 4
    ) / f_denom_0
    f2 = (-15 * gamma2 - 2 * gamma + 1) / f_denom_2
    g0 = B * (1 - 2 * gamma) / (2 * gamma)
    g2 = -B / (2 * gamma)
    return {
        "F_x0": f0,
        "F_x1": f2,
        "G_x0": g0,
        "G_x1": g2,
    }


def exact_tail_subclaims() -> dict[str, Any]:
    """Return JSON-serializable exact subclaims for the fixed branch."""
    forced = _forced_qp_trace()
    return {
        "fixed_branch_gamma_B": True,
        "gamma": str(GAMMA),
        "B": str(B_VALUE),
        "p": str(P_VALUE),
        "gamma_in_open_wedge_2_5_1_2": bool(Fraction(2, 5) < GAMMA < Fraction(1, 2)),
        "inequalities": {
            "2/5 < gamma": bool(Fraction(2, 5) < GAMMA),
            "gamma < 1/2": bool(GAMMA < Fraction(1, 2)),
        },
        "forced_qp_trace_exact_rational": {key: str(value) for key, value in forced.items()},
        "forced_qp_trace_decimal": {key: float(value) for key, value in forced.items()},
        "note": (
            "These are exact algebraic subclaims for the fixed branch only. "
            "They do not certify the infinite tail recurrence or the profile."
        ),
    }


def _as_float(data: dict[str, Any], key: str) -> float | None:
    value = data.get(key)
    if isinstance(value, (float, int)):
        return float(value)
    return None


def _forced_metadata(data: dict[str, Any]) -> dict[str, Any] | None:
    if data.get("format") == "twochart_profile_projection_v1":
        forced = (
            data.get("preserved_metadata", {})
            .get("tail_constraints", {})
            .get("forced_qp")
        )
    else:
        forced = data.get("tail_constraints", {}).get("forced_qp")
    return forced if isinstance(forced, dict) else None


def _tail_metadata(data: dict[str, Any]) -> dict[str, Any]:
    tail = data.get("tail_legality", {})
    requested = data.get("requested_options", {})
    if not isinstance(tail, dict):
        tail = {}
    if not isinstance(requested, dict):
        requested = {}
    return {
        "format": data.get("format"),
        "gamma": data.get("gamma"),
        "B": data.get("B"),
        "p": data.get("p"),
        "tail_legality_status": tail.get("status"),
        "floating_tail_gate_all_ok": tail.get("all_ok"),
        "forced_qp_coeff_error": tail.get("forced_qp_coeff_error"),
        "q2_policy": tail.get("q2_policy") or requested.get("q2_policy"),
        "q2_ok": tail.get("q2_ok"),
    }


def _compare_scalar(name: str, actual: float | None, expected: Fraction, tolerance: float) -> dict[str, Any]:
    if actual is None:
        return {
            "name": name,
            "actual": None,
            "expected": str(expected),
            "abs_error": None,
            "ok": False,
            "failure_reason": f"missing numeric {name}",
        }
    error = abs(actual - float(expected))
    return {
        "name": name,
        "actual": actual,
        "expected": str(expected),
        "expected_decimal": float(expected),
        "abs_error": error,
        "tolerance": tolerance,
        "ok": error <= tolerance,
    }


def _coerce_coeff_list(value: Any) -> list[float] | None:
    if not isinstance(value, list):
        return None
    try:
        return [float(item) for item in value]
    except (TypeError, ValueError):
        return None


def _compare_coeffs(name: str, actual_raw: Any, expected: list[Fraction], tolerance: float) -> dict[str, Any]:
    actual = _coerce_coeff_list(actual_raw)
    if actual is None:
        return {
            "name": name,
            "actual": None,
            "expected": [str(item) for item in expected],
            "max_abs_error": None,
            "ok": False,
            "failure_reason": f"missing numeric coefficient list {name}",
        }
    width = max(len(actual), len(expected))
    per_index = []
    max_error = 0.0
    for index in range(width):
        actual_value = actual[index] if index < len(actual) else 0.0
        expected_value = expected[index] if index < len(expected) else Fraction(0, 1)
        error = abs(actual_value - float(expected_value))
        max_error = max(max_error, error)
        per_index.append(
            {
                "index": index,
                "actual": actual_value,
                "expected": str(expected_value),
                "expected_decimal": float(expected_value),
                "abs_error": error,
                "ok": error <= tolerance,
            }
        )
    return {
        "name": name,
        "actual": actual,
        "expected": [str(item) for item in expected],
        "max_abs_error": max_error,
        "tolerance": tolerance,
        "per_index": per_index,
        "ok": max_error <= tolerance,
    }


def floating_profile_link(
    profile_data: dict[str, Any] | None,
    *,
    profile_path: str | None = None,
    tolerance: float = DEFAULT_TOLERANCE,
) -> dict[str, Any]:
    """Compare profile metadata and forced trace coefficients to exact values."""
    if profile_data is None:
        return {
            "profile": profile_path,
            "checked": False,
            "pass": False,
            "tolerance": tolerance,
            "metadata": None,
            "comparisons": [],
            "failure_reason": "no profile supplied",
        }
    forced = _forced_qp_trace()
    forced_meta = _forced_metadata(profile_data)
    comparisons = [
        _compare_scalar("gamma", _as_float(profile_data, "gamma"), GAMMA, tolerance),
        _compare_scalar("B", _as_float(profile_data, "B"), B_VALUE, tolerance),
        _compare_scalar("p", _as_float(profile_data, "p"), P_VALUE, tolerance),
    ]
    if forced_meta is None:
        comparisons.append(
            {
                "name": "forced_qp",
                "ok": False,
                "failure_reason": "missing forced_qp metadata",
            }
        )
    else:
        comparisons.extend(
            [
                _compare_coeffs(
                    "forced_qp.F_trace_x_coeffs",
                    forced_meta.get("F_trace_x_coeffs"),
                    [forced["F_x0"], forced["F_x1"]],
                    tolerance,
                ),
                _compare_coeffs(
                    "forced_qp.G_trace_x_coeffs",
                    forced_meta.get("G_trace_x_coeffs"),
                    [forced["G_x0"], forced["G_x1"]],
                    tolerance,
                ),
            ]
        )
    ok = all(bool(item.get("ok")) for item in comparisons)
    return {
        "profile": profile_path,
        "checked": True,
        "pass": ok,
        "tolerance": tolerance,
        "metadata": _tail_metadata(profile_data),
        "forced_qp_metadata": forced_meta,
        "comparisons": comparisons,
        "failure_reason": None if ok else "profile metadata or forced q^p coefficients differ from exact fixed-branch values",
    }


def exact_tail_algebra_report(
    profile_data: dict[str, Any] | None = None,
    *,
    profile_path: str | None = None,
    tolerance: float = DEFAULT_TOLERANCE,
) -> dict[str, Any]:
    """Return a JSON-serializable exact-tail subclaim report."""
    exact = exact_tail_subclaims()
    exact_ok = bool(exact["gamma_in_open_wedge_2_5_1_2"] and exact["fixed_branch_gamma_B"])
    link = floating_profile_link(profile_data, profile_path=profile_path, tolerance=tolerance)
    return {
        "pass": exact_ok and (not link["checked"] or link["pass"]),
        "claim_scope": "fixed_branch_exact_algebra_only",
        "exact_subclaims": exact,
        "floating_profile_link": link,
        "blockers_for_full_tail_certificate": [
            "does not prove the infinite tail recurrence",
            "does not provide a directed-rounding interval recurrence",
            "does not provide an infinite tail remainder majorant",
            "does not prove exponent semigroup closure",
        ],
    }


def load_json(path: str) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", help="optional profile JSON to link against exact subclaims")
    parser.add_argument("--tolerance", type=float, default=DEFAULT_TOLERANCE)
    args = parser.parse_args()

    profile_data = load_json(args.profile) if args.profile else None
    report = exact_tail_algebra_report(
        profile_data,
        profile_path=args.profile,
        tolerance=args.tolerance,
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
