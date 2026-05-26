#!/usr/bin/env python3
"""Replay accepted coordinate-search moves from a minimax log.

The long coordinate searches only write the seed at normal completion. This
helper reconstructs an intermediate candidate by replaying ``accept`` lines
from a log produced by ``tools/profile_minimax_coordinate.py``.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass


ACCEPT_RE = re.compile(
    r"^iter=(?P<iter>\d+) accept "
    r"(?P<key>[A-Za-z0-9_]+)\[(?P<i>-?\d+),(?P<j>-?\d+)\] "
    r"delta=(?P<delta>[-+0-9.eE]+) value=(?P<value>[-+0-9.eE]+) "
    r"(?P<metrics>.*)$"
)


@dataclass(frozen=True)
class Move:
    iteration: int
    key: str
    i: int
    j: int
    delta: float
    value: float
    metrics: str


def load_data(path: str) -> dict[str, object]:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def coeff_map(data: dict[str, object], key: str) -> dict[tuple[int, int], float]:
    raw = data.get(key, [])
    if not isinstance(raw, list):
        raise ValueError(f"{key} must be a list")
    values: dict[tuple[int, int], float] = {}
    for item in raw:
        if not isinstance(item, list) or len(item) != 3:
            raise ValueError(f"bad coefficient entry in {key}: {item!r}")
        values[(int(item[0]), int(item[1]))] = float(item[2])
    return values


def write_coeff_map(
    data: dict[str, object],
    key: str,
    values: dict[tuple[int, int], float],
) -> None:
    data[key] = [[i, j, values[(i, j)]] for i, j in sorted(values)]


def parse_moves(path: str) -> list[Move]:
    moves: list[Move] = []
    with open(path, "r", encoding="utf-8") as fh:
        for raw_line in fh:
            line = raw_line.strip()
            match = ACCEPT_RE.match(line)
            if match is None:
                continue
            moves.append(
                Move(
                    iteration=int(match.group("iter")),
                    key=match.group("key"),
                    i=int(match.group("i")),
                    j=int(match.group("j")),
                    delta=float(match.group("delta")),
                    value=float(match.group("value")),
                    metrics=match.group("metrics"),
                )
            )
    return moves


def replay_moves(data: dict[str, object], moves: list[Move]) -> None:
    by_key: dict[str, dict[tuple[int, int], float]] = {}
    for move in moves:
        values = by_key.setdefault(move.key, coeff_map(data, move.key))
        if (move.i, move.j) not in values:
            raise ValueError(f"log references missing coefficient {move.key}[{move.i},{move.j}]")
        values[(move.i, move.j)] = move.value
    for key, values in by_key.items():
        write_coeff_map(data, key, values)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed-json", required=True)
    parser.add_argument("--log", required=True)
    parser.add_argument("--save-json", required=True)
    args = parser.parse_args()

    data = load_data(args.seed_json)
    moves = parse_moves(args.log)
    replay_moves(data, moves)
    data["evidence"] = {
        "status": "approximate_non_validated_minimax_log_replay",
        "source": args.seed_json,
        "log": args.log,
        "accepted_moves": len(moves),
        "last_iteration": moves[-1].iteration if moves else None,
        "last_metrics": moves[-1].metrics if moves else "",
        "note": "Partial replay of accepted moves; validate independently before use.",
    }
    with open(args.save_json, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print(f"accepted_moves={len(moves)}")
    if moves:
        print(f"last_iteration={moves[-1].iteration}")
        print(moves[-1].metrics)
    print(f"saved seed json: {args.save_json}")


if __name__ == "__main__":
    main()
