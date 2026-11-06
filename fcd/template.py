"""Loads document section specs from YAML (fcd/specs/*.yaml).

A document type is a YAML spec plus a check module. The spec says, per section, which
study fields the drafter may use and what the section must contain. Keeping the field
list narrow is what makes the source-traceability check meaningful.
"""
from __future__ import annotations

import pathlib
from typing import Dict, List

import yaml

SPEC_DIR = pathlib.Path(__file__).parent / "specs"


def load_spec(name: str = "protocol_m11") -> Dict:
    path = pathlib.Path(name)
    if not path.suffix:
        path = SPEC_DIR / f"{name}.yaml"
    return yaml.safe_load(path.read_text())


def sections(name: str = "protocol_m11") -> List[Dict]:
    return load_spec(name)["sections"]


SECTIONS = sections()
