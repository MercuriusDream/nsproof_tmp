#!/usr/bin/env python3
"""Stage-0 CLI skeleton for hard-constrained two-chart Newton.

This command is intentionally a dry-run planner until
``validators.compactified_equations_twochart`` exposes the residual/Jacobian
contract needed by the real solver.  It parses the planned Newton flags,
checks the hard tail gates carried by the two-chart profile, and emits a
machine-readable plan.  It does not perform coefficient updates.
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import sys
from dataclasses import asdict, dataclass
from typing import Any


ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)


STATUS = "TWOCHART_NEWTON_STAGE0_DRY_RUN_ONLY"
MISSING_HOOK_STATUS = "REFUSED_REAL_NEWTON_MISSING_TWOCHART_RESIDUAL_JACOBIAN_HOOKS"
SUPPORTED_FORMATS = {
    "twochart_profile_projection_v1",
    "twochart_profile_v1",
    "compactified_twochart_profile_v1",
}
REQUIRED_HOOKS = ("eval_residual_and_jacobian",)


@dataclass(frozen=True)
class HookReport:
    module: str
    available: bool
    missing_hooks: tuple[str, ...]
    required_hooks: tuple[str, ...]
    import_error: str


def load_json(path: str) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def save_json(path: str, data: dict[str, Any]) -> None:
    out_dir = os.path.dirname(path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write("\n")


def parse_blocks(raw: str) -> tuple[str, ...]:
    blocks = tuple(item.strip() for item in raw.split(",") if item.strip())
    allowed = {"tail", "origin", "interface"}
    unknown = [block for block in blocks if block not in allowed]
    if unknown:
        raise ValueError(f"unknown --blocks item(s): {', '.join(unknown)}")
    if not blocks:
        raise ValueError("--blocks must name at least one of tail,origin,interface")
    return blocks


def hook_report() -> HookReport:
    module_name = "validators.compactified_equations_twochart"
    try:
        module = importlib.import_module(module_name)
    except Exception as exc:  # pragma: no cover - exact import error is environment-specific.
        return HookReport(
            module=module_name,
            available=False,
            missing_hooks=REQUIRED_HOOKS,
            required_hooks=REQUIRED_HOOKS,
            import_error=f"{type(exc).__name__}: {exc}",
        )
    missing = tuple(name for name in REQUIRED_HOOKS if not callable(getattr(module, name, None)))
    return HookReport(
        module=module_name,
        available=not missing,
        missing_hooks=missing,
        required_hooks=REQUIRED_HOOKS,
        import_error="",
    )


def validate_input_schema(data: dict[str, Any], path: str) -> None:
    fmt = data.get("format")
    if fmt not in SUPPORTED_FORMATS:
        raise ValueError(
            f"{path} must be a two-chart profile JSON; got format={fmt!r}. "
            "Run tools/profile_project_twochart.py first."
        )
    if not isinstance(data.get("tail_chart"), dict):
        raise ValueError(f"{path} is missing tail_chart")
    if not isinstance(data.get("origin_chart"), dict):
        raise ValueError(f"{path} is missing origin_chart")


def validate_hard_gates(data: dict[str, Any], q2_policy: str) -> dict[str, Any]:
    if q2_policy != "zero":
        raise ValueError("hard-constrained two-chart Newton requires --q2-policy zero")
    tail_legality = data.get("tail_legality")
    if not isinstance(tail_legality, dict):
        raise ValueError("input profile is missing tail_legality report")
    if tail_legality.get("q2_policy") != "zero":
        raise ValueError(f"input tail_legality q2_policy must be zero; got {tail_legality.get('q2_policy')!r}")
    if tail_legality.get("all_ok") is not True:
        raise ValueError(f"tail_legality gate is not all_ok: status={tail_legality.get('status')!r}")
    return tail_legality


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be positive")
    return parsed


def positive_float(value: str) -> float:
    parsed = float(value)
    if parsed <= 0.0:
        raise argparse.ArgumentTypeError("must be positive")
    return parsed


def build_plan(args: argparse.Namespace, data: dict[str, Any], hooks: HookReport) -> dict[str, Any]:
    blocks = parse_blocks(args.blocks)
    tail_legality = validate_hard_gates(data, args.q2_policy)
    hard_newton_schema = data.get("hard_newton_schema", {})
    residual_blocks = []
    unknown_blocks = []
    if isinstance(hard_newton_schema, dict):
        residual_blocks = hard_newton_schema.get("residual_blocks", [])  # type: ignore[assignment]
        unknown_blocks = hard_newton_schema.get("unknown_blocks", [])  # type: ignore[assignment]

    return {
        "format": "twochart_newton_stage0_dryrun_v1",
        "status": STATUS,
        "refusal_status": MISSING_HOOK_STATUS if not hooks.available else "",
        "dry_run": True,
        "newton_executed": False,
        "optimization_faked": False,
        "input": args.input,
        "out": args.out,
        "source_profile": {
            "format": data.get("format"),
            "status": data.get("status"),
            "gamma": data.get("gamma"),
            "B": data.get("B"),
            "p": data.get("p"),
            "source_profile_json": data.get("source_profile_json"),
        },
        "requested_solver": {
            "blocks": list(blocks),
            "gamma_fixed": True,
            "B_fixed": True,
            "residual_kind": args.residual_kind,
            "q2_policy": args.q2_policy,
            "mortar_order": args.mortar_order,
            "max_iter": args.max_iter,
            "trust": args.trust,
            "lm_lambda": args.lm_lambda,
            "scan": args.scan,
        },
        "hard_constraints": {
            "q2_policy": "zero",
            "tail_legality_all_ok": tail_legality.get("all_ok"),
            "tail_legality_status": tail_legality.get("status"),
            "gamma_B_policy": "fixed_until_twochart_solver_is_implemented",
            "interface_policy": "hard rows, not hidden penalties",
            "no_coefficient_finite_difference_jacobian": True,
        },
        "tail_legality": tail_legality,
        "planned_unknown_blocks": unknown_blocks,
        "planned_residual_blocks": residual_blocks,
        "planned_stages": [
            {
                "name": "stage0",
                "active_blocks": list(blocks),
                "goal": "assemble hard-constrained origin/interface Newton system",
                "execution": "blocked_until_residual_jacobian_hooks_exist",
            }
        ],
        "required_validator_hooks": asdict(hooks),
        "refusal_reason": (
            "Real Newton is disabled until validators/compactified_equations_twochart.py "
            "provides callable residual/Jacobian hooks."
        )
        if not hooks.available
        else "",
        "diagnostic_vs_proof": "dry-run solver plan only; no interval proof and no coefficient update",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Two-chart profile JSON.")
    parser.add_argument("--out", required=True, help="Dry-run plan JSON to write.")
    parser.add_argument("--blocks", default="origin,interface", help="Comma list: tail,origin,interface.")
    parser.add_argument("--gamma-fixed", action="store_true", default=True, help="Accepted planned flag; enforced true.")
    parser.add_argument("--B-fixed", action="store_true", default=True, help="Accepted planned flag; enforced true.")
    parser.add_argument("--residual-kind", default="normalized-structural")
    parser.add_argument("--q2-policy", choices=("zero",), default="zero")
    parser.add_argument("--mortar-order", type=positive_int, default=4)
    parser.add_argument("--max-iter", type=positive_int, default=20)
    parser.add_argument("--trust", type=positive_float, default=0.05)
    parser.add_argument("--lm-lambda", type=positive_float, default=1e-8)
    parser.add_argument("--scan", default="standard,focused,secondary,origin,edge")
    args = parser.parse_args()

    data = load_json(args.input)
    validate_input_schema(data, args.input)
    hooks = hook_report()
    plan = build_plan(args, data, hooks)
    save_json(args.out, plan)

    print(f"input={args.input}")
    print(f"saved={args.out}")
    print(f"status={plan['status']}")
    print(f"newton_executed={plan['newton_executed']}")
    print(f"q2_policy={args.q2_policy}")
    print(f"tail_legality_all_ok={plan['hard_constraints']['tail_legality_all_ok']}")
    print(f"hook_module={hooks.module}")
    print(f"hook_available={hooks.available}")
    if not hooks.available:
        print(f"refusal_status={plan['refusal_status']}")
        print(f"missing_hooks={','.join(hooks.missing_hooks)}")


if __name__ == "__main__":
    main()
