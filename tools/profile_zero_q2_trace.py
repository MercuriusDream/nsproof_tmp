#!/usr/bin/env python3
"""Remove the ordinary q^2 analytic trace from projected profiles.

For profiles of the form

    F = 1/2 + q^2 F_an + q^p F_frac + ...
    G = B   + q^2 G_an + q^p G_frac + ...

the ordinary q^2 tail coefficient is F_an(0,x), G_an(0,x).  This tool edits
only the q=0 Chebyshev patches of F_an/G_an so that those traces vanish
exactly in the patch Chebyshev representation.  It is a diagnostic for testing
whether the current branch relies on an unvalidated ordinary q^2 tail channel.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)


def load_json(path: str) -> dict[str, object]:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def save_json(path: str, data: dict[str, object]) -> None:
    out_dir = os.path.dirname(path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write("\n")


def zero_block_trace(data: dict[str, object], block_name: str) -> dict[str, object]:
    blocks = data["blocks"]  # type: ignore[index]
    patches = blocks[block_name]  # type: ignore[index]
    changed = 0
    max_trace_coeff = 0.0
    for patch in patches:
        q0, _q1 = patch["q_interval"]
        if abs(float(q0)) > 1e-15:
            continue
        coeffs = patch["coeffs"]
        if not coeffs:
            continue
        q_count = len(coeffs)
        x_count = len(coeffs[0])
        trace_coeffs = []
        for kx in range(x_count):
            trace = 0.0
            for kq in range(q_count):
                trace += ((-1.0) ** kq) * float(coeffs[kq][kx])
            trace_coeffs.append(trace)
            max_trace_coeff = max(max_trace_coeff, abs(trace))
        for kx, trace in enumerate(trace_coeffs):
            coeffs[0][kx] = float(coeffs[0][kx]) - trace
        changed += 1
    return {
        "block": block_name,
        "changed_q0_patches": changed,
        "max_removed_trace_cheb_coeff": max_trace_coeff,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    data = load_json(args.input)
    if data.get("format") != "transseries_cheb_projection_v1":
        raise ValueError("input must be a transseries_cheb_projection_v1 JSON file")
    out = copy.deepcopy(data)
    evidence = [zero_block_trace(out, "F_an"), zero_block_trace(out, "G_an")]
    out["q2_trace_zeroing_evidence"] = {
        "status": "ordinary_q2_trace_removed_not_validated",
        "source": args.input,
        "blocks": evidence,
        "note": "Only F_an/G_an q=0 traces were removed; this tests dependence on an unvalidated q^2 tail channel.",
    }
    save_json(args.out, out)
    print(f"input={args.input}")
    print(f"saved={args.out}")
    for item in evidence:
        print(
            f"{item['block']}: changed_q0_patches={item['changed_q0_patches']} "
            f"max_removed_trace_cheb_coeff={item['max_removed_trace_cheb_coeff']:.12e}"
        )
    print("status=ORDINARY_Q2_TRACE_REMOVED_NOT_VALIDATED")


if __name__ == "__main__":
    main()
