"""Model providers. Each exposes MODEL, draft_section(...) -> (SectionDraft, usage) and review(...) -> (ReviewReport, usage)."""
from __future__ import annotations


def get(name: str):
    name = (name or "anthropic").lower()
    if name in ("anthropic", "claude"):
        from . import anthropic_provider
        return anthropic_provider
    if name in ("openai", "xai", "grok"):
        from .openai_compat import Provider
        return Provider("xai" if name == "grok" else name)
    raise SystemExit(f"Unknown provider '{name}'. Use anthropic, openai or xai.")
