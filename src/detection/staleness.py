"""LLM staleness verification: given old code, new code, and a doc section,
is the doc still accurate?"""
from __future__ import annotations

import json

from openai import OpenAI
from pydantic import BaseModel


class StalenessVerdict(BaseModel):
    is_stale: bool
    confidence: float
    explanation: str


def verify_staleness(old_code: str, new_code: str, doc_section: str, client: OpenAI | None = None) -> StalenessVerdict:
    client = client or OpenAI()
    prompt = (
        "A code change was made. Determine whether the documentation section below is "
        "now inaccurate given the change. Only flag genuine inaccuracies, not stylistic differences.\n\n"
        f"OLD CODE:\n{old_code}\n\nNEW CODE:\n{new_code}\n\nDOC SECTION:\n{doc_section}\n\n"
        'Respond as JSON: {"is_stale": true/false, "confidence": 0.0-1.0, "explanation": "what is wrong, if anything"}.'
    )
    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0,
    )
    parsed = json.loads(resp.choices[0].message.content or "{}")
    return StalenessVerdict(
        is_stale=bool(parsed.get("is_stale", False)),
        confidence=float(parsed.get("confidence", 0.5)),
        explanation=parsed.get("explanation", ""),
    )
