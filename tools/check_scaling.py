#!/usr/bin/env python3
"""Pure-Python checks for the NSS Type-II scaling identities.

The script verifies the exponent signs used in nss-proof-execution.md.
It intentionally has no third-party dependencies.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass


@dataclass(frozen=True)
class Scaling:
    gamma: float

    @property
    def a(self) -> float:
        """Positive decay exponent: U ~ r^(-a)."""
        return 1.0 / self.gamma - 1.0

    @property
    def velocity_tail_power(self) -> float:
        """Power p in U ~ r^p."""
        return 1.0 - 1.0 / self.gamma

    @property
    def vorticity_tail_power(self) -> float:
        """Power p in Omega ~ r^p."""
        return -1.0 / self.gamma

    @property
    def viscosity_decay(self) -> float:
        return 1.0 - 2.0 * self.gamma

    @property
    def gluing_h81_power(self) -> float:
        return 1.5 - 1.0 / self.gamma

    @property
    def viscous_profile_h81_power(self) -> float:
        return -0.5 - 1.0 / self.gamma

    @property
    def fixed_physical_energy_tau_power(self) -> float:
        # tau^(5g-2) * (tau^-g)^(3-2a)
        return (5.0 * self.gamma - 2.0) - self.gamma * (3.0 - 2.0 * self.a)

    def assert_wedge_identities(self) -> None:
        if not (0.4 < self.gamma < 0.5):
            raise AssertionError(f"gamma={self.gamma} is outside (2/5,1/2)")
        if not (1.0 < self.a < 1.5):
            raise AssertionError(f"a={self.a} is outside (1,3/2)")
        if not (self.viscosity_decay > 0.0):
            raise AssertionError("viscosity is not perturbative")
        if not (self.gluing_h81_power < 0.0):
            raise AssertionError("moving-cutoff H^8_1 gluing power does not decay")
        if abs(self.fixed_physical_energy_tau_power) > 1e-12:
            raise AssertionError("fixed physical cutoff energy is not scale-invariant")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--gamma",
        type=float,
        action="append",
        default=None,
        help="Self-similar exponent. May be supplied multiple times.",
    )
    args = parser.parse_args()

    gammas = args.gamma if args.gamma else [0.41, 0.45, 0.49]
    for gamma in gammas:
        s = Scaling(gamma)
        s.assert_wedge_identities()
        print(f"gamma = {gamma:.6f}")
        print(f"  a = 1/gamma - 1                  = {s.a:.12f}")
        print(f"  U tail power                      = {s.velocity_tail_power:.12f}")
        print(f"  Omega tail power                  = {s.vorticity_tail_power:.12f}")
        print(f"  viscosity decay 1 - 2gamma        = {s.viscosity_decay:.12f}")
        print(f"  gluing H^8_1 power 3/2 - 1/gamma  = {s.gluing_h81_power:.12f}")
        print(f"  viscous profile H^8_1 power       = {s.viscous_profile_h81_power:.12f}")
        print(f"  fixed cutoff energy tau power     = {s.fixed_physical_energy_tau_power:.12e}")


if __name__ == "__main__":
    main()
