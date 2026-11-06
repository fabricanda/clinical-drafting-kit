"""Anthropic (Claude) provider: the reference implementation.

Claude calls. One structured call per section, then one reviewer call.

Design choices worth explaining in a demo:
- The system prompt and the full synopsis are identical on every call and sit first,
  marked for prompt caching, so sections 2..N reuse the cached prefix.
- Output is a validated Pydantic object (messages.parse), so every section comes back
  with its text, its source links, its assumptions and its open questions, never free text.
- Server-side fallback is on, so a policy decline retries on another model instead of failing.
"""
from __future__ import annotations

import json
import os
from typing import List, Optional

from ..prompts import REVIEW_SYSTEM, SYSTEM, review_task, section_task, synopsis_text
from ..schema import ReviewReport, SectionDraft, Synopsis

MODEL = os.environ.get("FCD_ANTHROPIC_MODEL", "claude-opus-5-5")
EFFORT = os.environ.get("FCD_EFFORT", "medium")




def _client():
    import anthropic

    return anthropic.Anthropic()


def _synopsis_block(syn: Synopsis) -> dict:
    return {
        "type": "text",
        "text": synopsis_text(syn),
        "cache_control": {"type": "ephemeral"},
    }


def _call(system: str, user_blocks: List[dict], output_format, use_fallback: bool = True):
    import anthropic

    kwargs = {}
    if use_fallback:
        kwargs["extra_headers"] = {"anthropic-beta": "server-side-fallback-2026-07-01"}
        kwargs["extra_body"] = {"fallbacks": "default"}
    try:
        resp = _client().messages.parse(
            model=MODEL,
            max_tokens=16000,
            system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
            messages=[{"role": "user", "content": user_blocks}],
            output_config={"effort": EFFORT},
            output_format=output_format,
            **kwargs,
        )
    except anthropic.RateLimitError:
        raise SystemExit("Rate limited by the API. Wait a minute and rerun; finished sections are kept.")
    except anthropic.AuthenticationError:
        raise SystemExit("No valid API key. Set ANTHROPIC_API_KEY, or use --offline.")
    except anthropic.APIStatusError as e:
        raise SystemExit(f"API error {e.status_code}: {e.message}")
    except anthropic.APIConnectionError:
        raise SystemExit("Network error reaching the API.")

    if resp.stop_reason == "refusal":
        raise SystemExit("The model declined this request (refusal). Check the synopsis content.")
    if resp.stop_reason == "max_tokens":
        raise SystemExit("Output hit max_tokens; shorten the section guidance or raise the limit.")
    u = resp.usage
    stats = {
        "input": u.input_tokens,
        "cache_read": getattr(u, "cache_read_input_tokens", 0) or 0,
        "cache_write": getattr(u, "cache_creation_input_tokens", 0) or 0,
        "output": u.output_tokens,
    }
    return resp.parsed_output, stats


def draft_section(syn: Synopsis, section: dict, prior: List[SectionDraft], use_fallback=True):
    return _call(SYSTEM, [_synopsis_block(syn), {"type": "text", "text": section_task(section, prior)}], SectionDraft, use_fallback)


def review(syn: Synopsis, drafts: List[SectionDraft], soa_md: str, use_fallback=True):
    return _call(REVIEW_SYSTEM, [_synopsis_block(syn), {"type": "text", "text": review_task(drafts, soa_md)}], ReviewReport, use_fallback)
