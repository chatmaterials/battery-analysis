#!/usr/bin/env python3

from __future__ import annotations

import re
from pathlib import Path


RY_TO_EV = 13.605693009
HARTREE_TO_EV = 27.211386018
BOHR_TO_ANG = 0.529177210903
ATOMIC_WEIGHTS = {
    "Li": 6.94,
    "Na": 22.99,
    "K": 39.098,
    "Mg": 24.305,
    "Ca": 40.078,
    "Al": 26.982,
    "Ti": 47.867,
    "V": 50.942,
    "Mn": 54.938,
    "Fe": 55.845,
    "Co": 58.933,
    "Ni": 58.693,
    "Cu": 63.546,
    "Zn": 65.38,
    "Si": 28.085,
    "P": 30.974,
    "S": 32.06,
    "O": 15.999,
    "F": 18.998,
    "C": 12.011,
}


def read_text(path: Path) -> str:
    return path.read_text(errors="ignore") if path.exists() else ""


def detect_backend(path: Path) -> str:
    root = path if path.is_dir() else path.parent
    names = {item.name for item in root.iterdir()} if root.is_dir() else set()
    if "OUTCAR" in names or "POSCAR" in names:
        return "vasp"
    if any(root.glob("*.in")) or any(root.glob("*.out")):
        return "qe"
    if any(root.glob("*.abi")) or any(root.glob("*.abo")):
        return "abinit"
    raise SystemExit(f"Could not detect backend from {path}")


def read_energy(path: Path) -> tuple[str, float]:
    backend = detect_backend(path)
    root = path if path.is_dir() else path.parent
    if backend == "vasp":
        text = read_text(root / "OUTCAR" if root.is_dir() else path)
        matches = re.findall(r"TOTEN\s*=\s*([\-0-9.Ee+]+)", text)
        if not matches:
            raise SystemExit(f"No TOTEN found for VASP path {path}")
        return backend, float(matches[-1])
    if backend == "qe":
        out_files = sorted(root.glob("*.out"))
        if not out_files:
            raise SystemExit(f"No QE output file found in {root}")
        text = read_text(out_files[0])
        matches = re.findall(r"!\s+total energy\s+=\s+([\-0-9.DdEe+]+)\s+Ry", text)
        if not matches:
            raise SystemExit(f"No total energy found for QE path {path}")
        return backend, float(matches[-1].replace("D", "e").replace("d", "e")) * RY_TO_EV
    out_file = root / "run.abo"
    if not out_file.exists():
        abo = sorted(root.glob("*.abo"))
        out_file = abo[0] if abo else out_file
    text = read_text(out_file)
    matches = re.findall(r"\betotal\s+([\-0-9.DdEe+]+)", text)
    if not matches:
        raise SystemExit(f"No etotal found for ABINIT path {path}")
    return backend, float(matches[-1].replace("D", "e").replace("d", "e")) * HARTREE_TO_EV


def volume(cell: list[list[float]]) -> float:
    a, b, c = cell
    return (
        a[0] * (b[1] * c[2] - b[2] * c[1])
        - a[1] * (b[0] * c[2] - b[2] * c[0])
        + a[2] * (b[0] * c[1] - b[1] * c[0])
    )


def read_structure(path: Path) -> tuple[str, float]:
    backend = detect_backend(path)
    root = path if path.is_dir() else path.parent
    if backend == "vasp":
        poscar = root / "POSCAR" if root.is_dir() else path
        lines = read_text(poscar).splitlines()
        scale = float(lines[1].split()[0])
        lattice = [[float(x) * scale for x in lines[i].split()] for i in range(2, 5)]
        return backend, volume(lattice)
    if backend == "qe":
        in_files = sorted(root.glob("*.in"))
        if not in_files:
            raise SystemExit(f"No QE input file found in {root}")
        lines = read_text(in_files[0]).splitlines()
        lattice = []
        for idx, line in enumerate(lines):
            if line.strip().upper().startswith("CELL_PARAMETERS"):
                lattice = [[float(x) for x in lines[idx + j + 1].split()[:3]] for j in range(3)]
                break
        if not lattice:
            raise SystemExit(f"No CELL_PARAMETERS block found in {in_files[0]}")
        return backend, volume(lattice)
    abi_files = sorted(root.glob("*.abi"))
    if not abi_files:
        raise SystemExit(f"No ABINIT input file found in {root}")
    text = read_text(abi_files[0])
    acell_match = re.search(r"acell\s+3\*([0-9.]+)", text)
    rprim_match = re.search(r"rprim\s+(.+?)xred", text, re.DOTALL)
    if not acell_match or not rprim_match:
        raise SystemExit(f"Could not parse acell/rprim in {abi_files[0]}")
    acell_bohr = float(acell_match.group(1))
    scale = acell_bohr * BOHR_TO_ANG
    raw = [line.split()[:3] for line in rprim_match.group(1).splitlines() if line.split()]
    lattice = [[float(x) * scale for x in row] for row in raw[:3]]
    return backend, volume(lattice)


def read_composition(path: Path) -> tuple[str, dict[str, int]]:
    backend = detect_backend(path)
    root = path if path.is_dir() else path.parent
    if backend == "vasp":
        poscar = root / "POSCAR" if root.is_dir() else path
        lines = read_text(poscar).splitlines()
        species = lines[5].split()
        counts = [int(x) for x in lines[6].split()]
        return backend, dict(zip(species, counts, strict=False))
    if backend == "qe":
        in_files = sorted(root.glob("*.in"))
        if not in_files:
            raise SystemExit(f"No QE input file found in {root}")
        species = []
        counts: dict[str, int] = {}
        lines = read_text(in_files[0]).splitlines()
        for idx, line in enumerate(lines):
            upper = line.strip().upper()
            if upper.startswith("ATOMIC_SPECIES"):
                j = idx + 1
                while j < len(lines) and lines[j].strip():
                    species.append(lines[j].split()[0])
                    j += 1
            if upper.startswith("ATOMIC_POSITIONS"):
                j = idx + 1
                while j < len(lines) and lines[j].strip():
                    label = lines[j].split()[0]
                    counts[label] = counts.get(label, 0) + 1
                    j += 1
                break
        return backend, {label: counts.get(label, 0) for label in species}
    abi_files = sorted(root.glob("*.abi"))
    if not abi_files:
        raise SystemExit(f"No ABINIT input file found in {root}")
    text = read_text(abi_files[0])
    znucl_match = re.search(r"^\s*znucl\s+(.+)$", text, re.MULTILINE)
    typat_match = re.search(r"^\s*typat\s+(.+)$", text, re.MULTILINE)
    if not znucl_match or not typat_match:
        raise SystemExit(f"Could not parse znucl/typat in {abi_files[0]}")
    z_values = [int(float(x)) for x in znucl_match.group(1).split()]
    symbol_map = {3: "Li", 8: "O", 11: "Na", 12: "Mg", 15: "P", 22: "Ti", 23: "V", 25: "Mn", 26: "Fe", 27: "Co", 28: "Ni"}
    species = [symbol_map.get(z, str(z)) for z in z_values]
    typats = [int(x) for x in typat_match.group(1).split()]
    counts = {species[idx - 1]: sum(1 for value in typats if value == idx) for idx in range(1, len(species) + 1)}
    return backend, counts


def infer_ion_change(host: Path, lithiated: Path, ion: str | None = None) -> tuple[str | None, int]:
    _, host_comp = read_composition(host)
    _, lith_comp = read_composition(lithiated)
    positive = {}
    for label in sorted(set(host_comp) | set(lith_comp)):
        delta = lith_comp.get(label, 0) - host_comp.get(label, 0)
        if delta > 0:
            positive[label] = delta
    if ion is not None:
        return ion, positive.get(ion, 0)
    if len(positive) == 1:
        label, delta = next(iter(positive.items()))
        return label, delta
    return None, 0


def formula_mass(composition: dict[str, int]) -> float | None:
    total = 0.0
    for label, count in composition.items():
        if label not in ATOMIC_WEIGHTS:
            return None
        total += ATOMIC_WEIGHTS[label] * count
    return total
