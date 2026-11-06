# Instructions for coding agents (Claude Code, Codex, others)

This repository drafts clinical development documents. Work by these rules:

1. **The study YAML is the source of truth.** Never invent a number, dose, timepoint, criterion or result. If something is missing, write `[TBD: what is needed]` and list it as an open question.
2. **Use the CLI for anything deterministic.** Draft with `fcd draft`, then always run `fcd check` and report every critical and major finding to the user. Never write or edit the Schedule of Activities by hand; it is rendered from the visit table.
3. **Follow the section spec.** `fcd/specs/<document>.yaml` lists, per section, which study fields may be used and what the section must contain.
4. **Never approve a section yourself.** `fcd approve` records a named human reviewer. Ask the user to run it, or run it only with the name they give you.
5. **Keep data where the user puts it.** Do not upload study files anywhere other than the model provider the user configured.
6. **Say what you could not do.** If a check fails or a field is missing, report it plainly; do not paper over it.

Skills for specific tasks live in `.claude/skills/` (SKILL.md format).
