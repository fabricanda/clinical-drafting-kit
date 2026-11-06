"""OpenAI-compatible provider. Covers OpenAI and xAI (Grok), whose API is OpenAI-compatible.

Same prompts and the same structured output (SectionDraft / ReviewReport) as the Claude
provider, so the deterministic checks and sign-off behave identically.

  FCD_PROVIDER=openai  OPENAI_API_KEY=...  FCD_OPENAI_MODEL=<model id>
  FCD_PROVIDER=xai     XAI_API_KEY=...     FCD_XAI_MODEL=<model id>

Model ids change often. Set them explicitly; the defaults are placeholders to verify.
"""
from __future__ import annotations

import os
from typing import List

from ..prompts import REVIEW_SYSTEM, SYSTEM, review_task, section_task, synopsis_text
from ..schema import ReviewReport, SectionDraft, Synopsis

VENDORS = {
    "openai": {"base_url": None, "key": "OPENAI_API_KEY", "model_env": "FCD_OPENAI_MODEL", "default": "gpt-5"},
    "xai": {"base_url": "https://api.x.ai/v1", "key": "XAI_API_KEY", "model_env": "FCD_XAI_MODEL", "default": "grok-4"},
}


class Provider:
    def __init__(self, vendor: str):
        self.cfg = VENDORS[vendor]
        self.vendor = vendor
        self.MODEL = os.environ.get(self.cfg["model_env"], self.cfg["default"])

    def _client(self):
        from openai import OpenAI

        key = os.environ.get(self.cfg["key"])
        if not key:
            raise SystemExit(f"Set {self.cfg['key']} to use the {self.vendor} provider, or use --offline.")
        return OpenAI(api_key=key, base_url=self.cfg["base_url"])

    def _call(self, system: str, syn: Synopsis, task: str, fmt):
        resp = self._client().chat.completions.parse(
            model=self.MODEL,
            messages=[{"role": "system", "content": system},
                      {"role": "user", "content": synopsis_text(syn) + "\n\n" + task}],
            response_format=fmt,
        )
        msg = resp.choices[0].message
        if getattr(msg, "refusal", None):
            raise SystemExit(f"The model declined this request: {msg.refusal}")
        u = resp.usage
        cached = getattr(getattr(u, "prompt_tokens_details", None), "cached_tokens", 0) or 0
        return msg.parsed, {"input": u.prompt_tokens, "cache_read": cached, "cache_write": 0, "output": u.completion_tokens}

    def draft_section(self, syn: Synopsis, section: dict, prior: List[SectionDraft], use_fallback=True):
        return self._call(SYSTEM, syn, section_task(section, prior), SectionDraft)

    def review(self, syn: Synopsis, drafts: List[SectionDraft], soa_md: str, use_fallback=True):
        return self._call(REVIEW_SYSTEM, syn, review_task(drafts, soa_md), ReviewReport)
