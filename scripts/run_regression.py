#!/usr/bin/env python3

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, *args], cwd=ROOT, text=True, capture_output=True, check=True)


def run_json(*args: str):
    return json.loads(run(*args).stdout)


def ensure(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    voltage = run_json("scripts/analyze_insertion_voltage.py", "fixtures/battery/host", "fixtures/battery/lithiated", "--reference-energy", "-1.50", "--json")
    ensure(abs(voltage["average_voltage_V"] - 1.0) < 1e-6, "battery-analysis should parse the average insertion voltage")
    volume = run_json("scripts/analyze_volume_change.py", "fixtures/battery/host/POSCAR", "fixtures/battery/lithiated/POSCAR", "--json")
    ensure(volume["relative_volume_change_percent"] > 0, "battery-analysis should detect positive volume expansion")
    qe_voltage = run_json("scripts/analyze_insertion_voltage.py", "fixtures/qe/host", "fixtures/qe/lithiated", "--reference-energy", "-1.50", "--json")
    ensure(abs(qe_voltage["average_voltage_V"] - 1.0) < 1e-6, "battery-analysis should parse a QE-based average insertion voltage")
    abinit_voltage = run_json("scripts/analyze_insertion_voltage.py", "fixtures/abinit/host", "fixtures/abinit/lithiated", "--reference-energy", "-1.50", "--json")
    ensure(abs(abinit_voltage["average_voltage_V"] - 1.0) < 1e-4, "battery-analysis should parse an ABINIT-based average insertion voltage")
    qe_volume = run_json("scripts/analyze_volume_change.py", "fixtures/qe/host", "fixtures/qe/lithiated", "--json")
    ensure(qe_volume["relative_volume_change_percent"] > 0, "battery-analysis should detect positive QE volume expansion")
    abinit_volume = run_json("scripts/analyze_volume_change.py", "fixtures/abinit/host", "fixtures/abinit/lithiated", "--json")
    ensure(abinit_volume["relative_volume_change_percent"] > 0, "battery-analysis should detect positive ABINIT volume expansion")
    neb = run_json("scripts/analyze_neb_barrier.py", "fixtures/neb", "--json")
    ensure(abs(neb["forward_barrier_eV"] - 0.7) < 1e-6, "battery-analysis should parse the forward NEB barrier")
    ensure(neb["highest_image"] == "02", "battery-analysis should identify the highest-energy image")
    temp_dir = Path(tempfile.mkdtemp(prefix="battery-analysis-report-"))
    try:
        report_path = Path(
            run(
                "scripts/export_battery_report.py",
                "fixtures/battery/host",
                "fixtures/battery/lithiated",
                "--reference-energy",
                "-1.50",
                "--neb-path",
                "fixtures/neb",
                "--output",
                str(temp_dir / "BATTERY_REPORT.md"),
            ).stdout.strip()
        )
        report_text = report_path.read_text()
        ensure("# Battery Analysis Report" in report_text, "battery report should have a heading")
        ensure("## Average Voltage" in report_text and "## Migration Barrier" in report_text, "battery report should include voltage and barrier sections")
    finally:
        shutil.rmtree(temp_dir)
    print("battery-analysis regression passed")


if __name__ == "__main__":
    main()
