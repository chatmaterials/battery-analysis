#!/usr/bin/env python3

from __future__ import annotations

import argparse
from pathlib import Path

from analyze_insertion_voltage import analyze as analyze_voltage
from analyze_neb_barrier import analyze as analyze_neb
from analyze_volume_change import analyze as analyze_volume


def screening_note(voltage: dict[str, object], volume: dict[str, object], neb: dict[str, object] | None) -> str:
    v = float(voltage["average_voltage_V"])
    expansion = abs(float(volume["relative_volume_change_percent"]))
    barrier = float(neb["forward_barrier_eV"]) if neb is not None else None
    if 2.0 <= v <= 4.5 and expansion <= 10.0 and (barrier is None or barrier <= 0.7):
        return "This case looks balanced for simple battery screening: voltage is in a typical working window, expansion is moderate, and migration is not excessively hindered."
    if v < 2.0:
        return "The estimated average voltage is low for many intercalation cathode screens, even if the structural metrics look reasonable."
    if v > 4.5:
        return "The estimated average voltage is high enough that electrolyte compatibility may become a practical concern."
    if expansion > 10.0:
        return "The relative volume change is large enough that structural breathing may become a concern during cycling."
    return "The thermodynamic and kinetic descriptors are mixed; additional voltage-composition points or migration paths would help refine the screening picture."


def render_markdown(voltage: dict[str, object], volume: dict[str, object], neb: dict[str, object] | None) -> str:
    lines = [
        "# Battery Analysis Report",
        "",
        "## Average Voltage",
        f"- Backend: `{voltage['backend']}`",
        f"- Average insertion voltage (V): `{voltage['average_voltage_V']:.4f}`",
        f"- Inserted species: `{voltage['inserted_species']}`",
        f"- Inserted ions per host cell: `{voltage['delta_ion']}`",
        f"- Host energy (eV): `{voltage['host_energy_eV']:.6f}`",
        f"- Lithiated energy (eV): `{voltage['lithiated_energy_eV']:.6f}`",
        f"- Theoretical capacity (mAh/g): `{voltage['theoretical_capacity_mAh_g']:.2f}`" if voltage["theoretical_capacity_mAh_g"] is not None else "- Theoretical capacity (mAh/g): `n/a`",
        "",
        "## Volume Change",
        f"- Initial volume (A^3): `{volume['volume_initial_A3']:.4f}`",
        f"- Final volume (A^3): `{volume['volume_final_A3']:.4f}`",
        f"- Relative volume change (%): `{volume['relative_volume_change_percent']:.4f}`",
        f"- Volume change per inserted ion (A^3): `{volume['volume_change_per_inserted_ion_A3']:.4f}`" if volume["volume_change_per_inserted_ion_A3"] is not None else "- Volume change per inserted ion (A^3): `n/a`",
    ]
    if neb is not None:
        lines.extend(
            [
                "",
                "## Migration Barrier",
                f"- Parsed backends: `{', '.join(neb['backends'])}`",
                f"- Forward barrier (eV): `{neb['forward_barrier_eV']:.4f}`",
                f"- Reverse barrier (eV): `{neb['reverse_barrier_eV']:.4f}`",
                f"- Reaction energy (eV): `{neb['reaction_energy_eV']:.4f}`",
                f"- Highest image: `{neb['highest_image']}`",
            ]
        )
    lines.extend(["", "## Screening Note", f"- {screening_note(voltage, volume, neb)}"])
    return "\n".join(lines).rstrip() + "\n"


def default_output(source: Path) -> Path:
    return source / "BATTERY_REPORT.md" if source.is_dir() else source.parent / "BATTERY_REPORT.md"


def main() -> None:
    parser = argparse.ArgumentParser(description="Export a markdown battery analysis report.")
    parser.add_argument("host")
    parser.add_argument("lithiated")
    parser.add_argument("--reference-energy", type=float, required=True)
    parser.add_argument("--delta-ion", type=int, default=1)
    parser.add_argument("--neb-path")
    parser.add_argument("--output")
    args = parser.parse_args()

    host = Path(args.host).expanduser().resolve()
    lithiated = Path(args.lithiated).expanduser().resolve()
    voltage = analyze_voltage(host, lithiated, args.reference_energy, args.delta_ion)
    volume = analyze_volume(host, lithiated)
    neb = analyze_neb(Path(args.neb_path).expanduser().resolve()) if args.neb_path else None
    output = Path(args.output).expanduser().resolve() if args.output else default_output(host.parent)
    output.write_text(render_markdown(voltage, volume, neb))
    print(output)


if __name__ == "__main__":
    main()
