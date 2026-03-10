# battery-analysis

Standalone skill for battery-relevant DFT result analysis.

Supports VASP, QE, and ABINIT-style host/lithiated inputs for voltage and volume analysis.

## Install

```bash
npx skills add chatmaterials/battery-analysis -g -y
```

## Local Validation

```bash
python3 -m py_compile scripts/*.py
npx skills add . --list
python3 scripts/analyze_insertion_voltage.py fixtures/battery/host fixtures/battery/lithiated --reference-energy -1.50 --json
python3 scripts/analyze_insertion_voltage.py fixtures/qe/host fixtures/qe/lithiated --reference-energy -1.50 --json
python3 scripts/analyze_insertion_voltage.py fixtures/abinit/host fixtures/abinit/lithiated --reference-energy -1.50 --json
python3 scripts/analyze_volume_change.py fixtures/battery/host/POSCAR fixtures/battery/lithiated/POSCAR --json
python3 scripts/analyze_neb_barrier.py fixtures/neb --json
python3 scripts/export_battery_report.py fixtures/battery/host fixtures/battery/lithiated --reference-energy -1.50 --neb-path fixtures/neb
python3 scripts/run_regression.py
```
