# Clinical Drafting Kit

AI first drafts of clinical development documents, built so a qualified reviewer can check every number. Maintained by [Fabricanda](https://fabricanda.ai).

**Status: v0.1 in development.** The protocol drafter works today. Other tools are on the roadmap below.

## What it does
You give it a structured study synopsis (YAML). It drafts a protocol in the ICH M11 layout, one section at a time, with any of three model providers. Then:

- **Every number traces back to the synopsis.** Each section returns its text, its source links, its assumptions and its open questions.
- **Deterministic checks run with no model.** They catch dose drift between sections, endpoints measured at a week with no visit, sample sizes that don't match, and numbers with no source.
- **Tables that must be exact are built from data.** The model never writes the Schedule of Activities.
- **A named person signs off each section.** A section with a critical finding can't be approved without a written reason. The document reads "DRAFT, NOT APPROVED" until every section is signed.

The kit gets you a strong first draft faster. It does not replace medical writing, clinical, statistical or regulatory review. Read [DISCLAIMER.md](DISCLAIMER.md).

## Use it in a coding agent (Claude Code, Codex)
Clone the repo and open it in your agent. Ask: *"Draft a protocol from examples/exm101_ad_ph3/study.yaml."* The agent follows `AGENTS.md` / `CLAUDE.md` and the skills in `.claude/skills/`, and it runs the same checks as the CLI.

## Use the CLI
```bash
pip install -e ".[openai]"               # Python 3.10+
fcd draft examples/exm101_ad_ph3/study.yaml --out out/ --offline   # no model, tests the pipeline
export ANTHROPIC_API_KEY=...             # or OPENAI_API_KEY / XAI_API_KEY
fcd draft examples/exm101_ad_ph3/study.yaml --out out/ --provider anthropic   # or openai, xai
fcd check --out out/                     # rerun deterministic checks after editing
fcd check --out out/ --inject-error      # demo: a dose edit gets caught
fcd approve 5 --by "Your Name" --out out/
fcd export --out out/                    # out/protocol_draft.md and .docx
```
Set model ids with `FCD_ANTHROPIC_MODEL`, `FCD_OPENAI_MODEL` or `FCD_XAI_MODEL`. Your data goes only to the provider you choose; nothing is sent to Fabricanda.

## Layout
```
fcd/specs/protocol_m11.yaml  Section plan: allowed study fields and guidance per section (edit this, not code)
fcd/schema.py                Study synopsis (input) and section draft (output) models
fcd/prompts.py               Prompts shared by every provider
fcd/providers/               anthropic (reference), openai_compat (OpenAI and xAI/Grok)
fcd/checks.py                Deterministic consistency and traceability checks
fcd/render.py                Markdown/Word output, SoA from data, appendices, sign-off log
fcd/offline.py               Template mode, no model
fcd/cli.py                   draft / check / approve / export
.claude/skills/              Agent skills (SKILL.md), readable by Claude Code and Codex
examples/                    Fictional studies only
```

## Roadmap
| Version | Tools |
|---|---|
| v0.1 | Protocol drafter (ICH M11), synopsis interviewer, protocol checker for any protocol |
| v0.2 | Informed consent (21 CFR 50.25), SAP shell and estimands (ICH E9(R1)), clinical development plan |
| v0.3 to v1.0 | IND prep pack (21 CFR 312.23, eCTD Modules 1 to 5), pre-IND meeting package, published evaluation |
| Later | Amendment summary of changes, CSR shell (ICH E3), IB updates, patient-burden score |

## License
Code: Apache-2.0 ([LICENSE](LICENSE)). Section specs, prompts, templates and docs: CC BY 4.0 ([LICENSE-content](LICENSE-content)). ICH guidelines are referenced by section, not reproduced; get them from ich.org.
