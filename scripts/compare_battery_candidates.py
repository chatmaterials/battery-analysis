#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
from pathlib import Path

from analyze_insertion_voltage import analyze as analyze_voltage
from analyze_neb_barrier import analyze as analyze_neb
from analyze_volume_change import analyze as analyze_volume


def analyze_case(
    root: Path,
    reference_energy: float,
    voltage_min: float,
    voltage_max: float,
    max_expansion_percent: float,
    max_barrier_eV: float,
    ion: str | None,
) -> dict[str, object]:
    host = root / "host"
    lithiated = root / "lithiated"
    neb = root / "neb"
    voltage = analyze_voltage(host, lithiated, reference_energy, ion=ion)
    volume = analyze_volume(host, lithiated)
    neb_payload = analyze_neb(neb) if neb.exists() else None
    value = float(voltage["average_voltage_V"])
    if value < voltage_min:
        voltage_penalty = voltage_min - value
    elif value > voltage_max:
        voltage_penalty = value - voltage_max
    else:
        voltage_penalty = 0.0
    expansion_penalty = max(0.0, abs(float(volume["relative_volume_change_percent"])) - max_expansion_percent) / 10.0
    barrier_penalty = max(0.0, float(neb_payload["forward_barrier_eV"]) - max_barrier_eV) if neb_payload is not None else 0.25
    score = voltage_penalty + expansion_penalty + barrier_penalty
    return {
        "case": root.name,
        "path": str(root),
        "backend": voltage["backend"],
        "inserted_species": voltage["inserted_species"],
        "average_voltage_V": voltage["average_voltage_V"],
        "theoretical_capacity_mAh_g": voltage["theoretical_capacity_mAh_g"],
        "relative_volume_change_percent": volume["relative_volume_change_percent"],
        "forward_barrier_eV": neb_payload["forward_barrier_eV"] if neb_payload is not None else None,
        "voltage_penalty": voltage_penalty,
        "expansion_penalty": expansion_penalty,
        "barrier_penalty": barrier_penalty,
        "screening_score": score,
    }


def analyze_cases(
    roots: list[Path],
    reference_energy: float,
    voltage_min: float,
    voltage_max: float,
    max_expansion_percent: float,
    max_barrier_eV: float,
    ion: str | None,
) -> dict[str, object]:
    cases = [
        analyze_case(root, reference_energy, voltage_min, voltage_max, max_expansion_percent, max_barrier_eV, ion)
        for root in roots
    ]
    ranked = sorted(cases, key=lambda item: item["screening_score"])
    return {
        "target_voltage_window_V": [voltage_min, voltage_max],
        "max_expansion_percent": max_expansion_percent,
        "max_barrier_eV": max_barrier_eV,
        "ranking_basis": "screening_score = voltage_penalty + expansion_penalty + barrier_penalty",
        "cases": ranked,
        "best_case": ranked[0]["case"] if ranked else None,
        "observations": [
            "This is a compact battery-screening heuristic intended for triage, not a full voltage profile or kinetic map."
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Rank battery candidates with a compact voltage-plus-volume-plus-barrier heuristic.")
    parser.add_argument("paths", nargs="+")
    parser.add_argument("--reference-energy", type=float, required=True)
    parser.add_argument("--voltage-min", type=float, default=2.0)
    parser.add_argument("--voltage-max", type=float, default=4.5)
    parser.add_argument("--max-expansion-percent", type=float, default=10.0)
    parser.add_argument("--max-barrier", type=float, default=0.7)
    parser.add_argument("--ion")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    payload = analyze_cases(
        [Path(path).expanduser().resolve() for path in args.paths],
        args.reference_energy,
        args.voltage_min,
        args.voltage_max,
        args.max_expansion_percent,
        args.max_barrier,
        args.ion,
    )
    if args.json:
        print(json.dumps(payload, indent=2))
        return
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
