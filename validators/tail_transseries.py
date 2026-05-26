"""Structural checks for transseries-Chebyshev profile projections.

These checks are deliberately weaker than the final proof obligations.  They
verify that a projected profile is in the intended formal class: exact leading
trace metadata, no ordinary q^1 channel, a lifted q^(1/gamma) block, and small
sampling reconstruction error.  They do not validate the formal tail recurrence
or provide interval arithmetic bounds.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TailProjectionReport:
    path: str
    gamma: float
    B: float
    p: float
    in_wedge: bool
    q1_f_max: float
    q1_g_max: float
    forced_qp_lifted: bool
    forced_qp_coeff_error: float
    forced_qp_expected_F: tuple[float, ...]
    forced_qp_expected_G: tuple[float, ...]
    projection_f_error: float
    projection_g_error: float
    origin_f_error: float
    origin_g_error: float
    tail_ok: bool
    projection_ok: bool
    origin_ok: bool

    @property
    def all_ok(self) -> bool:
        return self.tail_ok and self.projection_ok and self.origin_ok


def _as_float(data: dict[str, Any], key: str) -> float:
    value = data.get(key)
    if not isinstance(value, (float, int)):
        raise ValueError(f"missing numeric {key!r}")
    return float(value)


def forced_qp_expected_coeffs(gamma: float, B: float) -> tuple[tuple[float, ...], tuple[float, ...]]:
    """Formal first forced q^(1/gamma) trace in powers of x=b^2.

    The formulas are the leading recurrence for the conical core
    F_0=1/2, G_0=B.  They are finite in the open wedge used here, but the F
    denominator degenerates at the endpoint gamma=2/5, so callers should keep
    the usual strict wedge check.
    """
    gamma2 = gamma * gamma
    gamma3 = gamma2 * gamma
    f_denom_0 = 4.0 * (35.0 * gamma3 + 11.0 * gamma2 - 20.0 * gamma + 4.0)
    f_denom_2 = 4.0 * gamma * (7.0 * gamma2 + 5.0 * gamma - 2.0)
    if abs(f_denom_0) < 1e-15 or abs(f_denom_2) < 1e-15 or abs(gamma) < 1e-15:
        raise ValueError("forced q^p recurrence denominator is singular at this gamma")
    f0 = (
        28.0 * B * B * gamma3
        + 20.0 * B * B * gamma2
        - 8.0 * B * B * gamma
        + 25.0 * gamma3
        + 30.0 * gamma2
        - 27.0 * gamma
        + 4.0
    ) / f_denom_0
    f2 = (-15.0 * gamma2 - 2.0 * gamma + 1.0) / f_denom_2
    g0 = B * (1.0 - 2.0 * gamma) / (2.0 * gamma)
    g2 = -B / (2.0 * gamma)
    return (f0, f2), (g0, g2)


def _coeff_list(value: Any) -> list[float]:
    if not isinstance(value, list):
        return []
    return [float(item) for item in value]


def _coeff_error(actual: list[float], expected: tuple[float, ...]) -> float:
    width = max(len(actual), len(expected))
    error = 0.0
    for index in range(width):
        actual_value = actual[index] if index < len(actual) else 0.0
        expected_value = expected[index] if index < len(expected) else 0.0
        error = max(error, abs(actual_value - expected_value))
    return error


def load_projection(path: str) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    if data.get("format") != "transseries_cheb_projection_v1":
        raise ValueError(f"{path} is not a transseries_cheb_projection_v1 file")
    return data


def validate_projection(
    path: str,
    q1_tol: float = 1e-14,
    forced_tol: float = 1e-8,
    projection_tol: float = 1e-5,
    origin_tol: float = 1e-3,
) -> TailProjectionReport:
    data = load_projection(path)
    gamma = _as_float(data, "gamma")
    B = _as_float(data, "B")
    p = _as_float(data, "p")
    tail = data.get("tail_constraints", {})
    if not isinstance(tail, dict):
        raise ValueError("tail_constraints must be an object")
    q1 = tail.get("ordinary_q1", {})
    forced = tail.get("forced_qp", {})
    if not isinstance(q1, dict) or not isinstance(forced, dict):
        raise ValueError("tail_constraints.ordinary_q1 and forced_qp are required")
    checks = data.get("projection_checks", {})
    blocks = data.get("blocks", {})
    if not isinstance(checks, dict) or not isinstance(blocks, dict):
        raise ValueError("projection_checks and blocks are required")
    f_origin = blocks.get("F_origin_taylor", {})
    g_origin = blocks.get("G_origin_taylor", {})
    if not isinstance(f_origin, dict) or not isinstance(g_origin, dict):
        raise ValueError("origin Taylor blocks are required")

    q1_f = float(q1.get("F_max_abs", float("inf")))
    q1_g = float(q1.get("G_max_abs", float("inf")))
    forced_lifted = bool(forced.get("lifted_from_vanishing_edge", False))
    expected_f, expected_g = forced_qp_expected_coeffs(gamma, B)
    actual_f = _coeff_list(forced.get("F_trace_x_coeffs", []))
    actual_g = _coeff_list(forced.get("G_trace_x_coeffs", []))
    forced_error = max(_coeff_error(actual_f, expected_f), _coeff_error(actual_g, expected_g))
    f_error = float(checks.get("max_F_reconstruction_error", float("inf")))
    g_error = float(checks.get("max_G_reconstruction_error", float("inf")))
    origin_f = float(f_origin.get("max_fit_error", float("inf")))
    origin_g = float(g_origin.get("max_fit_error", float("inf")))

    in_wedge = 0.4 < gamma < 0.5
    forced_ok = forced_lifted and forced_error <= forced_tol
    tail_ok = in_wedge and q1_f <= q1_tol and q1_g <= q1_tol and forced_ok
    projection_ok = f_error <= projection_tol and g_error <= projection_tol
    origin_ok = origin_f <= origin_tol and origin_g <= origin_tol
    return TailProjectionReport(
        path=path,
        gamma=gamma,
        B=B,
        p=p,
        in_wedge=in_wedge,
        q1_f_max=q1_f,
        q1_g_max=q1_g,
        forced_qp_lifted=forced_lifted,
        forced_qp_coeff_error=forced_error,
        forced_qp_expected_F=expected_f,
        forced_qp_expected_G=expected_g,
        projection_f_error=f_error,
        projection_g_error=g_error,
        origin_f_error=origin_f,
        origin_g_error=origin_g,
        tail_ok=tail_ok,
        projection_ok=projection_ok,
        origin_ok=origin_ok,
    )
