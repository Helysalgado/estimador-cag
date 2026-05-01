#!/usr/bin/env python3
"""
Valida que el repositorio cumple la estructura mínima acordada (plantilla LIDR).
Ejecutar desde la raíz del proyecto: python scripts/validate_structure.py
"""

from __future__ import annotations

import sys
from pathlib import Path


REQUIRED_PATHS: tuple[str, ...] = (
    "app",
    "tests",
    ".dockerignore",
    ".env.example",
    ".gitignore",
    ".python-version",
    "Dockerfile",
    "docker-compose.yml",
    "pyproject.toml",
    "README.md",
    "scripts/validate_structure.py",
    "tests/__init__.py",
    "tests/conftest.py",
    "tests/test_health.py",
)


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    missing: list[str] = []

    for rel in REQUIRED_PATHS:
        path = root / rel
        if not path.exists():
            missing.append(rel)

    if missing:
        print("Estructura incompleta. Faltan rutas obligatorias:", file=sys.stderr)
        for m in missing:
            print(f"  - {m}", file=sys.stderr)
        return 1

    print("Estructura OK:", len(REQUIRED_PATHS), "rutas verificadas.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
