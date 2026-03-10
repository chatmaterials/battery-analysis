#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
from pathlib import Path

from battery_io import density_from_formula_mass_and_volume, formula_mass, infer_ion_change, read_composition, read_energy, read_structure


FARADAY_MAH_PER_MOL = 26801.0


def analyze(
    host: Path,
    lithiated: Path,
    reference_energy: float,
    delta_ion: int | None = None,
    ion: str | None = None,
) -> dict[str, object]:
    backend_host, e_host = read_energy(host)
    backend_lithiated, e_lithiated = read_energy(lithiated)
    if backend_host != backend_lithiated:
        raise SystemExit("Host and lithiated states must use the same backend for direct comparison")
    _, host_comp = read_composition(host)
    inserted_species, inferred_delta = infer_ion_change(host, lithiated, ion)
    delta = delta_ion if delta_ion is not None else inferred_delta
    if delta <= 0:
        raise SystemExit("Could not determine a positive inserted-ion count; provide --delta-ion or a clearer host/lithiated pair")
    voltage = -(e_lithiated - e_host - delta * reference_energy) / delta
    host_mass = formula_mass(host_comp)
    capacity = FARADAY_MAH_PER_MOL * delta / host_mass if host_mass is not None and host_mass > 0.0 else None
    specific_energy = voltage * capacity if capacity is not None else None
    _, host_volume_A3 = read_structure(host)
    density = density_from_formula_mass_and_volume(host_mass, host_volume_A3)
    volumetric_energy = specific_energy * density if specific_energy is not None and density is not None else None
    if voltage < 1.0:
        voltage_class = "low-voltage"
    elif voltage <= 3.5:
        voltage_class = "working-window"
    else:
        voltage_class = "high-voltage"
    return {
        "backend": backend_host,
        "host": str(host),
        "lithiated": str(lithiated),
        "host_energy_eV": e_host,
        "lithiated_energy_eV": e_lithiated,
        "inserted_species": inserted_species,
        "reference_energy_per_ion_eV": reference_energy,
        "delta_ion": delta,
        "average_voltage_V": voltage,
        "host_formula_mass_g_mol": host_mass,
        "host_density_g_cm3": density,
        "theoretical_capacity_mAh_g": capacity,
        "specific_energy_Wh_kg": specific_energy,
        "volumetric_energy_Wh_L": volumetric_energy,
        "voltage_class": voltage_class,
        "observations": ["Average insertion voltage estimated from total-energy differences."],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Estimate an average insertion voltage from two states.")
    parser.add_argument("host")
    parser.add_argument("lithiated")
    parser.add_argument("--reference-energy", type=float, required=True)
    parser.add_argument("--delta-ion", type=int)
    parser.add_argument("--ion")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    payload = analyze(
        Path(args.host).expanduser().resolve(),
        Path(args.lithiated).expanduser().resolve(),
        args.reference_energy,
        args.delta_ion,
        args.ion,
    )
    if args.json:
        print(json.dumps(payload, indent=2))
        return
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
