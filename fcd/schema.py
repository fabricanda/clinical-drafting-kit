"""Data models: the study synopsis (input) and the drafted section (Claude's structured output)."""
from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field


# ---------- Input: the study synopsis a clinical team fills in ----------

class Endpoint(BaseModel):
    id: str = Field(description="Stable ID, e.g. P1, S1")
    name: str
    timepoint: str
    type: Literal["primary", "key_secondary", "secondary", "exploratory", "safety"]


class Arm(BaseModel):
    id: str
    name: str
    dose: str
    regimen: str


class Visit(BaseModel):
    name: str
    week: float
    window_days: int = 0
    procedures: List[str]


class Synopsis(BaseModel):
    protocol_id: str
    title: str
    sponsor: str
    phase: str
    indication: str
    investigational_product: str
    mechanism: str
    rationale: str
    population: str
    age_min: int
    age_max: Optional[int] = None
    key_inclusion: List[str]
    key_exclusion: List[str]
    design: str
    arms: List[Arm]
    randomization_ratio: str
    blinding: str
    sample_size: int
    power_assumptions: str
    treatment_duration_weeks: int
    follow_up_weeks: int
    endpoints: List[Endpoint]
    visits: List[Visit]
    rescue_therapy: str
    safety_monitoring: str
    analysis_population: str
    primary_analysis: str
    multiplicity: str
    references: List[str] = []


# ---------- Output: one drafted protocol section ----------

class SourceLink(BaseModel):
    statement: str = Field(description="A short quote or paraphrase of one factual statement in the section text")
    source: str = Field(description="Synopsis field path it comes from (e.g. 'sample_size', 'endpoints[P1]', 'visits[Week 16]') or 'ASSUMPTION' if not in the synopsis")


class SectionDraft(BaseModel):
    section_number: str
    heading: str
    text: str = Field(description="Protocol text for this section, in Markdown. Use only facts in the synopsis; mark anything else [TBD].")
    sources: List[SourceLink] = Field(description="One entry per factual statement (numbers, doses, timepoints, criteria).")
    assumptions: List[str] = Field(description="Anything written that is not directly in the synopsis.")
    open_questions: List[str] = Field(description="Questions the clinical team must answer before this section can be final.")


# ---------- Review findings ----------

class Finding(BaseModel):
    severity: Literal["critical", "major", "minor"]
    sections: List[str]
    issue: str
    suggestion: str


class ReviewReport(BaseModel):
    findings: List[Finding]
