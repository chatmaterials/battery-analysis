#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
from pathlib import Path

from battery_io import read_energy


def analyze(host: Path, lithiated: Path, reference_energy: float, delta_ion: int = 1) -> dict[str, object]:
    backend_host, e_host = read_energy(host)
    backend_lithiated, e_lithiated = read_energy(lithiated)
    if backend_host != backend_lithiated:
        raise SystemExit("Host and lithiated states must use the same backend for direct comparison")
    voltage = -(e_lithiated - e_host - delta_ion * reference_energy) / delta_ion
    return {
        "backend": backend_host,
        "host": str(host),
        "lithiated": str(lithiated),
        "host_energy_eV": e_host,
        "lithiated_energy_eV": e_lithiated,
        "reference_energy_per_ion_eV": reference_energy,
        "delta_ion": delta_ion,
        "average_voltage_V": voltage,
        "observations": ["Average insertion voltage estimated from total-energy differences."],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Estimate an average insertion voltage from two states.")
    parser.add_argument("host")
    parser.add_argument("lithiated")
    parser.add_argument("--reference-energy", type=float, required=True)
    parser.add_argument("--delta-ion", type=int, default=1)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    payload = analyze(
        Path(args.host).expanduser().resolve(),
        Path(args.lithiated).expanduser().resolve(),
        args.reference_energy,
        args.delta_ion,
    )
    if args.json:
        print(json.dumps(payload, indent=2))
        return
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
