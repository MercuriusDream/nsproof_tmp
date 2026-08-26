#!/usr/bin/env python3
from __future__ import annotations

import ast
import hashlib
import itertools
import json
import math
import os
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "output"
OUT.mkdir(parents=True, exist_ok=True)


def locate_rp4() -> Path:
    roots = [Path("/usr/share/gap"), Path("/usr/lib/gap"), Path("/usr/lib64/gap"), Path("/opt")]
    hits: list[Path] = []
    for root in roots:
        if root.exists():
            hits.extend(root.rglob("RP4.scb"))
    if not hits:
        raise FileNotFoundError("RP4.scb was not found after installing gap-simpcomp")
    return sorted(hits, key=lambda p: len(str(p)))[0]


def load_facets_with_gap(path: Path) -> list[list[int]]:
    gap_script = ROOT / "load_rp4.g"
    gap_script.write_text(
        'LoadPackage("simpcomp");;\n'
        f'K:=SCLoad("{str(path).replace(chr(92), chr(92)*2)}");;\n'
        'Print("FACETS_BEGIN\\n");;\n'
        'Print(SCFacetsEx(K),"\\n");;\n'
        'Print("FACETS_END\\n");;\n'
        'QUIT;\n'
    )
    proc = subprocess.run(
        ["gap", "-q", str(gap_script)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
        timeout=180,
    )
    (OUT / "gap_output.txt").write_text(proc.stdout)
    if proc.returncode != 0:
        raise RuntimeError(f"GAP exited with {proc.returncode}:\n{proc.stdout[-4000:]}")
    match = re.search(r"FACETS_BEGIN\s*(\[.*?\])\s*FACETS_END", proc.stdout, re.S)
    if not match:
        raise RuntimeError(f"Could not parse GAP facets output:\n{proc.stdout[-4000:]}")
    facets = ast.literal_eval(match.group(1))
    if not isinstance(facets, list) or not all(isinstance(f, list) for f in facets):
        raise TypeError("SCFacetsEx output is not a list of lists")
    return [[int(v) for v in f] for f in facets]


def face_masks(facets: list[list[int]]) -> set[int]:
    labels = sorted({v for f in facets for v in f})
    if len(labels) != 16:
        raise ValueError(f"expected 16 vertices, got labels={labels}")
    relabel = {v: i for i, v in enumerate(labels)}
    faces: set[int] = set()
    for facet in facets:
        if len(facet) != 5:
            raise ValueError(f"non-4-simplex facet: {facet}")
        verts = [relabel[v] for v in facet]
        for r in range(1, 6):
            for sub in itertools.combinations(verts, r):
                mask = sum(1 << i for i in sub)
                faces.add(mask)
    return faces


def zeta(values: list[int], n: int) -> list[int]:
    out = values[:]
    for i in range(n):
        bit = 1 << i
        for mask in range(1 << n):
            if mask & bit:
                out[mask] += out[mask ^ bit]
    return out


def mobius(values: list[int], n: int) -> list[int]:
    out = values[:]
    for i in range(n):
        bit = 1 << i
        for mask in range(1 << n):
            if mask & bit:
                out[mask] -= out[mask ^ bit]
    return out


def render_expression(coeff: dict[int, int], n: int) -> str:
    pieces: list[str] = []
    for mask in sorted(coeff, key=lambda m: (m.bit_count(), m)):
        c = coeff[mask]
        monomial = "*".join(f"x{i + 1}" for i in range(n) if mask & (1 << i))
        if not pieces:
            pieces.append(monomial if c == 1 else "-" + monomial)
        else:
            pieces.append((" + " if c == 1 else " - ") + monomial)
    return "".join(pieces)


def main() -> None:
    rp4 = locate_rp4()
    facets = load_facets_with_gap(rp4)
    facets = sorted(sorted(f) for f in facets)
    if len(facets) != 150 or len({tuple(f) for f in facets}) != 150:
        raise ValueError(f"expected 150 distinct facets, got {len(facets)}")

    faces = face_masks(facets)
    n = 16
    by_size = {k: sum(mask.bit_count() == k for mask in faces) for k in range(1, 6)}
    expected_f = {1: 16, 2: 120, 3: 330, 4: 375, 5: 150}
    if by_size != expected_f:
        raise ValueError(f"unexpected f-vector: {by_size}")

    coeff_array = [0] * (1 << n)
    for mask in faces:
        coeff_array[mask] = 1 if mask.bit_count() % 2 == 1 else -1
    values = zeta(coeff_array, n)
    value_set = sorted(set(values))

    # Independent path: direct face containment on every vertex subset.
    direct = [0] * (1 << n)
    face_items = [(mask, coeff_array[mask]) for mask in faces]
    for subset in range(1 << n):
        direct[subset] = sum(c for mask, c in face_items if mask & ~subset == 0)
    if direct != values:
        raise AssertionError("direct Euler and zeta-transform evaluations disagree")

    recovered = mobius(values, n)
    if recovered != coeff_array:
        raise AssertionError("Möbius round trip failed")

    degree = max(mask.bit_count() for mask, c in enumerate(recovered) if c)
    s0 = sum(values[1 << i] != values[0] for i in range(n))
    c_threshold = math.log(6) / math.log(3)
    log_margin = math.log(s0) * math.log(3) - math.log(6) * math.log(degree)
    boolean = value_set == [0, 1]
    passed = boolean and degree > 1 and s0 > degree ** c_threshold and log_margin > 0

    coeff = {mask: c for mask, c in enumerate(recovered) if c}
    expression = render_expression(coeff, n)
    sha = hashlib.sha256((expression + "\n").encode()).hexdigest()

    report = {
        "status": "PASS" if passed else "FAIL",
        "construction": "Euler characteristic of induced subcomplexes of the 16-vertex RP4 triangulation",
        "rp4_path": str(rp4),
        "facet_count": len(facets),
        "face_counts": by_size,
        "n": n,
        "degree": degree,
        "s0": s0,
        "value_set": value_set,
        "bad_points": [i for i, v in enumerate(values) if v not in (0, 1)][:100],
        "boolean_points_checked": 1 << n,
        "nonzero_coefficients": len(coeff),
        "threshold_c": c_threshold,
        "achieved_a": math.log(s0) / math.log(degree),
        "log_margin": log_margin,
        "submission_sha256": sha,
        "facets": facets,
    }
    (OUT / "result.json").write_text(json.dumps(report, indent=2) + "\n")
    (OUT / "facets.json").write_text(json.dumps(facets, indent=2) + "\n")
    (OUT / "values.json").write_text(json.dumps(values) + "\n")
    if passed:
        (OUT / "submission.txt").write_text(expression + "\n")
        (OUT / "RESULT.md").write_text(
            "# Verified degree-sensitivity breakthrough\n\n"
            f"- n = {n}\n- degree = {degree}\n- s0 = {s0}\n"
            f"- achieved exponent = {math.log(s0) / math.log(degree):.30f}\n"
            f"- threshold = {c_threshold:.30f}\n- log margin = {log_margin:.30f}\n"
            f"- all {1 << n} cube points checked twice with exact integer arithmetic\n"
            f"- SHA-256(submission.txt) = `{sha}`\n"
        )
    else:
        (OUT / "RESULT.md").write_text(
            "# RP4 induced-Euler construction rejected\n\n"
            f"The exact value set is `{value_set}`. The first bad points are "
            f"`{report['bad_points']}`.\n"
        )
    print(json.dumps(report, indent=2))
    if not passed:
        raise SystemExit(3)


if __name__ == "__main__":
    main()
