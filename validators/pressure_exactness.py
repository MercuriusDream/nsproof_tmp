#!/usr/bin/env python3
"""Pressure-reconstruction ledger helpers.

This module records the exact obligations needed to turn a validated
pressure-eliminated axisymmetric-with-swirl profile into a velocity-pressure
profile.  It intentionally contains no interval backend and never returns a
passing validation result.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from validators.exact_profile_residual import stable_json_hash


PRESSURE_RECONSTRUCTION_STATEMENT = """
Given the two-chart profile ansatz

  psi = r^2 z q^p F(q,x),  Gamma = r^2 q^p G(q,x),
  q = (1 + r^2 + z^2)^(-1/2),  x = z^2/(r^2 + z^2),

build the axisymmetric-with-swirl velocity

  U = u^r e_r + u^theta e_theta + u^z e_z,
  u^r = -partial_z psi / r,
  u^z =  partial_r psi / r,
  u^theta = Gamma / r.

Let R^r, R^theta, R^z be the non-pressure self-similar momentum residual
computed from this U in cylindrical coordinates.  A pressure reconstruction
certificate must validate, with outward-rounded interval bounds, that

  R^theta = 0,
  partial_z R^r - partial_r R^z = 0,
  partial_r P + R^r = 0,
  partial_z P + R^z = 0,

on every tail and origin chart, that the chart pressure potentials agree on
their overlap up to one fixed additive constant, and that the reconstructed
pressure has the required tail class.

The pressure-eliminated profile equations provide the formal identities

  r R^theta = E_Gamma,
  E_psi = -r^3 (partial_z R^r - partial_r R^z),

but those identities become a pressure certificate only after the profile
Newton-Kantorovich gate passes and the one-form, chart-matching, and pressure
tail bounds are interval validated.
""".strip()


PRESSURE_OBLIGATIONS: tuple[dict[str, Any], ...] = (
    {
        "obligation_id": "velocity_from_streamfunction_swirl",
        "statement": (
            "Build U from psi/Gamma using u^r=-partial_z psi/r, "
            "u^z=partial_r psi/r, and u^theta=Gamma/r on both charts."
        ),
        "required_artifact": "interval Taylor-jet evaluator for psi, Gamma, and U",
        "validated": False,
        "status": "formula-recorded-no-interval-bounds",
    },
    {
        "obligation_id": "theta_residual_zero",
        "statement": "Validate R^theta=0, equivalently r R^theta=E_Gamma=0.",
        "required_artifact": "outward-rounded interval bound for R^theta",
        "validated": False,
        "status": "missing-interval-bound",
    },
    {
        "obligation_id": "one_form_closedness",
        "statement": (
            "Validate closedness of the pressure one-form: "
            "partial_z R^r - partial_r R^z = 0."
        ),
        "required_artifact": "outward-rounded interval bound for one-form curl",
        "validated": False,
        "status": "missing-interval-bound",
    },
    {
        "obligation_id": "pressure_potential_equations",
        "statement": "Construct P and validate partial_r P + R^r=0 and partial_z P + R^z=0.",
        "required_artifact": "directed-rounding pressure integration/potential backend",
        "validated": False,
        "status": "missing-pressure-potential-backend",
    },
    {
        "obligation_id": "chart_pressure_matching",
        "statement": (
            "Validate tail-chart and origin-chart pressure potentials match on "
            "the overlap up to one fixed additive constant."
        ),
        "required_artifact": "interval chart-overlap pressure matching certificate",
        "validated": False,
        "status": "missing-chart-matching-bound",
    },
    {
        "obligation_id": "pressure_tail",
        "statement": "Validate the reconstructed pressure tail and its derivative bounds.",
        "required_artifact": "pressure tail interval certificate",
        "validated": False,
        "status": "missing-pressure-tail-bound",
    },
)


def pressure_obligations() -> list[dict[str, Any]]:
    """Return a mutable copy of the pressure-reconstruction obligations."""

    return deepcopy(list(PRESSURE_OBLIGATIONS))


def pressure_reconstruction_hash(code_hashes: dict[str, str]) -> str:
    """Hash the mathematical pressure ledger and implementation inputs."""

    return stable_json_hash(
        {
            "statement": PRESSURE_RECONSTRUCTION_STATEMENT,
            "obligations": PRESSURE_OBLIGATIONS,
            "code_hashes": code_hashes,
        }
    )


def missing_interval_blockers(obligations: list[dict[str, Any]]) -> list[str]:
    """Return concrete blockers for obligations that are not validated."""

    blockers = []
    for obligation in obligations:
        if obligation.get("validated") is True:
            continue
        blockers.append(
            f"{obligation['obligation_id']} not validated: {obligation['required_artifact']}"
        )
    return blockers
