#!/usr/bin/env python3

from __future__ import annotations

import argparse
from pathlib import Path

from analyze_insertion_voltage import analyze as analyze_voltage
from analyze_neb_barrier import analyze as analyze_neb
from analyze_volume_change import analyze as analyze_volume


def render_markdown(voltage: dict[str, object], volume: dict[str, object], neb: dict[str, object] | None) -> str:
    lines = [
        "# Battery Analysis Report",
        "",
        "## Average Voltage",
        f"- Average insertion voltage (V): `{voltage['average_voltage_V']:.4f}`",
        f"- Host energy (eV): `{voltage['host_energy_eV']:.6f}`",
        f"- Lithiated energy (eV): `{voltage['lithiated_energy_eV']:.6f}`",
        "",
        "## Volume Change",
        f"- Initial volume (A^3): `{volume['volume_initial_A3']:.4f}`",
        f"- Final volume (A^3): `{volume['volume_final_A3']:.4f}`",
        f"- Relative volume change (%): `{volume['relative_volume_change_percent']:.4f}`",
    ]
    if neb is not None:
        lines.extend(
            [
                "",
                "## Migration Barrier",
                f"- Forward barrier (eV): `{neb['forward_barrier_eV']:.4f}`",
                f"- Reverse barrier (eV): `{neb['reverse_barrier_eV']:.4f}`",
                f"- Reaction energy (eV): `{neb['reaction_energy_eV']:.4f}`",
                f"- Highest image: `{neb['highest_image']}`",
            ]
        )
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
