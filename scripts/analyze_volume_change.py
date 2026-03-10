#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
from pathlib import Path

from battery_io import infer_ion_change, read_structure


def analyze(initial: Path, final: Path) -> dict[str, object]:
    backend_a, vol_a = read_structure(initial)
    backend_b, vol_b = read_structure(final)
    if backend_a != backend_b:
        raise SystemExit("Initial and final structures must use the same backend for direct comparison")
    inserted_species, delta = infer_ion_change(initial, final)
    change = (vol_b - vol_a) / vol_a * 100.0
    return {
        "backend": backend_a,
        "initial": str(initial),
        "final": str(final),
        "volume_initial_A3": vol_a,
        "volume_final_A3": vol_b,
        "relative_volume_change_percent": change,
        "inserted_species": inserted_species,
        "delta_ion": delta,
        "volume_change_per_inserted_ion_A3": (vol_b - vol_a) / delta if delta > 0 else None,
        "observations": ["Volume change estimated from the lattice vectors in the two structures."],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare the volume of two POSCAR-like structures.")
    parser.add_argument("initial")
    parser.add_argument("final")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    payload = analyze(Path(args.initial).expanduser().resolve(), Path(args.final).expanduser().resolve())
    if args.json:
        print(json.dumps(payload, indent=2))
        return
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
