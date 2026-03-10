---
name: "battery-analysis"
description: "Use when the task is to analyze battery-relevant quantities from DFT results, including average insertion voltage, automatic inserted-ion counting, host-to-lithiated volume change, migration barriers from NEB images, specific and volumetric energy descriptors, mode-specific candidate ranking, and compact markdown reports from finished calculations. Supports VASP, QE, and ABINIT-style host and lithiated inputs."
---

# Battery Analysis

Use this skill for battery-material post-processing rather than generic workflow setup.

## When to use

- estimate average insertion voltage from two states
- infer the inserted ion and inserted-ion count from host and lithiated structures
- quantify structural or volume change upon insertion or extraction
- summarize migration barriers from NEB image sets
- derive compact gravimetric/volumetric energy and breathing descriptors for battery screening
- rank multiple battery candidates in balanced, stability, energy, or power modes
- write a compact battery-analysis report from existing calculations

The current scripts can read host and lithiated states from:

- VASP-like directories with `OUTCAR` and `POSCAR`
- QE-like directories with `.out` and `CELL_PARAMETERS`
- ABINIT-like directories with `.abo` and `.abi`

## Use the bundled helpers

- `scripts/analyze_insertion_voltage.py`
  Estimate an average insertion voltage and infer the inserted ion count when possible.
- `scripts/analyze_volume_change.py`
  Compare host and lithiated structures and compute the relative volume change and change per inserted ion.
- `scripts/analyze_neb_barrier.py`
  Estimate forward and reverse migration barriers from a numbered image set across VASP, QE, or ABINIT-style energies.
- `scripts/compare_battery_candidates.py`
  Rank battery candidates with a compact voltage-plus-volume-plus-barrier screening heuristic.
- `scripts/export_battery_report.py`
  Export a markdown battery-analysis report.

## Guardrails

- Do not claim experimental voltage agreement from two raw total energies alone.
- State the reference ion energy and stoichiometric change explicitly.
- Distinguish migration barriers from thermodynamic driving forces.
