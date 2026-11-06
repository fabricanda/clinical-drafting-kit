"""Offline mode: builds plain template drafts from the synopsis with no model call.

Use it to test the pipeline (checks, sign-off, export) without an API key, or as a
fallback if the network fails mid-demo. The text is deliberately plain; the live
mode is where the writing quality comes from.
"""
from __future__ import annotations

from typing import List

from .schema import ReviewReport, SectionDraft, SourceLink, Synopsis


def _s(stmt, src):
    return SourceLink(statement=stmt, source=src)


def draft_section(syn: Synopsis, section: dict, prior) -> SectionDraft:
    n = section["number"]
    arms = "; ".join(f"{a.name}: {a.dose} {a.regimen}" for a in syn.arms)
    eps = [e for e in syn.endpoints]
    if n == "2":
        text = (f"{syn.indication}. {syn.rationale}\n\n{syn.investigational_product} is {syn.mechanism}.\n\n"
                "Benefit/risk: [TBD: summary of nonclinical and Phase 2 safety].")
        src = [_s(syn.investigational_product, "investigational_product"), _s(syn.mechanism, "mechanism")]
        oq = ["Provide the Phase 2 efficacy and safety summary for the benefit/risk section."]
    elif n == "3":
        rows = "\n".join(f"| {e.type.replace('_', ' ')} | {e.id} | {e.name} | {e.timepoint} |" for e in eps)
        text = ("| Category | ID | Endpoint | Timepoint |\n|---|---|---|---|\n" + rows +
                f"\n\nEstimand for primary endpoints: {syn.population}; intercurrent event of rescue therapy "
                f"({syn.rescue_therapy}) handled as non-response (composite strategy).")
        src = [_s(e.name, f"endpoints[{e.id}]") for e in eps]
        oq = []
    elif n == "4":
        text = (f"{syn.design}. Arms: {arms}. Randomization {syn.randomization_ratio}; {syn.blinding}. "
                f"Treatment period {syn.treatment_duration_weeks} weeks with {syn.follow_up_weeks}-week follow-up. "
                f"Approximately {syn.sample_size} participants will be randomized.")
        src = [_s(str(syn.sample_size), "sample_size"), _s(syn.randomization_ratio, "randomization_ratio")]
        oq = ["Confirm the dose-selection rationale from Phase 2."]
    elif n == "5":
        inc = "\n".join(f"{i}. {c}" for i, c in enumerate(syn.key_inclusion, 1))
        exc = "\n".join(f"{i}. {c}" for i, c in enumerate(syn.key_exclusion, 1))
        age = f"Aged {syn.age_min} years or older" + (f" and up to {syn.age_max}" if syn.age_max else "")
        text = f"Population: {syn.population}. {age}.\n\n**Inclusion**\n{inc}\n\n**Exclusion**\n{exc}"
        src = [_s(f"age {syn.age_min}", "age_min")]
        oq = ["Contraception and pregnancy-testing criteria are not in the synopsis."]
    elif n == "6":
        text = f"{syn.investigational_product}. {arms}. {syn.blinding}. Rescue therapy: {syn.rescue_therapy}."
        src = [_s(a.dose, f"arms[{a.id}]") for a in syn.arms]
        oq = ["Drug supply, packaging and labeling details."]
    elif n == "8":
        text = "Efficacy assessments: " + "; ".join(f"{e.name} at {e.timepoint}" for e in eps) + \
               f". Safety: {syn.safety_monitoring}. Timing per the Schedule of Activities (Section 1.3)."
        src = [_s(e.name, f"endpoints[{e.id}]") for e in eps]
        oq = []
    elif n == "9":
        text = (f"AEs collected from consent through end of follow-up. SAEs reported to the sponsor within 24 hours. "
                f"Product-specific monitoring: {syn.safety_monitoring}.")
        src = [_s("24 hours", "ASSUMPTION")]
        oq = []
    else:  # 10
        prim = ", ".join(e.name for e in eps if e.type in ("primary", "key_secondary"))
        text = (f"Sample size: {syn.sample_size} participants. {syn.power_assumptions}. Analysis set: {syn.analysis_population}. "
                f"Primary analysis: {syn.primary_analysis}. Multiplicity: {syn.multiplicity}. Endpoints tested: {prim}.")
        src = [_s(str(syn.sample_size), "sample_size")]
        oq = []
    assumptions = ["SAE reporting within 24 hours per ICH E2A practice."] if n == "9" else []
    return SectionDraft(section_number=n, heading=section["heading"], text=text, sources=src,
                        assumptions=assumptions, open_questions=oq)


def review(syn, drafts, soa_md) -> ReviewReport:
    return ReviewReport(findings=[])
