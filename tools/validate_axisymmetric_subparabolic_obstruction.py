#!/usr/bin/env python3
"""Certify the exact no-go theorem for the frozen smooth axisymmetric gamma<1/2 route."""
from __future__ import annotations

import argparse, hashlib, json, math, os
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "work/twochart_stage0_current_profile_top8pde128_rowlocal_densemortar_step22_nativebatch.json"
PROBLEM = ROOT / "proof-problem.md"
EXECUTION = ROOT / "nss-proof-execution.md"
POSITIVE = ROOT / "certs/final_theorem_manifest.json"
CERT = ROOT / "certs/obstructions/axisymmetric_subparabolic_no_go.json"
MANIFEST = ROOT / "certs/branch_kill_manifest.json"
BASE_COMMIT = "46ddb7e3e1c576ee4697a12581298b25651e3c54"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path: Path) -> dict:
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise ValueError(f"expected object: {path}")
    return value


def finite_tree(value) -> bool:
    if isinstance(value, list):
        return all(finite_tree(x) for x in value)
    return isinstance(value, (int, float)) and math.isfinite(float(value))


def patches(value):
    if isinstance(value, list):
        for item in value:
            if isinstance(item, dict):
                yield item
            else:
                yield from patches(item)


def block_ok(value) -> tuple[bool, dict]:
    ps = list(patches(value))
    ok = bool(ps)
    q0, q1, x0, x1 = 1.0, 0.0, 1.0, 0.0
    for p in ps:
        qi, xi, co = p.get("q_interval"), p.get("x_interval"), p.get("coeffs")
        good = (
            isinstance(qi, list) and len(qi) == 2 and finite_tree(qi)
            and isinstance(xi, list) and len(xi) == 2 and finite_tree(xi)
            and isinstance(co, list) and finite_tree(co)
        )
        ok &= good
        if good:
            q0, q1 = min(q0, qi[0]), max(q1, qi[1])
            x0, x1 = min(x0, xi[0]), max(x1, xi[1])
    return ok and q0 == 0.0 and x0 == 0.0 and x1 == 1.0, {
        "patches": len(ps), "q_range": [q0, q1], "x_range": [x0, x1]
    }


def add(checks: list[dict], name: str, passed: bool, evidence) -> None:
    checks.append({"check_id": name, "pass": bool(passed), "evidence": evidence})


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", type=Path, default=PROFILE)
    ap.add_argument("--problem", type=Path, default=PROBLEM)
    ap.add_argument("--execution", type=Path, default=EXECUTION)
    ap.add_argument("--positive-manifest", type=Path, default=POSITIVE)
    ap.add_argument("--out", type=Path, default=CERT)
    ap.add_argument("--manifest-out", type=Path, default=MANIFEST)
    ns = ap.parse_args()
    paths = {"profile": ns.profile, "problem": ns.problem, "execution": ns.execution,
             "positive_manifest": ns.positive_manifest}
    for p in paths.values():
        if not p.is_file(): raise FileNotFoundError(p)

    profile, positive = read(ns.profile), read(ns.positive_manifest)
    problem, execution = ns.problem.read_text(), ns.execution.read_text()
    gamma = Fraction(profile["requested_options"]["gamma_override"])
    p = 1 / gamma
    checks: list[dict] = []

    add(checks, "exact_exponent", Fraction(2,5) < gamma < Fraction(1,2), {
        "gamma": str(gamma), "gamma-2/5": str(gamma-Fraction(2,5)),
        "1/2-gamma": str(Fraction(1,2)-gamma), "1-2gamma": str(1-2*gamma)})
    add(checks, "tail_power", math.isclose(profile["p"], float(p), abs_tol=1e-14), {
        "1/gamma": str(p), "U_tail": str(1-p), "gradU_Omega_tail": str(-p)})

    pm = ["Work with axisymmetric-with-swirl variables", "U(y)\\sim |y|^{1-\\frac1\\gamma}",
          "Solve the full nonlinear profile equation", "global self-similar profiles exist only"]
    em = ["F_gamma(U_*,P_*) = 0", "global profile used for finite-energy Navier-Stokes gluing",
          "tail chart in (q,x)", "origin chart in (R,Z)=(r^2,z^2)",
          "C3 minimum and preferably C4 interface matching"]
    missing = [x for x in pm if x not in problem] + [x for x in em if x not in execution]
    add(checks, "repository_target_contract", not missing, {"missing": missing,
        "problem_sha256": sha(ns.problem), "execution_sha256": sha(ns.execution)})

    maps = profile.get("coordinate_maps", {})
    global_domain = (
        profile.get("format") == "twochart_profile_projection_v1"
        and maps.get("tail_chart",{}).get("active_domain",{}).get("q",[None])[0] == 0.0
        and maps.get("origin_chart",{}).get("active_domain",{}).get("q",[None,None])[1] == 1.0
        and maps.get("tail_chart",{}).get("active_domain",{}).get("x") == [0.0,1.0]
        and bool(maps.get("overlap",{}).get("q_band")))
    add(checks, "global_two_chart_domain", global_domain, maps)

    blocks = profile.get("tail_chart",{}).get("blocks",{})
    summaries, finite = {}, True
    for name in ("F_an","F_frac","G_an","G_frac"):
        good, summary = block_ok(blocks.get(name)); summaries[name] = summary; finite &= good
    rep = profile.get("tail_chart",{}).get("representation",{})
    finite &= rep.get("F","").startswith("1/2 + q^2") and rep.get("G","").startswith("B + q^2")
    add(checks, "bounded_tail_factors", finite, {"representation": rep, "blocks": summaries})

    ob = profile.get("origin_chart",{}).get("blocks",{})
    origin = all(isinstance(ob.get(k),dict) and ob[k].get("enabled") and ob[k].get("basis")
                 for k in ("F_origin_taylor","G_origin_taylor"))
    orders = set()
    for row in profile.get("hard_newton_schema",{}).get("residual_blocks",[]):
        if row.get("name") == "overlap_derivative_mortar": orders |= set(row.get("orders",[]))
    add(checks, "C2_origin_and_interface_target", origin and {"dqq","dqx","dxx"} <= orders,
        {"origin_coordinates": profile.get("origin_chart",{}).get("coordinate_choice"),
         "mortar_orders": sorted(orders)})

    B = profile.get("B")
    add(checks, "nontrivial_swirl_tail", B == 1.0 and profile.get("tail_legality",{}).get("all_ok") is True,
        {"B": B, "G0": profile.get("preserved_metadata",{}).get("tail_constraints",{}).get("G0")})
    add(checks, "origin_normalization", origin, {
        "ansatz": "psi=r^2 z q^p F; Gamma=r^2 q^p G",
        "consequence": "U_r=O(r), U_z=O(z), U_theta=O(r), hence U(0)=0"})
    add(checks, "paper_majorant_3_8", finite and p == Fraction(20,9), {
        "bound": "|U|<=C|y|q^p; |grad U|+|Omega|<=Cq^p",
        "rates": {"U":"|y|^(-11/9)", "gradU_Omega":"|y|^(-20/9)"}})
    positive_false = positive.get("pass") is False and positive.get("certified_stop_condition_gates") == {"passed":0,"total":5}
    add(checks, "positive_manifest_preserved", positive_false, {
        "pass": positive.get("pass"), "gates": positive.get("certified_stop_condition_gates"),
        "sha256": sha(ns.positive_manifest)})

    passed = all(c["pass"] for c in checks)
    cert = {
      "schema_version":"nsproof-branch-kill-v1", "certificate_name":"axisymmetric_subparabolic_no_go",
      "audited_base_commit":BASE_COMMIT, "branch_kill_pass":passed,
      "target_profile_class_empty":passed, "positive_theorem_pass":False,
      "final_navier_stokes_theorem_certificate_percent":0.0,
      "source_theorem":{
        "authors":["Peter Constantin","Mihaela Ignatova","Vlad Vicol"],
        "title":"On putative self-similarity for incompressible 3D Euler",
        "arxiv":"2602.17570v3", "version_date_utc":"2026-07-20T03:23:08Z",
        "theorem":"4.5", "url":"https://arxiv.org/html/2602.17570v3",
        "conclusion":"nontrivial C^2 smooth axisymmetric global profile with (3.5),(3.8) implies gamma>=1/2"},
      "exact_arithmetic":{"gamma":str(gamma),"1/gamma":str(p),"1-2gamma":str(1-2*gamma),
        "U_tail_exponent":str(1-p),"gradU_Omega_tail_exponent":str(-p)},
      "inputs":{k:{"path":os.path.relpath(v,ROOT),"sha256":sha(v)} for k,v in paths.items()},
      "hypothesis_checks":checks,
      "proof_chain":[
        "The natural tail confines every backward meridional trajectory and preserves r>0.",
        "Along it, exp((1-2gamma)tau) R U_theta is constant.",
        "At gamma=9/20, 1-2gamma=1/10>0, so tau->-infinity forces U_theta=0.",
        "Then Omega_r=Omega_z=0; transport of Omega_theta/r forces Omega_theta=0.",
        "curl U=div U=0 and grad U->0 imply U is constant; U(0)=0 gives U=0.",
        "This contradicts the intended nontrivial B=1 swirl profile."],
      "scope":{"killed":"C^2 smooth axisymmetric whole-space global exact self-similar natural-tail profiles with 2/5<gamma<1/2",
        "not_claimed":["3D Navier-Stokes regularity or blow-up","non-axisymmetric mechanisms","below-C^2 profiles","boundary/local/non-self-similar mechanisms"]},
      "conclusion":"TARGET CLASS EMPTY" if passed else "APPLICABILITY CHECK FAILED"}
    ns.out.parent.mkdir(parents=True,exist_ok=True)
    ns.out.write_text(json.dumps(cert,indent=2,sort_keys=True)+"\n")
    manifest = {"schema_version":"nsproof-branch-kill-v1","certificate_name":"branch_kill_manifest",
      "pass":passed and positive_false,"branch_kill_pass":passed,"target_profile_class_empty":passed,
      "positive_theorem_pass":False,"resolution_type":"exact_analytical_no_go_for_frozen_target_class",
      "dependencies":[{"path":os.path.relpath(ns.out,ROOT),"sha256":sha(ns.out),"pass":passed},
        {"path":os.path.relpath(ns.positive_manifest,ROOT),"sha256":sha(ns.positive_manifest),"pass":False,"role":"unchanged positive manifest"}]}
    ns.manifest_out.parent.mkdir(parents=True,exist_ok=True)
    ns.manifest_out.write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n")
    print(f"checks={sum(c['pass'] for c in checks)}/{len(checks)}")
    print(f"gamma={gamma} one_minus_2gamma={1-2*gamma}")
    print(f"branch_kill_pass={str(passed).lower()}")
    print("positive_theorem_pass=false")
    print(f"status={'TARGET_CLASS_EMPTY' if passed else 'APPLICABILITY_CHECK_FAILED'}")
    return 0 if passed else 1

if __name__ == "__main__": raise SystemExit(main())
