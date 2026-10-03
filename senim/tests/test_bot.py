import asyncio

from senim import bot, store
from senim.config import settings
from tests.conftest import SAMPLE


class FakeTelegram:
    def __init__(self):
        self.calls = []

    async def call(self, method, **params):
        self.calls.append((method, params))
        return {"message_id": 99} if method == "sendMessage" else True


def _update(text, lang="ru", user_id=1):
    return {"update_id": 1, "message": {"message_id": 5, "chat": {"id": 42}, "text": text,
                                         "from": {"id": user_id, "language_code": lang}}}


def test_bot_checks_a_forwarded_answer(offline, monkeypatch):
    monkeypatch.setattr(bot, "EDIT_EVERY_S", 0)
    store.clear_memory()
    tg = FakeTelegram()
    asyncio.run(bot.Bot(tg).handle(_update(SAMPLE)))
    assert tg.calls[0][0] == "sendMessage" and "Проверяю" in tg.calls[0][1]["text"]
    final = tg.calls[-1][1]["text"]
    assert "❌ Ошибка" in final and "✅ Подтверждается" in final
    assert "Правильно: Абай Кунанбаев родился в 1845 году." in final
    assert "Готово за" in final and tg.calls[-1][1]["parse_mode"] == "HTML"


def test_bot_speaks_the_users_language_and_limits(offline, monkeypatch):
    store.clear_memory()
    monkeypatch.setattr(settings, "rate_limit_per_hour", 1)
    monkeypatch.setattr(settings, "daily_budget_usd", 0)
    tg = FakeTelegram()
    b = bot.Bot(tg)
    asyncio.run(b.handle(_update("/start", "kk")))
    assert "полиграф" in tg.calls[-1][1]["text"] and "тілдерінде" in tg.calls[-1][1]["text"]
    asyncio.run(b.handle(_update("коротко", "en")))
    assert "longer text" in tg.calls[-1][1]["text"]
    asyncio.run(b.handle(_update(SAMPLE, user_id=7)))
    asyncio.run(b.handle(_update(SAMPLE, user_id=7)))
    assert "Слишком много проверок" in tg.calls[-1][1]["text"]


def test_render_escapes_html_and_shows_progress():
    claims = [{"id": "c1", "text": "Код <script> в 1845 году", "checkable": True},
              {"id": "c2", "text": "Второй факт", "checkable": True}]
    verdicts = {"c1": {"label": "confirmed", "source_url": "https://e-history.kz/a?x=1&y=2",
                       "source_quote": "родился в 1845 году", "reasons": []}}
    text = bot.render("ru", claims, verdicts, finished=False, seconds=3)
    assert "Проверено 1 из 2" in text and "&lt;script&gt;" in text and "⏳ Второй факт" in text
    assert 'href="https://e-history.kz/a?x=1&amp;y=2"' in text
