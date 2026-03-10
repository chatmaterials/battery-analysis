#!/usr/bin/env python3

from __future__ import annotations

import re
from pathlib import Path


RY_TO_EV = 13.605693009
HARTREE_TO_EV = 27.211386018
BOHR_TO_ANG = 0.529177210903


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
