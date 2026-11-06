"""fcd: Fabricanda clinical drafting kit. Draft a protocol from a study synopsis, with checks and human sign-off.

  fcd draft examples/exm101_ad_ph3/study.yaml --out out/        # live (needs ANTHROPIC_API_KEY)
  fcd draft examples/exm101_ad_ph3/study.yaml --out out/ --offline
  fcd check  --out out/ [--inject-error]
  fcd approve 5 --by "Jane Reviewer" --out out/
  fcd export --out out/
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import sys
import time

import yaml

from . import checks, render
from .schema import Finding, ReviewReport, SectionDraft, Synopsis
from .template import SECTIONS


def _load_syn(path) -> Synopsis:
    return Synopsis.model_validate(yaml.safe_load(pathlib.Path(path).read_text()))


def _state(out: pathlib.Path):
    st = json.loads((out / "state.json").read_text())
    syn = Synopsis.model_validate(st["synopsis"])
    drafts = [SectionDraft.model_validate(d) for d in st["drafts"]]
    return st, syn, drafts


def _save(out, st):
    (out / "state.json").write_text(json.dumps(st, indent=2))


def _render(out: pathlib.Path, st, syn, drafts, findings):
    md = render.to_markdown(syn, drafts, findings, st.get("approvals", {}), st.get("model", ""))
    (out / "protocol_draft.md").write_text(md)
    render.to_docx(md, str(out / "protocol_draft.docx"))
    return md


def _print_findings(findings):
    if not findings:
        print("  No findings.")
    for f in findings:
        print(f"  [{f.severity.upper():8}] §{','.join(f.sections)}: {f.issue}")


def cmd_draft(a):
    out = pathlib.Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    syn = _load_syn(a.synopsis)
    if a.offline:
        from . import offline as eng
        model = "offline template mode"
    else:
        from . import providers
        eng = providers.get(a.provider)
        model = f"{a.provider}: {eng.MODEL}"
    st = {"synopsis": syn.model_dump(), "model": model, "drafts": [], "approvals": {}, "usage": []}
    drafts = []
    t0 = time.time()
    for sec in SECTIONS:
        if a.only and sec["number"] not in a.only.split(","):
            continue
        print(f"Drafting §{sec['number']} {sec['heading']} ...", flush=True)
        if a.offline:
            d, u = eng.draft_section(syn, sec, drafts), {}
        else:
            d, u = eng.draft_section(syn, sec, drafts, use_fallback=not a.no_fallback)
            print(f"   tokens in {u['input']} (cache read {u['cache_read']}), out {u['output']}")
        drafts.append(d)
        st["drafts"].append(d.model_dump())
        st["usage"].append({"section": sec["number"], **u})
        _save(out, st)  # keep partial progress if a later call fails
    print("Running deterministic checks ...")
    findings = checks.run_all(syn, drafts)
    print("Running reviewer pass ...")
    rep = eng.review(syn, drafts, render.soa_markdown(syn)) if a.offline else eng.review(
        syn, drafts, render.soa_markdown(syn), use_fallback=not a.no_fallback)[0]
    findings += rep.findings
    st["review_findings"] = [f.model_dump() for f in rep.findings]
    st["findings"] = [f.model_dump() for f in findings]
    _save(out, st)
    _render(out, st, syn, drafts, findings)
    print(f"\nDone in {time.time() - t0:.0f}s. Findings:")
    _print_findings(findings)
    print(f"\nWrote {out/'protocol_draft.md'} and {out/'protocol_draft.docx'}")


def cmd_check(a):
    out = pathlib.Path(a.out)
    st, syn, drafts = _state(out)
    if a.inject_error:
        # Simulate a human editing error: change the dose in Section 6 only.
        for d in drafts:
            if d.section_number == "6":
                wrong = syn.arms[0].dose
                d.text = d.text.replace(wrong, "[EDITED] 250 mg")
                print(f"Injected error: Section 6 dose '{wrong}' changed to '250 mg'.")
        st["drafts"] = [d.model_dump() for d in drafts]
        _save(out, st)
    # Rerun the deterministic checks; keep the model reviewer's findings from the draft run.
    findings = checks.run_all(syn, drafts) + [Finding.model_validate(f) for f in st.get("review_findings", [])]
    _print_findings(findings)
    st["findings"] = [f.model_dump() for f in findings]
    _save(out, st)
    _render(out, st, syn, drafts, findings)


def cmd_approve(a):
    out = pathlib.Path(a.out)
    st, syn, drafts = _state(out)
    nums = {d.section_number for d in drafts}
    if a.section not in nums:
        sys.exit(f"No section {a.section}. Sections: {', '.join(sorted(nums, key=float))}")
    crit = [f for f in st.get("findings", []) if f["severity"] == "critical" and a.section in f["sections"]]
    if crit and not a.override:
        sys.exit(f"Section {a.section} has {len(crit)} critical finding(s). Fix them or pass --override with a reason.")
    st.setdefault("approvals", {})[a.section] = {"status": "approved", "by": a.by, "date": dt.date.today().isoformat(),
                                                 **({"override": a.override} if a.override else {})}
    _save(out, st)
    _render(out, st, syn, drafts, [Finding.model_validate(f) for f in st.get("findings", [])])
    print(f"Section {a.section} approved by {a.by}.")


def cmd_export(a):
    out = pathlib.Path(a.out)
    st, syn, drafts = _state(out)
    md = _render(out, st, syn, drafts, [Finding.model_validate(f) for f in st.get("findings", [])])
    print(md.splitlines()[7] if len(md.splitlines()) > 7 else "")
    print(f"Exported {out/'protocol_draft.docx'}")


def main(argv=None):
    p = argparse.ArgumentParser(prog="fcd", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = p.add_subparsers(dest="cmd", required=True)
    d = sp.add_parser("draft"); d.add_argument("synopsis"); d.add_argument("--out", default="out")
    d.add_argument("--offline", action="store_true"); d.add_argument("--only", help="e.g. 3,6")
    d.add_argument("--no-fallback", action="store_true")
    d.add_argument("--provider", default=os.environ.get("FCD_PROVIDER", "anthropic"), help="anthropic (default), openai or xai")
    d.set_defaults(fn=cmd_draft)
    c = sp.add_parser("check"); c.add_argument("--out", default="out"); c.add_argument("--inject-error", action="store_true")
    c.set_defaults(fn=cmd_check)
    ap = sp.add_parser("approve"); ap.add_argument("section"); ap.add_argument("--by", required=True)
    ap.add_argument("--override", help="reason for approving despite critical findings"); ap.add_argument("--out", default="out")
    ap.set_defaults(fn=cmd_approve)
    e = sp.add_parser("export"); e.add_argument("--out", default="out"); e.set_defaults(fn=cmd_export)
    a = p.parse_args(argv)
    a.fn(a)


if __name__ == "__main__":
    main()
