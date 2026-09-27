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
Judge the MEANING, not the wording: paraphrases and synonyms agree (e.g. "salty" and "bitter/brackish" water,
"the capital moved" and "the capital was transferred"). Answers may be in Kazakh, Russian or English.
Reply with ONLY JSON: {"relations": ["agree|contradict|unsure", ...]} in the same order as the answers."""

_REFUSAL = re.compile(
    r"\bunknown\b|i don.?t know|not sure|no (reliable )?information|not aware|not familiar|"
    r"could(?:n.?t| not) find|unable to (find|verify)|no record|does(?:n.?t| not) exist|"
    r"не знаю|нет (точной |достоверной )?информации|нет данных|не располагаю|не могу (найти|подтвердить)|"
    r"не удалось (найти|установить)|не наш[её]л|не существует|неизвестн|"
    r"білмеймін|мәлімет жоқ|ақпарат жоқ|белгісіз",
    re.I,
)


_CENTURY = re.compile(r"век|ғасыр|centur|\b[IVXL]+\b", re.I)


def is_refusal(answer: str) -> bool:
    return bool(_REFUSAL.search(answer or ""))


def numeric_relation(claim_answer: str, witness_answer: str) -> str | None:
    """Deterministic comparison when the key fact is a number/date. None = cannot decide numerically."""
    wanted = numbers(claim_answer)
    if not wanted or _CENTURY.search(claim_answer):
        return None               # "9th century" vs "born around 870": not comparable digit-by-digit
    if is_refusal(witness_answer):
        return "unsure"
    got = numbers(witness_answer)
    if not got:
        return None
    if wanted <= got:
        return "agree"            # every key number of the claim is there (extra ones like the day are fine)
    if got - wanted:
        return "contradict"       # e.g. claim "1991, 25 Dec" vs witness "1991, 16 Dec"
    return None                   # partial answer (only "1991"): let the classifier decide


def summarize(answers: list[WitnessAnswer]) -> ReinterrogationResult:
    n = len(answers) or 1
    res = ReinterrogationResult(answers=answers)
    res.agree_share = sum(a.relation == "agree" for a in answers) / n
    res.contradict_share = sum(a.relation == "contradict" for a in answers) / n
    res.unsure_share = sum(a.relation == "unsure" for a in answers) / n
    return res


async def _ask(model: str, question: str, phrasing: int) -> WitnessAnswer | llm.LLMError:
    try:
        reply = await llm.chat(model, [
            {"role": "system", "content": WITNESS_SYSTEM},
            {"role": "user", "content": question},
        ], temperature=0.7, max_tokens=1000)  # headroom: some models spend tokens on hidden reasoning
    except llm.LLMError as e:
        return e
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
    replies = await asyncio.gather(*jobs)
    answers = [a for a in replies if isinstance(a, WitnessAnswer)]
    failures = [str(a) for a in replies if isinstance(a, llm.LLMError)]
    if not answers:
        return ReinterrogationResult(status="error", note="no witness answered: " + "; ".join(failures[:2]))

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
    res = summarize(answers)
    if failures:
        res.note = f"{len(failures)} of {len(replies)} witness calls failed: {failures[0][:120]}"
    return res
