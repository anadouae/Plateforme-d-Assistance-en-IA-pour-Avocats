#!/usr/bin/env python3
"""Compat : délègue à la source LexHub actuelle."""
from pathlib import Path
import runpy

TARGET = Path(__file__).resolve().parents[1] / "docs" / "livraison-encadrant-2026" / "generate_soutenance_pfa.py"
runpy.run_path(str(TARGET), run_name="__main__")
