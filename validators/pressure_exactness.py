#!/usr/bin/env python3
"""Pressure-reconstruction ledger helpers.

This module records the exact obligations needed to turn a validated
pressure-eliminated axisymmetric-with-swirl profile into a velocity-pressure
profile.  It intentionally contains no interval backend and never returns a
passing validation result.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from fractions import Fraction
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


@dataclass(frozen=True)
class LaurentPolynomial:
    """Tiny exact Laurent-polynomial ring in ``r,z`` for identity checks."""

    terms: dict[tuple[int, int], Fraction]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "terms",
            {key: value for key, value in self.terms.items() if value},
        )

    @staticmethod
    def monomial(r_power: int, z_power: int, coeff: int | Fraction = 1) -> "LaurentPolynomial":
        return LaurentPolynomial({(int(r_power), int(z_power)): Fraction(coeff)})

    def __add__(self, other: object) -> "LaurentPolynomial":
        rhs = as_laurent(other)
        terms = dict(self.terms)
        for key, value in rhs.terms.items():
            terms[key] = terms.get(key, Fraction(0)) + value
        return LaurentPolynomial(terms)

    __radd__ = __add__

    def __neg__(self) -> "LaurentPolynomial":
        return LaurentPolynomial({key: -value for key, value in self.terms.items()})

    def __sub__(self, other: object) -> "LaurentPolynomial":
        return self + (-as_laurent(other))

    def __rsub__(self, other: object) -> "LaurentPolynomial":
        return as_laurent(other) + (-self)

    def __mul__(self, other: object) -> "LaurentPolynomial":
        rhs = as_laurent(other)
        terms: dict[tuple[int, int], Fraction] = {}
        for (r_power, z_power), lhs_coeff in self.terms.items():
            for (r_power_rhs, z_power_rhs), rhs_coeff in rhs.terms.items():
                key = (r_power + r_power_rhs, z_power + z_power_rhs)
                terms[key] = terms.get(key, Fraction(0)) + lhs_coeff * rhs_coeff
        return LaurentPolynomial(terms)

    __rmul__ = __mul__

    def scale(self, value: int | Fraction) -> "LaurentPolynomial":
        factor = Fraction(value)
        return LaurentPolynomial({key: factor * coeff for key, coeff in self.terms.items()})

    def shift(self, r_power: int = 0, z_power: int = 0) -> "LaurentPolynomial":
        return LaurentPolynomial(
            {
                (r_exp + int(r_power), z_exp + int(z_power)): coeff
                for (r_exp, z_exp), coeff in self.terms.items()
            }
        )

    def dr(self) -> "LaurentPolynomial":
        return LaurentPolynomial(
            {
                (r_power - 1, z_power): coeff * r_power
                for (r_power, z_power), coeff in self.terms.items()
                if r_power
            }
        )

    def dz(self) -> "LaurentPolynomial":
        return LaurentPolynomial(
            {
                (r_power, z_power - 1): coeff * z_power
                for (r_power, z_power), coeff in self.terms.items()
                if z_power
            }
        )

    def is_zero(self) -> bool:
        return not self.terms

    def summary(self) -> dict[str, Any]:
        if not self.terms:
            return {"term_count": 0, "max_abs_coeff": "0", "sample_terms": []}
        items = sorted(self.terms.items(), key=lambda item: (item[0][0], item[0][1]))
        max_abs = max(abs(coeff) for _key, coeff in items)
        return {
            "term_count": len(items),
            "max_abs_coeff": str(max_abs),
            "sample_terms": [
                {"r_power": key[0], "z_power": key[1], "coeff": str(coeff)}
                for key, coeff in items[:8]
            ],
        }


def as_laurent(value: object) -> LaurentPolynomial:
    if isinstance(value, LaurentPolynomial):
        return value
    if isinstance(value, (int, Fraction)):
        return LaurentPolynomial.monomial(0, 0, Fraction(value))
    raise TypeError(f"cannot coerce {value!r} to LaurentPolynomial")


def formal_pressure_identity_self_test() -> dict[str, Any]:
    """Verify the pressure-elimination identities in exact rational algebra.

    The check uses a nontrivial manufactured Laurent-polynomial streamfunction
    and swirl with the same axis divisibility as the profile ansatz.  It is a
    positive-control algebra regression, not a replacement for the interval
    profile-specific pressure certificate.
    """

    r = LaurentPolynomial.monomial(1, 0)
    z = LaurentPolynomial.monomial(0, 1)
    gamma = Fraction(9, 20)
    psi = LaurentPolynomial.monomial(2, 1) * (
        1 + 2 * r + 3 * z + 5 * r * r + 7 * r * z + 11 * z * z
    )
    gamma_swirl = LaurentPolynomial.monomial(2, 0) * (
        2 - r + 4 * z + 3 * r * r - 5 * r * z + 6 * z * z
    )

    u_r = -psi.dz().shift(r_power=-1)
    u_z = psi.dr().shift(r_power=-1)
    u_theta = gamma_swirl.shift(r_power=-1)

    residual_r = (
        u_r.scale(1 - gamma)
        + (r * u_r.dr() + z * u_r.dz()).scale(gamma)
        + u_r * u_r.dr()
        + u_z * u_r.dz()
        - (u_theta * u_theta).shift(r_power=-1)
    )
    residual_z = (
        u_z.scale(1 - gamma)
        + (r * u_z.dr() + z * u_z.dz()).scale(gamma)
        + u_r * u_z.dr()
        + u_z * u_z.dz()
    )
    residual_theta = (
        u_theta.scale(1 - gamma)
        + (r * u_theta.dr() + z * u_theta.dz()).scale(gamma)
        + u_r * u_theta.dr()
        + u_z * u_theta.dz()
        + (u_r * u_theta).shift(r_power=-1)
    )

    a = psi.dr().dr() - psi.dr().shift(r_power=-1) + psi.dz().dz()
    e_psi = (
        (r * r * a).scale(1 - gamma)
        + (r * r * r * a.dr()).scale(gamma)
        + (z * r * r * a.dz()).scale(gamma)
        + r * (psi.dr() * a.dz() - psi.dz() * a.dr())
        + (psi.dz() * a).scale(2)
        + (gamma_swirl * gamma_swirl).dz()
    )
    e_gamma = (
        gamma_swirl.scale(1 - 2 * gamma)
        + (r * gamma_swirl.dr() + z * gamma_swirl.dz()).scale(gamma)
        + (psi.dr() * gamma_swirl.dz() - psi.dz() * gamma_swirl.dr()).shift(r_power=-1)
    )

    theta_identity_defect = r * residual_theta - e_gamma
    curl_identity_defect = e_psi + (residual_r.dz() - residual_z.dr()).shift(r_power=3)
    pass_gate = theta_identity_defect.is_zero() and curl_identity_defect.is_zero()
    return {
        "pass": bool(pass_gate),
        "backend": "exact-rational-laurent-polynomial",
        "gamma": str(gamma),
        "manufactured_fields": {
            "psi_axis_factor": "r^2 z",
            "Gamma_axis_factor": "r^2",
            "psi_term_count": len(psi.terms),
            "Gamma_term_count": len(gamma_swirl.terms),
        },
        "identities_checked": {
            "theta": "r*R^theta - E_Gamma == 0",
            "one_form_curl": "E_psi + r^3*(partial_z R^r - partial_r R^z) == 0",
        },
        "theta_identity_defect": theta_identity_defect.summary(),
        "one_form_curl_identity_defect": curl_identity_defect.summary(),
        "scope": (
            "Exact manufactured-field regression for the pressure-elimination "
            "algebra. The actual profile still needs interval bounds on the "
            "certified profile ball and pressure chart matching."
        ),
    }
