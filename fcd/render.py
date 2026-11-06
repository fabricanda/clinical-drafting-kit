"""Render the draft protocol to Markdown and Word, with the traceability and review appendix."""
from __future__ import annotations

import datetime as dt
from typing import Dict, List

from .schema import Finding, SectionDraft, Synopsis


def soa_markdown(syn: Synopsis) -> str:
    """Schedule of Activities, built straight from the synopsis. No model touches it."""
    procs: List[str] = []
    for v in syn.visits:
        for p in v.procedures:
            if p not in procs:
                procs.append(p)
    head = "| Procedure | " + " | ".join(f"{v.name} (Wk {v.week:g}{', ±' + str(v.window_days) + 'd' if v.window_days else ''})" for v in syn.visits) + " |"
    sep = "|---|" + "---|" * len(syn.visits)
    rows = [f"| {p} | " + " | ".join("X" if p in v.procedures else "" for v in syn.visits) + " |" for p in procs]
    return "\n".join([head, sep] + rows)


def status_line(approvals: Dict[str, dict], drafts: List[SectionDraft]) -> str:
    ok = [d.section_number for d in drafts if approvals.get(d.section_number, {}).get("status") == "approved"]
    if len(ok) == len(drafts):
        return "STATUS: All sections approved by a named reviewer."
    return f"STATUS: DRAFT, NOT APPROVED ({len(ok)} of {len(drafts)} sections signed off). Not for use."


def to_markdown(syn: Synopsis, drafts: List[SectionDraft], findings: List[Finding],
                approvals: Dict[str, dict], model_label: str) -> str:
    L = [f"# {syn.title}", "", f"**Protocol ID:** {syn.protocol_id}  ", f"**Sponsor:** {syn.sponsor}  ",
         f"**Phase:** {syn.phase}  ", f"**Generated:** {dt.date.today().isoformat()} by the Fabricanda Clinical Drafting Kit ({model_label})", "",
         f"> {status_line(approvals, drafts)}", "",
         "> Drafting aid output for review by qualified professionals. Not validated for GxP use; not Part 11 compliant. See DISCLAIMER.md.", "",
         "## 1.3 Schedule of Activities", "", "*Built directly from the synopsis visit table.*", "", soa_markdown(syn), ""]
    for d in drafts:
        L += [f"## {d.section_number} {d.heading}", "", d.text, ""]
    L += ["---", "## Appendix A. Review findings", ""]
    if not findings:
        L.append("No findings.")
    for f in findings:
        L.append(f"- **{f.severity.upper()}** (Sections {', '.join(f.sections)}): {f.issue} *Fix:* {f.suggestion}")
    L += ["", "## Appendix B. Source traceability", "", "| Section | Statement | Source |", "|---|---|---|"]
    for d in drafts:
        for s in d.sources:
            L.append(f"| {d.section_number} | {s.statement.replace('|', '/')} | {s.source} |")
    L += ["", "## Appendix C. Assumptions and open questions", ""]
    for d in drafts:
        if d.assumptions or d.open_questions:
            L.append(f"**Section {d.section_number}**")
            L += [f"- Assumption: {a}" for a in d.assumptions]
            L += [f"- Open question: {q}" for q in d.open_questions]
            L.append("")
    L += ["## Appendix D. Sign-off log", "", "| Section | Status | Reviewer | Date |", "|---|---|---|---|"]
    for d in drafts:
        a = approvals.get(d.section_number, {})
        L.append(f"| {d.section_number} {d.heading} | {a.get('status', 'pending')} | {a.get('by', '')} | {a.get('date', '')} |")
    return "\n".join(L) + "\n"


def to_docx(md_text: str, path: str) -> None:
    """Minimal Markdown-to-Word: headings, paragraphs, bullets, tables."""
    from docx import Document
    from docx.shared import Pt

    doc = Document()
    doc.styles["Normal"].font.size = Pt(10)
    lines = md_text.splitlines()
    i = 0
    while i < len(lines):
        ln = lines[i]
        if ln.startswith("|"):
            block = []
            while i < len(lines) and lines[i].startswith("|"):
                if not set(lines[i].replace("|", "").strip()) <= set("-: "):
                    block.append([c.strip() for c in lines[i].strip("|").split("|")])
                i += 1
            t = doc.add_table(rows=len(block), cols=len(block[0]))
            t.style = "Table Grid"
            for r, row in enumerate(block):
                for c, val in enumerate(row[: len(block[0])]):
                    t.cell(r, c).text = val.replace("**", "")
            continue
        if ln.startswith("# "):
            doc.add_heading(ln[2:], 0)
        elif ln.startswith("## "):
            doc.add_heading(ln[3:], 1)
        elif ln.startswith("- "):
            doc.add_paragraph(ln[2:].replace("**", "").replace("*", ""), style="List Bullet")
        elif ln.startswith("> "):
            p = doc.add_paragraph()
            p.add_run(ln[2:]).bold = True
        elif ln.strip() and ln.strip() != "---":
            doc.add_paragraph(ln.replace("**", "").replace("*", ""))
        i += 1
    doc.save(path)
