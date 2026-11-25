---
name: synopsis-interview
description: Turn rough study concept material (notes, a TPP, an earlier protocol, a call transcript) into a validated study synopsis YAML for the protocol drafter. Use when the user wants to start a new protocol or has no study file yet.
---

# Build a study synopsis by interview

The study file is the single source of truth for every later draft, so this step decides draft quality. Your job is to extract and ask, never to invent.

1. **Collect sources.** Ask what the user has: concept notes, a target product profile, a prior protocol or synopsis, a slide deck, a transcript. Read them.
2. **Start from the template.** Copy `examples/_template/study.yaml` to a new folder (e.g. `studies/<protocol_id>/study.yaml`). The field descriptions are in `schemas/study.schema.json`.
3. **Fill only what the sources state.** Copy numbers exactly. For anything not stated, leave `[TBD: what is needed]`. Keep a short list of every field you filled by inference (e.g. "visit windows assumed ±3 days") and show it to the user for confirmation.
4. **Interview for the gaps, in this order** (decisions that drive the rest come first), a few questions per turn:
   1. Objectives and endpoints: primary, key secondary, timepoints, endpoint type.
   2. Design: phase, comparator, arms with dose and regimen, randomization ratio and strata, blinding.
   3. Population: age range, key inclusion and exclusion criteria.
   4. Duration: treatment weeks, follow-up weeks, visit schedule with procedures (every endpoint timepoint needs a visit).
   5. Statistics: sample size, power assumptions, analysis population, primary analysis including intercurrent events and missing data, multiplicity.
   6. Safety and conduct: rescue therapy, safety monitoring, discontinuation criteria, oversight (DMC, monitoring approach).
   Offer a typical choice when the user is unsure (e.g. "a composite strategy treating rescue as non-response is common here"), label it as a suggestion, and record it only if they accept.
5. **Validate.** Run `fcd validate <file>`. Fix every schema error with the user. Report remaining empty and `[TBD]` fields as open decisions.
6. **Hand off.** Tell the user the file is ready for the `protocol-draft` skill, and list the open decisions that will appear as `[TBD]` in the draft.

Never fill a dose, sample size, timepoint, or criterion the user or sources did not give you.
