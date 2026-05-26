"""Formal tail recurrence gates for transseries-Chebyshev profiles.

This module is intentionally conservative.  It certifies only the recurrence
facts currently derived in the repo: the conical trace, ordinary q^1 exclusion,
and the first forced q^(1/gamma) coefficient.  It also audits the ordinary q^2
analytic trace and marks it unvalidated by default, because the proof program
has not yet derived a recurrence allowing that channel.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from fractions import Fraction
from typing import Any

from profile_project_cheb import cheb_eval_tensor
from validators.tail_transseries import forced_qp_expected_coeffs


@dataclass(frozen=True)
class TailFormalRecurrenceReport:
    path: str
    gamma: float
    B: float
    p: float
    q1_f_max: float
    q1_g_max: float
    forced_qp_coeff_error: float
    q2_f_trace_max: float
    q2_g_trace_max: float
    q2_policy: str
    q2_ok: bool
    all_ok: bool
    status: str


def parse_fraction_or_float(raw: str) -> float:
    text = raw.strip()
    if "/" in text:
        return float(Fraction(text))
    return float(text)


def load_projection(path: str) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    if data.get("format") != "transseries_cheb_projection_v1":
        raise ValueError(f"{path} is not a transseries_cheb_projection_v1 file")
    return data


def coeff_list(value: Any) -> list[float]:
    if not isinstance(value, list):
        return []
    return [float(item) for item in value]


def coeff_error(actual: list[float], expected: tuple[float, ...]) -> float:
    width = max(len(actual), len(expected))
    error = 0.0
    for index in range(width):
        a = actual[index] if index < len(actual) else 0.0
        e = expected[index] if index < len(expected) else 0.0
        error = max(error, abs(a - e))
    return error


def find_q0_patches(data: dict[str, Any], block: str) -> list[dict[str, Any]]:
    patches = data["blocks"][block]
    out: list[dict[str, Any]] = []
    for patch in patches:
        q0, _q1 = patch["q_interval"]
        if abs(float(q0)) <= 1e-15:
            out.append(patch)
    return out


def patch_interval(patch: dict[str, Any]) -> tuple[float, float, float, float]:
    q0, q1 = patch["q_interval"]
    x0, x1 = patch["x_interval"]
    return float(q0), float(q1), float(x0), float(x1)


def trace_max_at_q0(data: dict[str, Any], block: str, samples_per_patch: int) -> float:
    worst = 0.0
    for patch in find_q0_patches(data, block):
        q0, q1, x0, x1 = patch_interval(patch)
        del q1
        count = max(samples_per_patch, 2)
        for index in range(count):
            x = x0 + (x1 - x0) * index / (count - 1)
            value = cheb_eval_tensor(patch["coeffs"], q0, x, q0, patch_interval(patch)[1], x0, x1)
            worst = max(worst, abs(value))
    return worst


def validate_tail_formal_recurrence(
    path: str,
    gamma: float | None = None,
    B: float | None = None,
    q1_tol: float = 1e-14,
    forced_tol: float = 1e-12,
    q2_tol: float = 1e-12,
    q2_policy: str = "zero",
    samples_per_patch: int = 9,
) -> TailFormalRecurrenceReport:
    if q2_policy not in ("zero", "warn", "allow"):
        raise ValueError("q2_policy must be zero, warn, or allow")
    data = load_projection(path)
    gamma_value = float(data["gamma"]) if gamma is None else gamma
    B_value = float(data["B"]) if B is None else B
    p = float(data["p"])
    tail = data["tail_constraints"]
    q1 = tail["ordinary_q1"]
    forced = tail["forced_qp"]
    q1_f = float(q1.get("F_max_abs", float("inf")))
    q1_g = float(q1.get("G_max_abs", float("inf")))
    expected_f, expected_g = forced_qp_expected_coeffs(gamma_value, B_value)
    forced_error = max(
        coeff_error(coeff_list(forced.get("F_trace_x_coeffs", [])), expected_f),
        coeff_error(coeff_list(forced.get("G_trace_x_coeffs", [])), expected_g),
    )
    q2_f = trace_max_at_q0(data, "F_an", samples_per_patch)
    q2_g = trace_max_at_q0(data, "G_an", samples_per_patch)
    if q2_policy == "allow":
        q2_ok = True
    elif q2_policy == "warn":
        q2_ok = True
    else:
        q2_ok = q2_f <= q2_tol and q2_g <= q2_tol
    basic_ok = q1_f <= q1_tol and q1_g <= q1_tol and forced_error <= forced_tol
    all_ok = basic_ok and q2_ok
    if not basic_ok:
        status = "TAIL_RECURRENCE_BASIC_FAILURE"
    elif q2_policy == "zero" and not q2_ok:
        status = "UNVALIDATED_Q2_TRACE_PRESENT"
    elif q2_policy == "warn" and (q2_f > q2_tol or q2_g > q2_tol):
        status = "WARNING_UNVALIDATED_Q2_TRACE_PRESENT"
    else:
        status = "TAIL_FORMAL_RECURRENCE_GATE_OK_NOT_INTERVAL"
    return TailFormalRecurrenceReport(
        path=path,
        gamma=gamma_value,
        B=B_value,
        p=p,
        q1_f_max=q1_f,
        q1_g_max=q1_g,
        forced_qp_coeff_error=forced_error,
        q2_f_trace_max=q2_f,
        q2_g_trace_max=q2_g,
        q2_policy=q2_policy,
        q2_ok=q2_ok,
        all_ok=all_ok,
        status=status,
    )
