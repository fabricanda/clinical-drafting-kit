"""Run with: python -m pytest -q  (no API key needed; the API is mocked)."""
import json
import pathlib

import httpx2 as httpx
import anthropic

from fcd import checks, offline, providers
from fcd.providers import anthropic_provider as llm
from fcd.cli import _load_syn
from fcd.template import SECTIONS

SYN = _load_syn(pathlib.Path(__file__).parent.parent / "examples" / "exm101_ad_ph3" / "study.yaml")


def test_offline_drafts_pass_core_checks():
    drafts = []
    for s in SECTIONS:
        drafts.append(offline.draft_section(SYN, s, drafts))
    crit = [f for f in checks.run_all(SYN, drafts) if f.severity == "critical"]
    assert crit == []


def test_dose_error_is_caught():
    drafts = []
    for s in SECTIONS:
        drafts.append(offline.draft_section(SYN, s, drafts))
    sec6 = next(d for d in drafts if d.section_number == "6")
    sec6.text = sec6.text.replace("200 mg", "250 mg")
    f = checks.run_all(SYN, drafts)
    assert any(x.severity == "critical" and "200 mg" in x.issue for x in f)
    assert any("250" in x.issue for x in f)


def test_missing_visit_for_endpoint_is_caught():
    syn = SYN.model_copy(deep=True)
    syn.visits = [v for v in syn.visits if v.week != 16]
    assert any("Week 16" in f.issue for f in checks.endpoint_visit_alignment(syn))


def test_live_request_shape(monkeypatch):
    seen = {}
    fake = {"section_number": "4", "heading": "Trial Design", "text": "600 participants, 1:1:1.",
            "sources": [{"statement": "600", "source": "sample_size"}], "assumptions": [], "open_questions": []}

    def handler(req: httpx.Request):
        seen["body"] = json.loads(req.content)
        seen["beta"] = req.headers.get("anthropic-beta")
        return httpx.Response(200, json={
            "id": "msg_1", "type": "message", "role": "assistant", "model": llm.MODEL,
            "content": [{"type": "text", "text": json.dumps(fake)}],
            "stop_reason": "end_turn", "stop_sequence": None,
            "usage": {"input_tokens": 3000, "output_tokens": 200, "cache_read_input_tokens": 2500, "cache_creation_input_tokens": 0}})

    client = anthropic.Anthropic(api_key="test", base_url="https://api.test",
                                 http_client=httpx.Client(transport=httpx.MockTransport(handler)))
    monkeypatch.setattr(llm, "_client", lambda: client)
    d, u = llm.draft_section(SYN, next(s for s in SECTIONS if s['number'] == '4'), [])
    b = seen["body"]
    assert b["model"] == "claude-opus-5-5"
    assert b["output_config"]["effort"] == "medium" and "format" in b["output_config"]
    assert b["fallbacks"] == "default" and "server-side-fallback-2026-07-01" in seen["beta"]
    assert b["system"][0]["cache_control"]["type"] == "ephemeral"
    assert d.section_number == "4" and u["cache_read"] == 2500


def test_spec_loads_from_yaml():
    from fcd.template import sections
    secs = sections("protocol_m11")
    assert [s["number"] for s in secs] == ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11"]
    assert all(s["fields"] and s["guidance"] for s in secs)


def test_provider_registry():
    assert providers.get("anthropic") is llm
    assert providers.get("grok").vendor == "xai"
    assert providers.get("xai").cfg["base_url"] == "https://api.x.ai/v1"


def test_subsection_headings_are_not_untraced_numbers():
    from fcd.schema import SectionDraft
    d = SectionDraft(section_number="7", heading="x", text="**7.1 Discontinuation.** Stop.\n### 7.3 Withdrawal\n7.4 Lost to follow-up.",
                     sources=[], assumptions=[], open_questions=[])
    assert checks.untraced_numbers(SYN, d) == []
    d.text = "Dose reduced to 37.5 mg."
    assert any("37.5" in f.issue for f in checks.untraced_numbers(SYN, d))


def test_offline_full_m11_draft_is_clean():
    drafts = []
    for s in SECTIONS:
        drafts.append(offline.draft_section(SYN, s, drafts))
    bad = [f for f in checks.run_all(SYN, drafts) if f.severity in ("critical", "major")]
    assert bad == [], [f.issue for f in bad]


def test_validate_flags_missing_visit(tmp_path, capsys):
    import yaml, pytest
    from fcd.cli import main
    raw = SYN.model_dump()
    raw["visits"] = [v for v in raw["visits"] if v["week"] != 16]
    f = tmp_path / "s.yaml"
    f.write_text(yaml.safe_dump(raw))
    with pytest.raises(SystemExit):
        main(["validate", str(f)])
    assert "Week 16" in capsys.readouterr().out


def test_validate_reports_schema_errors(tmp_path, capsys):
    import pytest
    from fcd.cli import main
    f = tmp_path / "s.yaml"
    f.write_text("protocol_id: X\nsample_size: lots\n")
    with pytest.raises(SystemExit):
        main(["validate", str(f)])
    out = capsys.readouterr().out
    assert "sample_size" in out and "title" in out
