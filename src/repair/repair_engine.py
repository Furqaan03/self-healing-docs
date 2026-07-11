"""Doc repair engine: generate targeted corrections, validate, choose mode by confidence."""
from __future__ import annotations

import json

from openai import OpenAI
from pydantic import BaseModel


class Correction(BaseModel):
    corrected_text: str
    mode: str            # "auto_fix" | "draft_for_review"
    validation_passed: bool
    validation_note: str


def _classify_mode(staleness_confidence: float, change_is_simple: bool) -> str:
    """Simple, high-confidence changes (renamed param, changed default) auto-fix.
    Complex or low-confidence changes become drafts flagged for human review."""
    if staleness_confidence >= 0.85 and change_is_simple:
        return "auto_fix"
    return "draft_for_review"


def generate_correction(doc_section: str, new_code: str, staleness_explanation: str,
                        staleness_confidence: float, change_is_simple: bool,
                        client: OpenAI | None = None) -> Correction:
    client = client or OpenAI()

    prompt = (
        "Rewrite ONLY the stale parts of this documentation section to match the new code. "
        "Preserve the original style, tone, and structure. Do not rewrite parts that are still accurate.\n\n"
        f"DOC SECTION:\n{doc_section}\n\nNEW CODE:\n{new_code}\n\nWHAT IS STALE:\n{staleness_explanation}"
    )
    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )
    corrected = resp.choices[0].message.content or ""

    validation_passed, note = _validate_correction(corrected, new_code, client)
    mode = _classify_mode(staleness_confidence, change_is_simple)
    if not validation_passed:
        mode = "draft_for_review"  # never auto-fix something that failed validation

    return Correction(corrected_text=corrected, mode=mode, validation_passed=validation_passed, validation_note=note)


def _validate_correction(corrected: str, new_code: str, client: OpenAI) -> tuple[bool, str]:
    """Second LLM pass: does the corrected doc accurately describe the new code?"""
    prompt = (
        "Does this documentation accurately describe the code? "
        'Respond as JSON: {"accurate": true/false, "note": "one sentence"}.\n\n'
        f"DOC:\n{corrected}\n\nCODE:\n{new_code}"
    )
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0,
    )
    parsed = json.loads(resp.choices[0].message.content or "{}")
    return bool(parsed.get("accurate", False)), parsed.get("note", "")
