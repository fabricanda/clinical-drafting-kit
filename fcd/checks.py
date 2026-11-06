"""Deterministic checks. These run with no model and catch the errors that matter most
in a regulated document: numbers with no source, endpoints that don't line up with the
visit schedule, doses or sample sizes that drift between sections.
"""
from __future__ import annotations

import json
import re
from typing import Dict, List

from .schema import Finding, SectionDraft, Synopsis
from .template import SECTIONS

NUM = re.compile(r"(?<![\w.])(\d+(?:\.\d+)?)(?![\w])")
WEEK = re.compile(r"[Ww]eek\s*(\d+(?:\.\d+)?)")
# Numbers that are structural, not facts (section refs, list numbering, ICH guideline ids).
IGNORE = {"1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "0"}
GUIDELINE = re.compile(r"\b(?:E\d+|M\d+|R\d+|E2A|21 CFR|Part)\s*\(?R?\d*\)?", re.I)


def _field_values(syn: Synopsis, fields: List[str]) -> str:
    d = syn.model_dump()
    return json.dumps({f: d.get(f) for f in fields})


def _numbers(text: str) -> set:
    text = GUIDELINE.sub(" ", text)
    text = re.sub(r"(?:Sections?|§)\s*\d+(?:\.\d+)*(?:\s*(?:and|,|-)\s*\d+(?:\.\d+)*)*", " ", text)  # cross-references
    text = re.sub(r"^\s*\d+(\.\d+)*[.)]\s", " ", text, flags=re.M)  # list numbering
    text = re.sub(r"\[\^?\d+\]", " ", text)
    return {n for n in NUM.findall(text) if n not in IGNORE}


def untraced_numbers(syn: Synopsis, d: SectionDraft) -> List[Finding]:
    sec = next((s for s in SECTIONS if s["number"] == d.section_number), None)
    allowed = _field_values(syn, sec["fields"] if sec else list(syn.model_dump()))
    whole = json.dumps(syn.model_dump())
    out = []
    assumed = " ".join(d.assumptions)
    for n in sorted(_numbers(d.text), key=float):
        if n in allowed:
            continue
        if n in assumed:
            continue  # declared as an assumption, which is the honest path
        sev = "minor" if n in whole else "major"
        where = "comes from a synopsis field this section is not meant to use" if n in whole else "is not in the synopsis and not declared as an assumption"
        out.append(Finding(severity=sev, sections=[d.section_number], issue=f"The number {n} {where}.",
                           suggestion="Trace it to the synopsis, move it to assumptions, or replace it with [TBD]."))
    return out


def endpoint_visit_alignment(syn: Synopsis) -> List[Finding]:
    weeks = {v.week for v in syn.visits}
    out = []
    for e in syn.endpoints:
        for w in WEEK.findall(e.timepoint):
            if float(w) not in weeks:
                out.append(Finding(severity="critical", sections=["1.3", "3"],
                                   issue=f"Endpoint {e.id} ({e.name}) is measured at Week {w}, but the Schedule of Activities has no Week {w} visit.",
                                   suggestion=f"Add a Week {w} visit or change the endpoint timepoint."))
    return out


def cross_section(syn: Synopsis, drafts: Dict[str, SectionDraft]) -> List[Finding]:
    out = []
    def has(num, needle):
        return num in drafts and needle.lower() in drafts[num].text.lower()

    for num in ("4", "10"):
        if num in drafts and not has(num, str(syn.sample_size)):
            out.append(Finding(severity="major", sections=[num],
                               issue=f"Section {num} does not state the planned sample size ({syn.sample_size}).",
                               suggestion="State the sample size exactly as in the synopsis."))
    if "6" in drafts:
        for a in syn.arms:
            if not has("6", a.dose):
                out.append(Finding(severity="critical", sections=["6"],
                                   issue=f"Section 6 does not state the dose for arm '{a.name}' as '{a.dose}'.",
                                   suggestion="Correct the dose to match the synopsis."))
    for e in syn.endpoints:
        if e.type in ("primary", "key_secondary"):
            for num in ("3", "10"):
                if num in drafts and not (has(num, e.name) or has(num, e.id)):
                    out.append(Finding(severity="major", sections=[num],
                                       issue=f"{e.type.replace('_', ' ').title()} endpoint '{e.name}' is not named in Section {num}.",
                                       suggestion="Name every primary and key secondary endpoint in both the objectives and the statistics section."))
    if "5" in drafts and not has("5", str(syn.age_min)):
        out.append(Finding(severity="major", sections=["5"], issue=f"Minimum age {syn.age_min} is missing from Section 5.",
                           suggestion="Add the age criterion."))
    return out


def source_hygiene(d: SectionDraft) -> List[Finding]:
    out = []
    n_assume = sum(1 for s in d.sources if s.source.strip().upper() == "ASSUMPTION")
    if d.sources and n_assume / len(d.sources) > 0.4:
        out.append(Finding(severity="minor", sections=[d.section_number],
                           issue=f"{n_assume} of {len(d.sources)} statements rest on assumptions, not the synopsis.",
                           suggestion="Have the clinical team confirm or supply these in the synopsis."))
    return out


def run_all(syn: Synopsis, drafts: List[SectionDraft]) -> List[Finding]:
    by = {d.section_number: d for d in drafts}
    findings = endpoint_visit_alignment(syn) + cross_section(syn, by)
    for d in drafts:
        findings += untraced_numbers(syn, d) + source_hygiene(d)
    order = {"critical": 0, "major": 1, "minor": 2}
    return sorted(findings, key=lambda f: order[f.severity])
