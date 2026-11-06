"""Prompts and task builders shared by every provider. Plain text, so any model can use them."""
from __future__ import annotations

import json
from typing import List

from .schema import SectionDraft, Synopsis

SYSTEM = """You are a senior clinical protocol writer working for a sponsor's clinical development team.
You draft one section of a clinical trial protocol at a time, following the ICH M11 structured protocol
layout and ICH E6(R3), E8(R1) and E9(R1) principles.

Rules:
1. Use only facts stated in the study synopsis. Never invent numbers, doses, timepoints, criteria or results.
2. If the section needs something the synopsis does not give, write [TBD: what is needed] in the text and
   add it to open_questions.
3. Anything you add that is standard practice but not in the synopsis goes in assumptions.
4. Every factual statement (number, dose, timepoint, criterion, endpoint) gets an entry in sources that
   names the synopsis field it came from, or ASSUMPTION.
5. Stay consistent with the sections already drafted. Do not restate them.
6. Write plainly, in the register of a regulatory document. No marketing language."""

REVIEW_SYSTEM = """You are a protocol quality reviewer (medical writing QC plus a biostatistician's eye).
Find inconsistencies across sections and against the synopsis: endpoints, timepoints, doses, sample size,
estimands vs analysis, population vs criteria, visit timing vs endpoint timing, blinding, rescue therapy handling.
Report only real problems, each with the sections involved and a concrete fix. Do not report style issues."""


def synopsis_text(syn: Synopsis) -> str:
    return "STUDY SYNOPSIS (source of truth):\n" + json.dumps(syn.model_dump(), indent=2)


def section_task(section: dict, prior: List[SectionDraft]) -> str:
    prior_txt = "\n\n".join(f"## {d.section_number} {d.heading}\n{d.text}" for d in prior) or "(none yet)"
    return (
        f"Draft Section {section['number']} '{section['heading']}'.\n"
        f"Synopsis fields you may use: {', '.join(section['fields'])}.\n"
        f"Section guidance: {section['guidance']}\n\n"
        f"Sections already drafted (stay consistent):\n{prior_txt}"
    )


def review_task(drafts: List[SectionDraft], soa_md: str) -> str:
    body = "\n\n".join(f"## {d.section_number} {d.heading}\n{d.text}" for d in drafts)
    return (f"Schedule of Activities (Section 1.3):\n{soa_md}\n\nDraft protocol sections:\n{body}\n\n"
            "Review for cross-section inconsistencies.")
