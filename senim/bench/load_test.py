"""Load test: how check time grows with simultaneous users, before vs after the scaling fixes.

    python -m bench.load_test

Runs the real SENIM pipeline. Only the outside world is simulated, with fixed delays typical of our
providers (main model 2-6 s per call, small models ~1-1.5 s, web search ~1 s), so the numbers measure
SENIM's own scheduling, not anyone's network. No API keys or credits needed.

"before": one pool of 8 model calls shared by every user, every sensor always runs.
"after":  8 calls per check + 48 per server, cascade skips witnesses when the sources settle a claim.
"""

from __future__ import annotations

import asyncio
import json
import statistics
import time

from senim import llm, net, pipeline
from senim.config import settings
from senim.extract import EXTRACT_SYSTEM
from senim.models import CheckRequest
from senim.sensors import alibi, phantom, reinterrogate

FACTS = [  # (claim, key fact, page sentence, judge stance)
    ("Абай Кунанбаев родился в 1845 году.", "1845", "Абай Кунанбаев родился в 1845 году в Чингисских горах.", "supports"),
    ("Абай умер в 1904 году.", "1904", "Абай скончался в 1904 году в родных местах.", "supports"),
    ("Столицу перенесли в Акмолу в 1997 году.", "1997", "В 1997 году столица была перенесена в Акмолу.", "supports"),
    ("Казахстан объявил независимость 16 декабря 1991 года.", "16 декабря 1991",
     "16 декабря 1991 года Казахстан провозгласил независимость.", "supports"),
    ("Гагарин стартовал с Байконура в 1963 году.", "1963", "Гагарин совершил полёт с Байконура в 1961 году.", "contradicts"),
    ("Балхаш — самое глубокое озеро Казахстана.", "Балхаш", "Балхаш — крупное озеро на юго-востоке Казахстана.", "irrelevant"),
]
TEXT = " ".join(f[0] for f in FACTS)
DELAY = {"extract": 6.0, "judge": 3.0, "witness": 1.5, "classify": 1.0, "twin": 2.0, "target": 2.0,
         "phantom_judge": 1.0, "search": 1.0, "wikimedia": 0.3}


def _extraction() -> str:
    claims = [{
        "text": c, "span": c, "type": "date", "checkable": True, "entity": f"entity{i}", "entity_kind": "person",
        "question": f"Вопрос {i}?", "question_alt": f"Вопрос {i} иначе?", "answer": a,
        "search_queries": [c, c], "citation_ids": [],
    } for i, (c, a, _, _) in enumerate(FACTS, 1)]
    return json.dumps({"language": "ru", "claims": claims, "citations": []}, ensure_ascii=False)


async def fake_model(model: str, messages: list[dict], temperature: float, max_tokens: int) -> str:
    system = messages[0]["content"] if messages[0]["role"] == "system" else ""
    user = messages[-1]["content"]
    if system.startswith(EXTRACT_SYSTEM[:40]):
        await asyncio.sleep(DELAY["extract"])
        return _extraction()
    if system == alibi.JUDGE_SYSTEM:
        await asyncio.sleep(DELAY["judge"])
        fact = next(f for f in FACTS if f"CLAIM: {f[0]}" in user)
        stance = fact[3]
        return json.dumps({"assessments": [
            {"source": s, "stance": stance, "quote": fact[2] if stance != "irrelevant" else ""} for s in ("S1", "S2")
        ][: 1 if stance == "contradicts" else 2], "suggested_correction": None}, ensure_ascii=False)
    if system == reinterrogate.WITNESS_SYSTEM:
        await asyncio.sleep(DELAY["witness"])
        return "Не знаю."
    if system == reinterrogate.CLASSIFY_SYSTEM:
        await asyncio.sleep(DELAY["classify"])
        return json.dumps({"relations": ["unsure"] * user.count("\n")})
    if system == phantom.TWIN_SYSTEM:
        await asyncio.sleep(DELAY["twin"])
        ids = [line.split("claim_id ")[1].split(" ")[0] for line in user.splitlines() if "claim_id" in line]
        return json.dumps({"twins": [{"claim_id": i, "fake_entity": "Ерлан Жаксыгалиев",
                                      "twin_question": "Когда родился Ерлан Жаксыгалиев?"} for i in ids]},
                          ensure_ascii=False)
    if system == phantom.JUDGE_SYSTEM:
        await asyncio.sleep(DELAY["phantom_judge"])
        return json.dumps({"fabricated": [False] * user.count("FICTIONAL")})
    await asyncio.sleep(DELAY["target"])
    return "Я не знаю такого человека."


async def fake_pages(claim):
    await asyncio.sleep(DELAY["search"])
    fact = next(f for f in FACTS if f[0] == claim.text)
    return "tavily", claim.search_queries, [
        {"url": f"https://{d}/{claim.id}", "title": "t", "text": f"Справка. {fact[2]} Конец."}
        for d in ("ru.wikipedia.org", "e-history.kz")]


async def fake_get_json(url, params=None, **kw):
    await asyncio.sleep(DELAY["wikimedia"])
    params = params or {}
    if "wbsearchentities" in str(params.get("action")):
        return 200, {"search": [{"id": "Q1", "label": "X", "description": ""}]}
    if params.get("action") == "wbgetentities":
        return 200, {"entities": {"Q1": {"sitelinks": {"ruwiki": {"title": "X"}}}}}
    if "pageviews" in url:
        return 200, {"items": [{"views": 5000}] * 12}
    if params.get("list") == "search":
        return 200, {"query": {"searchinfo": {"totalhits": 0}, "search": []}}
    return 404, None


async def one_check() -> tuple[float, float, int]:
    started, first = time.perf_counter(), None
    calls = 0
    async for ev in pipeline.check(CheckRequest(text=TEXT, mode="deep")):
        if ev["event"] == "verdict" and first is None:
            first = time.perf_counter() - started
        if ev["event"] == "done":
            calls = ev["data"]["llm_calls"]
    return first or 0.0, time.perf_counter() - started, calls


async def scenario(users: int) -> dict:
    results = await asyncio.gather(*[one_check() for _ in range(users)])
    return {
        "users": users,
        "first_verdict_s": round(statistics.median(r[0] for r in results), 1),
        "full_check_s": round(statistics.median(r[1] for r in results), 1),
        "slowest_s": round(max(r[1] for r in results), 1),
        "calls_per_check": round(statistics.mean(r[2] for r in results), 1),
    }


def run(label: str, global_slots: int, cascade: bool, user_counts) -> list[dict]:
    settings.llm_global_concurrency, settings.llm_concurrency, settings.cascade = global_slots, 8, cascade
    settings.rate_limit_per_hour, settings.daily_budget_usd = 0, 0
    llm._semaphores.clear()
    rows = []
    for n in user_counts:
        net.cache_clear()
        llm._semaphores.clear()
        rows.append({"setup": label, **asyncio.run(scenario(n))})
        print(rows[-1])
    return rows


def main() -> None:
    llm.set_backend(fake_model)
    alibi.gather_pages = fake_pages
    net.get_json = fake_get_json
    users = (1, 5, 10, 20)
    rows = run("before", 8, False, users) + run("after", 48, True, users)
    lines = ["| Users | Setup | First verdict | Full check (median) | Slowest user | Model calls per check |",
             "|---|---|---|---|---|---|"]
    for n in users:
        for r in (x for x in rows if x["users"] == n):
            lines.append(f"| {n} | {r['setup']} | {r['first_verdict_s']} s | {r['full_check_s']} s | "
                         f"{r['slowest_s']} s | {r['calls_per_check']} |")
    print("\n" + "\n".join(lines))


if __name__ == "__main__":
    main()
