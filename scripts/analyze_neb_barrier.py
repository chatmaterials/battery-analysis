#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
from pathlib import Path

from battery_io import read_energy


def analyze(root: Path) -> dict[str, object]:
    image_dirs = sorted(path for path in root.iterdir() if path.is_dir() and path.name.isdigit())
    if not image_dirs:
        raise SystemExit("No numbered image directories were found")
    images = []
    for path in image_dirs:
        backend, energy = read_energy(path)
        images.append({"image": path.name, "backend": backend, "energy_eV": energy})
    reference = images[0]["energy_eV"]
    for image in images:
        image["relative_energy_eV"] = image["energy_eV"] - reference
    highest_rel = max(image["relative_energy_eV"] for image in images)
    reaction_energy = images[-1]["relative_energy_eV"]
    highest = max(images, key=lambda item: item["relative_energy_eV"])
    backends = sorted({image["backend"] for image in images})
    return {
        "path": str(root),
        "backends": backends,
        "images": images,
        "forward_barrier_eV": highest_rel,
        "reverse_barrier_eV": highest_rel - reaction_energy,
        "reaction_energy_eV": reaction_energy,
        "highest_image": highest["image"],
        "observations": ["Barrier and reaction energy estimated from image energies relative to the initial state."],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze a numbered NEB image set.")
    parser.add_argument("path", nargs="?", default=".")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    payload = analyze(Path(args.path).expanduser().resolve())
    if args.json:
        print(json.dumps(payload, indent=2))
        return
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
