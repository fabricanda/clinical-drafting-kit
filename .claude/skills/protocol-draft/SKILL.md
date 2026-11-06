---
name: protocol-draft
description: Draft a clinical trial protocol in ICH M11 layout from a study synopsis YAML, then run consistency checks. Use when the user asks to draft or redraft a protocol or protocol sections.
---

# Draft a protocol

1. Find the study file (default `examples/exm101_ad_ph3/study.yaml`). Validate it by running `fcd draft <file> --out <dir> --offline` first; if it fails validation, show the user the missing or malformed fields and stop.
2. Ask which provider the user has a key for (anthropic, openai, xai). Draft: `fcd draft <file> --out <dir> --provider <p>`. Use `--only 3,10` to redraft selected sections.
3. Run `fcd check --out <dir>`. Report every critical and major finding with its section and the suggested fix.
4. Summarize Appendix C (assumptions and open questions) as the list of decisions the clinical team still owes.
5. Point the user to `<dir>/protocol_draft.docx`. Remind them each section needs `fcd approve <section> --by "<name>"` from a qualified reviewer. Do not approve sections yourself.

If the user has no API key, you may draft sections yourself following `fcd/specs/protocol_m11.yaml` and the rules in `docs/agent-instructions.md`, but say clearly that the CLI checks then apply only after the text is loaded into `state.json`.
