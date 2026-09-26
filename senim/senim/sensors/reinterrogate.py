"""Sensor 2 — RE-INTERROGATION: ask different AI models the claim's question again.
If the story changes between "witnesses", the original answer was probably a guess
(a simplified form of semantic-entropy / SelfCheckGPT)."""

from __future__ import annotations

import asyncio
import re

from .. import llm
from ..config import settings
from ..models import Claim, ReinterrogationResult, WitnessAnswer
from ..text import numbers

WITNESS_SYSTEM = (
    "Answer the question in ONE short sentence with the specific fact (number, date, name, place). "
    "If you do not know, answer exactly: unknown."
)

CLASSIFY_SYSTEM = """Compare each ANSWER with the CLAIM. For each answer output:
"agree" if it states the same key fact, "contradict" if it states a different value for the same fact,
"unsure" if it says it does not know or does not address the fact.
Reply with ONLY JSON: {"relations": ["agree|contradict|unsure", ...]} in the same order as the answers."""

_REFUSAL = re.compile(
    r"\bunknown\b|i don.?t know|not sure|no (reliable )?information|not aware|not familiar|"
    r"could(?:n.?t| not) find|unable to (find|verify)|no record|does(?:n.?t| not) exist|"
    r"не знаю|нет (точной |достоверной )?информации|нет данных|не располагаю|не могу (найти|подтвердить)|"
    r"не удалось (найти|установить)|не наш[её]л|не существует|неизвестн|"
    r"білмеймін|мәлімет жоқ|ақпарат жоқ|белгісіз",
    re.I,
)


def is_refusal(answer: str) -> bool:
    return bool(_REFUSAL.search(answer or ""))


def numeric_relation(claim_answer: str, witness_answer: str) -> str | None:
    """Deterministic comparison when the key fact is a number/date. None = cannot decide numerically."""
    wanted = numbers(claim_answer)
    if not wanted:
        return None
    if is_refusal(witness_answer):
        return "unsure"
    got = numbers(witness_answer)
    if not got:
        return None
    return "agree" if wanted & got else "contradict"


def summarize(answers: list[WitnessAnswer]) -> ReinterrogationResult:
    n = len(answers) or 1
    res = ReinterrogationResult(answers=answers)
    res.agree_share = sum(a.relation == "agree" for a in answers) / n
    res.contradict_share = sum(a.relation == "contradict" for a in answers) / n
    res.unsure_share = sum(a.relation == "unsure" for a in answers) / n
    return res


async def _ask(model: str, question: str, phrasing: int) -> WitnessAnswer | None:
    try:
        reply = await llm.chat(model, [
            {"role": "system", "content": WITNESS_SYSTEM},
            {"role": "user", "content": question},
        ], temperature=0.7, max_tokens=300)
    except llm.LLMError:
        return None
    return WitnessAnswer(model=model, phrasing=phrasing, answer=reply.strip()[:400])


async def run(claim: Claim) -> ReinterrogationResult:
    if not claim.checkable:
        return ReinterrogationResult(status="skipped", note="not a checkable fact")
    if not llm.available():
        return ReinterrogationResult(status="off", note="OPENROUTER_API_KEY not set")
    if not claim.question:
        return ReinterrogationResult(status="skipped", note="no question could be formed for this claim")

    phrasings = [claim.question, claim.question_alt or claim.question]
    jobs = [_ask(m, q, i + 1) for m in settings.witnesses for i, q in enumerate(phrasings)]
    answers = [a for a in await asyncio.gather(*jobs) if a is not None]
    if not answers:
        return ReinterrogationResult(status="error", note="no witness model answered")

    undecided = []
    for a in answers:
        rel = numeric_relation(claim.answer or "", a.answer)
        if rel is None and is_refusal(a.answer):
            rel = "unsure"
        if rel is None:
            undecided.append(a)
        else:
            a.relation = rel
    if undecided:
        listing = "\n".join(f"{i + 1}. {a.answer}" for i, a in enumerate(undecided))
        try:
            data = await llm.chat_json(settings.model_fast, [
                {"role": "system", "content": CLASSIFY_SYSTEM},
                {"role": "user", "content": f"CLAIM: {claim.text}\nKEY FACT: {claim.answer or '-'}\n\nANSWERS:\n{listing}"},
            ], max_tokens=400)
            rels = data.get("relations", []) if isinstance(data, dict) else []
        except llm.LLMError:
            rels = []
        for a, rel in zip(undecided, rels):
            if rel in ("agree", "contradict", "unsure"):
                a.relation = rel
    return summarize(answers)
