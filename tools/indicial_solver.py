#!/usr/bin/env python3
"""Prototype indicial shooting solver for the conical-core pencil.

This is intentionally dependency-free. It is not a proof validator; it is the
first executable version of the determinant gate described in proof-problem.md.
The production version should use interval or ball arithmetic.
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from typing import Iterable


State = tuple[complex, complex, complex, complex]


@dataclass(frozen=True)
class ResidualComponents:
    n_phi: float
    n_chi: float
    n_amp: float
    n_h: float
    r_phi: complex
    r_chi: complex
    r_amp: complex
    r_h: complex

    @property
    def rms(self) -> float:
        return math.sqrt(
            self.n_phi * self.n_phi
            + self.n_chi * self.n_chi
            + self.n_amp * self.n_amp
            + self.n_h * self.n_h
        )


@dataclass(frozen=True)
class Params:
    gamma: float
    B: float
    delta: complex

    @property
    def alpha(self) -> float:
        return 0.5 - self.gamma


def add(a: State, b: State, scale: complex = 1.0) -> State:
    return tuple(x + scale * y for x, y in zip(a, b))  # type: ignore[return-value]


def rhs(zeta: float, y: State, p: Params) -> State:
    phi, phip, chi, h = y
    delta = p.delta
    alpha = p.alpha
    B = p.B
    denom = 1.5 * zeta
    phipp = (
        h
        + (3.0 - 2.0 * delta) * zeta * phip
        - (3.0 - delta) * (1.0 - delta) * phi
    ) / (1.0 + zeta * zeta)
    chip = (2.0 * B * phip - alpha * delta * chi) / denom
    hp = -((1.5 + alpha * delta) * h + 2.0 * B * chip) / denom
    return (phip, phipp, chip, hp)


def rk4_step(zeta: float, y: State, dz: float, p: Params) -> State:
    k1 = rhs(zeta, y, p)
    k2 = rhs(zeta + 0.5 * dz, add(y, k1, 0.5 * dz), p)
    k3 = rhs(zeta + 0.5 * dz, add(y, k2, 0.5 * dz), p)
    k4 = rhs(zeta + dz, add(y, k3, dz), p)
    total = add(add(k1, k2, 2.0), add(k3, k4, 2.0))
    return add(y, total, dz / 6.0)


def phi_to_h_coeff(j: int, delta: complex) -> complex:
    """Coefficient multiplying p_j in h_j, excluding the p_{j+1} term.

    Here phi = sum p_j zeta^(2j+1), chi = sum q_j zeta^(2j),
    and h = sum h_j zeta^(2j+1).
    """

    return (
        (2 * j + 1) * (2 * j)
        - (3.0 - 2.0 * delta) * (2 * j + 1)
        + (3.0 - delta) * (1.0 - delta)
    )


def frobenius_coefficients(p: Params, terms: int) -> tuple[list[complex], list[complex]]:
    """Return Frobenius coefficients for regular equatorial data.

    phi(zeta) = sum_j p_j zeta^(2j+1),
    chi(zeta) = sum_j q_j zeta^(2j).

    The normalization is q_0=1. For generic delta, regularity and parity
    leave only this one amplitude.
    """

    if terms < 1:
        raise ValueError("terms must be >= 1")
    if abs(p.B) < 1e-14:
        raise ValueError("This Frobenius normalization assumes B != 0.")

    delta = p.delta
    alpha = p.alpha
    B = p.B
    q = [0j for _ in range(terms)]
    coeff_p = [0j for _ in range(terms)]
    q[0] = 1.0

    for j in range(terms):
        coeff_p[j] = ((3.0 * j + alpha * delta) * q[j]) / (
            2.0 * B * (2 * j + 1)
        )
        if j + 1 >= terms:
            break
        next_s = (3.0 * (j + 1) + alpha * delta) / (
            2.0 * B * (2 * j + 3)
        )
        a_j = (2 * j + 3) * (2 * j + 2)
        b_j = phi_to_h_coeff(j, delta)
        prefactor = 3.0 * (j + 1) + alpha * delta
        denom = prefactor * a_j * next_s + 4.0 * B * (j + 1)
        numer = -prefactor * b_j * coeff_p[j]
        q[j + 1] = numer / denom

    return coeff_p, q


def frobenius_initial(eps: float, p: Params, terms: int = 2) -> State:
    if abs(p.B) < 1e-14:
        raise ValueError("This Frobenius normalization assumes B != 0.")
    coeff_p, q = frobenius_coefficients(p, terms)
    delta = p.delta
    phi = 0j
    phip = 0j
    phipp = 0j
    chi = 0j
    for j, p_j in enumerate(coeff_p):
        power = 2 * j + 1
        phi += p_j * eps**power
        phip += power * p_j * eps ** (power - 1)
        if power >= 2:
            phipp += power * (power - 1) * p_j * eps ** (power - 2)
    for j, q_j in enumerate(q):
        chi += q_j * eps ** (2 * j)
    h = (
        (1.0 + eps * eps) * phipp
        - (3.0 - 2.0 * delta) * eps * phip
        + (3.0 - delta) * (1.0 - delta) * phi
    )
    return (phi, phip, chi, h)


def integrate(
    delta: complex,
    gamma: float,
    B: float,
    eps: float,
    L: float,
    steps: int,
    series_terms: int,
) -> State:
    p = Params(gamma=gamma, B=B, delta=delta)
    y = frobenius_initial(eps, p, series_terms)
    zeta = eps
    dz = (L - eps) / steps
    for _ in range(steps):
        y = rk4_step(zeta, y, dz, p)
        zeta += dz
    return y


def residual_components(
    delta: complex,
    gamma: float,
    B: float,
    eps: float,
    L: float,
    steps: int,
    series_terms: int,
) -> ResidualComponents:
    p = Params(gamma=gamma, B=B, delta=delta)
    y = integrate(delta, gamma, B, eps, L, steps, series_terms)
    phi, phip, chi, h = y
    chip = rhs(L, y, p)[2]

    r_phi = L * phip - (1.0 - delta) * phi
    r_chi = L * chip + delta * chi
    c_phi = phi / (L ** (1.0 - delta))
    c_chi = chi / (L ** (-delta))
    r_amp = 2.0 * B * (1.0 - delta) * c_phi + delta * (1.0 + gamma) * c_chi
    r_h = h + delta * (1.0 - delta) * phi / (L * L)

    n_phi = abs(r_phi) / (abs(L * phip) + abs(phi) + 1e-30)
    n_chi = abs(r_chi) / (abs(L * chip) + abs(chi) + 1e-30)
    n_amp = abs(r_amp) / (
        abs(2.0 * B * (1.0 - delta) * c_phi)
        + abs(delta * (1.0 + gamma) * c_chi)
        + 1e-30
    )
    n_h = abs(r_h) / (abs(h) + abs(delta * (1.0 - delta) * phi / (L * L)) + 1e-30)
    return ResidualComponents(
        n_phi=n_phi,
        n_chi=n_chi,
        n_amp=n_amp,
        n_h=n_h,
        r_phi=r_phi,
        r_chi=r_chi,
        r_amp=r_amp,
        r_h=r_h,
    )


def residual(
    delta: complex,
    gamma: float,
    B: float,
    eps: float,
    L: float,
    steps: int,
    series_terms: int,
) -> float:
    return residual_components(delta, gamma, B, eps, L, steps, series_terms).rms


def scan_values(start: float, stop: float, count: int) -> Iterable[float]:
    if count <= 1:
        yield start
        return
    step = (stop - start) / (count - 1)
    for i in range(count):
        yield start + i * step


def optimize_delta(
    start: complex,
    gamma: float,
    B: float,
    eps: float,
    L: float,
    steps: int,
    step_real: float,
    step_imag: float,
    iterations: int,
    min_real: float,
    max_abs_imag: float,
    series_terms: int,
) -> tuple[complex, float]:
    """Pattern-search minimization of the boundary residual."""
    z = start
    best = residual(z, gamma, B, eps, L, steps, series_terms)
    directions = [
        complex(1.0, 0.0),
        complex(-1.0, 0.0),
        complex(0.0, 1.0),
        complex(0.0, -1.0),
        complex(1.0, 1.0),
        complex(1.0, -1.0),
        complex(-1.0, 1.0),
        complex(-1.0, -1.0),
    ]
    dr = step_real
    di = step_imag
    for i in range(iterations):
        improved = False
        candidate_best = best
        candidate_z = z
        for direction in directions:
            trial = z + complex(direction.real * dr, direction.imag * di)
            if trial.real < min_real:
                continue
            if abs(trial.imag) > max_abs_imag:
                continue
            score = residual(trial, gamma, B, eps, L, steps, series_terms)
            if score < candidate_best:
                candidate_best = score
                candidate_z = trial
                improved = True
        if improved:
            z = candidate_z
            best = candidate_best
        else:
            dr *= 0.5
            di *= 0.5
        print(
            f"iter={i:03d} delta={z.real:.12f}{z.imag:+.12f}i "
            f"residual={best:.12e} step=({dr:.3e},{di:.3e})"
        )
        if max(dr, di) < 1e-8:
            break
    return z, best


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gamma", type=float, default=0.45)
    parser.add_argument("--B", type=float, default=1.0)
    parser.add_argument("--eps", type=float, default=1e-4)
    parser.add_argument("--L", type=float, default=40.0)
    parser.add_argument("--steps", type=int, default=20000)
    parser.add_argument("--series-terms", type=int, default=6)
    parser.add_argument("--delta-real", type=float, default=1.0)
    parser.add_argument("--delta-imag", type=float, default=0.0)
    parser.add_argument("--scan", action="store_true")
    parser.add_argument("--delta-min", type=float, default=0.05)
    parser.add_argument("--delta-max", type=float, default=4.0)
    parser.add_argument("--count", type=int, default=80)
    parser.add_argument("--imag-min", type=float, default=0.0)
    parser.add_argument("--imag-max", type=float, default=0.0)
    parser.add_argument("--imag-count", type=int, default=1)
    parser.add_argument("--optimize", action="store_true")
    parser.add_argument("--opt-step-real", type=float, default=0.1)
    parser.add_argument("--opt-step-imag", type=float, default=0.1)
    parser.add_argument("--opt-iters", type=int, default=40)
    parser.add_argument("--opt-min-real", type=float, default=1e-4)
    parser.add_argument("--opt-max-abs-imag", type=float, default=10.0)
    parser.add_argument("--components", action="store_true")
    args = parser.parse_args()

    if not (0.4 < args.gamma < 0.5):
        raise SystemExit("gamma must lie in (2/5,1/2) for this proof program.")

    if args.optimize:
        start = complex(args.delta_real, args.delta_imag)
        z, score = optimize_delta(
            start=start,
            gamma=args.gamma,
            B=args.B,
            eps=args.eps,
            L=args.L,
            steps=args.steps,
            step_real=args.opt_step_real,
            step_imag=args.opt_step_imag,
            iterations=args.opt_iters,
            min_real=args.opt_min_real,
            max_abs_imag=args.opt_max_abs_imag,
            series_terms=args.series_terms,
        )
        print(
            f"\nOptimized candidate: delta={z.real:.12f}{z.imag:+.12f}i "
            f"residual={score:.12e}"
        )
    elif args.scan:
        scored = []
        for d_re in scan_values(args.delta_min, args.delta_max, args.count):
            for d_im in scan_values(args.imag_min, args.imag_max, args.imag_count):
                d = complex(d_re, d_im)
                label = f"{d_re:.8f}{d_im:+.8f}i"
                try:
                    score = residual(
                        d,
                        args.gamma,
                        args.B,
                        args.eps,
                        args.L,
                        args.steps,
                        args.series_terms,
                    )
                except (OverflowError, ZeroDivisionError, ValueError) as exc:
                    print(f"delta={label} failed: {exc}")
                    continue
                scored.append((score, d))
                print(f"delta={label} residual={score:.6e}")
        print("\nBest candidates:")
        for score, d in sorted(scored, key=lambda item: item[0])[:10]:
            print(f"  delta={d.real:.10f}{d.imag:+.10f}i residual={score:.6e}")
    else:
        d = complex(args.delta_real, args.delta_imag)
        components = residual_components(
            d,
            args.gamma,
            args.B,
            args.eps,
            args.L,
            args.steps,
            args.series_terms,
        )
        print(
            f"gamma={args.gamma} B={args.B} "
            f"delta={d.real}{d.imag:+}i residual={components.rms:.12e}"
        )
        if args.components:
            print("normalized components:")
            print(f"  phi power residual = {components.n_phi:.12e}")
            print(f"  chi power residual = {components.n_chi:.12e}")
            print(f"  amplitude residual = {components.n_amp:.12e}")
            print(f"  h residual         = {components.n_h:.12e}")
            print("raw components:")
            print(f"  r_phi = {components.r_phi.real:.12e}{components.r_phi.imag:+.12e}i")
            print(f"  r_chi = {components.r_chi.real:.12e}{components.r_chi.imag:+.12e}i")
            print(f"  r_amp = {components.r_amp.real:.12e}{components.r_amp.imag:+.12e}i")
            print(f"  r_h   = {components.r_h.real:.12e}{components.r_h.imag:+.12e}i")


if __name__ == "__main__":
    main()
