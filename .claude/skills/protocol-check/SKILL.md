---
name: protocol-check
description: Check a drafted protocol for cross-section inconsistencies (doses, sample size, endpoints vs. visits, untraced numbers). Use after editing a draft or when the user asks to QC a protocol.
---

# Check a protocol

1. Run `fcd check --out <dir>` on a draft produced by `fcd draft`.
2. Group findings by severity. For each critical or major finding, quote the section text involved and propose a concrete edit.
3. To demonstrate the checker, run `fcd check --out <dir> --inject-error` on a copy of the output folder, never on the user's working draft.
4. Checking an arbitrary protocol document (docx/PDF not produced by this kit) is on the v0.1 roadmap and not yet implemented. Say so if asked.
