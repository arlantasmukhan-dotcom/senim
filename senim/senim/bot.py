"""SENIM Telegram bot: forward an AI answer, get a verdict for every fact as soon as it is ready.

    TELEGRAM_BOT_TOKEN=... python -m senim.bot

Long polling, no extra dependencies. Runs the same pipeline as the web app (and the same abuse limits:
checks per Telegram user per hour, daily model budget). One message is edited as verdicts arrive.
"""

from __future__ import annotations

import asyncio
import html
import logging
import os
import time
from typing import Any

import httpx

from . import guard, pipeline
from .models import CheckRequest

log = logging.getLogger("senim.bot")

LABELS = {
    "ru": {"contradicted": "❌ Ошибка", "suspicious": "🟠 Сомнительно", "unconfirmed": "⚪ Нет подтверждения",
           "confirmed": "✅ Подтверждается", "not_checkable": "💬 Мнение"},
    "kk": {"contradicted": "❌ Қате", "suspicious": "🟠 Күмәнді", "unconfirmed": "⚪ Расталмаған",
           "confirmed": "✅ Расталады", "not_checkable": "💬 Пікір"},
    "en": {"contradicted": "❌ Error", "suspicious": "🟠 Doubtful", "unconfirmed": "⚪ Not confirmed",
           "confirmed": "✅ Confirmed", "not_checkable": "💬 Opinion"},
}
TEXT = {
    "ru": {
        "start": ("Я SENIM — полиграф для ответов ИИ.\n\nПерешлите мне ответ ChatGPT, Gemini или другого ИИ, "
                  "и я проверю каждый факт: найду источники с дословной цитатой, переспрошу другие модели "
                  "и скажу, где ИИ ошибся.\n\nРаботаю на казахском, русском и английском."),
        "short": "Пришлите текст подлиннее — хотя бы одно предложение с фактом.",
        "working": "🔎 Проверяю… Разбираю ответ на факты.",
        "progress": "🔎 Проверено {done} из {total}",
        "done": "Готово за {s} с.",
        "fix": "Правильно",
        "source": "Источник",
        "none": "В тексте не нашлось фактов, которые можно проверить.",
        "rate_limited": "Слишком много проверок. Попробуйте через час.",
        "budget_exceeded": "Дневной лимит проверок исчерпан. Попробуйте завтра.",
        "error": "Не получилось проверить: {msg}",
        "busy": "Подождите, предыдущая проверка ещё идёт.",
    },
    "kk": {
        "start": ("Мен SENIM — ЖИ жауаптарына арналған полиграф.\n\nChatGPT, Gemini не басқа ЖИ жауабын маған "
                  "жіберіңіз: әр фактіні тексеремін, дереккөзден нақты дәйексөз табамын, басқа модельдерден "
                  "қайта сұраймын және ЖИ қай жерде қателескенін айтамын.\n\nҚазақ, орыс және ағылшын тілдерінде жұмыс істеймін."),
        "short": "Ұзынырақ мәтін жіберіңіз — кем дегенде бір фактісі бар сөйлем.",
        "working": "🔎 Тексеріп жатырмын… Жауапты фактілерге бөлудемін.",
        "progress": "🔎 {total} фактінің {done} тексерілді",
        "done": "{s} с ішінде дайын.",
        "fix": "Дұрысы",
        "source": "Дереккөз",
        "none": "Мәтінде тексеруге болатын факт табылмады.",
        "rate_limited": "Тексеру тым көп. Бір сағаттан кейін қайталаңыз.",
        "budget_exceeded": "Күндік тексеру лимиті таусылды. Ертең қайталаңыз.",
        "error": "Тексеру мүмкін болмады: {msg}",
        "busy": "Күте тұрыңыз, алдыңғы тексеру әлі жүріп жатыр.",
    },
    "en": {
        "start": ("I'm SENIM, a polygraph for AI answers.\n\nForward me an answer from ChatGPT, Gemini or any AI and "
                  "I'll check every fact: find sources with a word-for-word quote, re-ask other models and show "
                  "where the AI got it wrong.\n\nI work in Kazakh, Russian and English."),
        "short": "Send a longer text — at least one sentence with a fact.",
        "working": "🔎 Checking… Splitting the answer into facts.",
        "progress": "🔎 Checked {done} of {total}",
        "done": "Done in {s} s.",
        "fix": "Correct",
        "source": "Source",
        "none": "No checkable facts found in this text.",
        "rate_limited": "Too many checks. Try again in an hour.",
        "budget_exceeded": "The daily check limit is used up. Try again tomorrow.",
        "error": "Could not check it: {msg}",
        "busy": "Please wait, your previous check is still running.",
    },
}
MAX_MESSAGE = 4000
EDIT_EVERY_S = 1.5


def ui_lang(user: dict | None) -> str:
    code = ((user or {}).get("language_code") or "ru")[:2]
    return code if code in TEXT else "ru"


def _e(s: str) -> str:
    return html.escape(s or "", quote=False)


def _short(s: str, n: int) -> str:
    s = " ".join((s or "").split())
    return s if len(s) <= n else s[: n - 1] + "…"


def render(lang: str, claims: list[dict], verdicts: dict[str, dict], finished: bool, seconds: float) -> str:
    """The bot's single message: one block per fact, in the order of the answer. Pure (tested)."""
    t, labels = TEXT[lang], LABELS[lang]
    checkable = [c for c in claims if c.get("checkable")]
    blocks = []
    if not finished:
        blocks.append(f"<i>{t['progress'].format(done=sum(c['id'] in verdicts for c in checkable), total=len(checkable))}</i>")
    for c in claims:
        v = verdicts.get(c["id"])
        if not v:
            blocks.append(f"⏳ {_e(_short(c['text'], 200))}")
            continue
        lines = [f"<b>{labels.get(v['label'], v['label'])}</b>: {_e(_short(c['text'], 200))}"]
        if v.get("suggested_correction"):
            lines.append(f"✏️ {t['fix']}: {_e(_short(v['suggested_correction'], 200))}")
        if v.get("source_quote") and v.get("source_url"):
            lines.append(f"📎 <a href=\"{html.escape(v['source_url'])}\">{t['source']}</a>: "
                         f"«{_e(_short(v['source_quote'], 180))}»")
        elif v.get("reasons"):
            lines.append(f"↳ {_e(_short(v['reasons'][0], 220))}")
        blocks.append("\n".join(lines))
    if finished:
        blocks.append(f"<i>{t['done'].format(s=round(seconds))}</i>")
    text = "\n\n".join(blocks)
    return text if len(text) <= MAX_MESSAGE else text[: MAX_MESSAGE - 1] + "…"


class Telegram:
    def __init__(self, token: str, client: httpx.AsyncClient | None = None):
        self.base = f"https://api.telegram.org/bot{token}/"
        self.http = client or httpx.AsyncClient(timeout=70)

    async def call(self, method: str, **params: Any) -> Any:
        r = await self.http.post(self.base + method, json=params)
        data = r.json()
        if not data.get("ok"):
            if "message is not modified" in str(data.get("description")):
                return None
            raise RuntimeError(f"{method}: {data.get('description')}")
        return data["result"]


class Bot:
    def __init__(self, tg: Telegram):
        self.tg = tg
        self.busy: set[int] = set()

    async def handle(self, update: dict) -> None:
        msg = update.get("message") or {}
        chat = (msg.get("chat") or {}).get("id")
        user = msg.get("from") or {}
        text = (msg.get("text") or msg.get("caption") or "").strip()
        if not chat or not text:
            return
        lang = ui_lang(user)
        if text.startswith("/start") or text.startswith("/help"):
            await self.tg.call("sendMessage", chat_id=chat, text=TEXT[lang]["start"])
            return
        if len(text) < 20:
            await self.tg.call("sendMessage", chat_id=chat, text=TEXT[lang]["short"])
            return
        if user.get("id") in self.busy:
            await self.tg.call("sendMessage", chat_id=chat, text=TEXT[lang]["busy"])
            return
        refused = await guard.admit(f"tg:{user.get('id')}")
        if refused:
            await self.tg.call("sendMessage", chat_id=chat, text=TEXT[lang][refused])
            return
        self.busy.add(user.get("id"))
        try:
            await self.check(chat, msg.get("message_id"), text, lang)
        finally:
            self.busy.discard(user.get("id"))

    async def check(self, chat: int, reply_to: int | None, text: str, lang: str) -> None:
        sent = await self.tg.call("sendMessage", chat_id=chat, text=TEXT[lang]["working"],
                                  reply_to_message_id=reply_to)
        message_id = sent["message_id"]
        claims: list[dict] = []
        verdicts: dict[str, dict] = {}
        started, last_edit, shown = time.monotonic(), 0.0, ""

        async def show(final: bool = False) -> None:
            nonlocal last_edit, shown
            body = render(lang, claims, verdicts, final, time.monotonic() - started)
            if body == shown or (not final and time.monotonic() - last_edit < EDIT_EVERY_S):
                return
            await self.tg.call("editMessageText", chat_id=chat, message_id=message_id, text=body,
                               parse_mode="HTML", disable_web_page_preview=True)
            last_edit, shown = time.monotonic(), body

        async for ev in pipeline.check(CheckRequest(text=text, ui_lang=lang, mode="deep")):
            if ev["event"] == "claims":
                claims = ev["data"]["claims"]
                await show()
            elif ev["event"] == "verdict":
                verdicts[ev["data"]["claim_id"]] = ev["data"]
                await show()
            elif ev["event"] == "error":
                await self.tg.call("editMessageText", chat_id=chat, message_id=message_id,
                                   text=TEXT[lang]["error"].format(msg=ev["data"].get("message") or ev["data"]["code"]))
                return
        if not claims:
            await self.tg.call("editMessageText", chat_id=chat, message_id=message_id, text=TEXT[lang]["none"])
            return
        await show(final=True)

    async def run(self) -> None:
        offset = 0
        await self.tg.call("deleteWebhook")
        me = await self.tg.call("getMe")
        log.info("SENIM bot @%s is running", me.get("username"))
        running: set[asyncio.Task] = set()
        while True:
            try:
                updates = await self.tg.call("getUpdates", offset=offset, timeout=50,
                                             allowed_updates=["message"])
            except Exception as e:
                log.warning("getUpdates failed: %s", e)
                await asyncio.sleep(3)
                continue
            for u in updates:
                offset = u["update_id"] + 1
                task = asyncio.create_task(self._safe(u))
                running.add(task)
                task.add_done_callback(running.discard)

    async def _safe(self, update: dict) -> None:
        try:
            await self.handle(update)
        except Exception:
            log.exception("update failed")


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        raise SystemExit("Set TELEGRAM_BOT_TOKEN (get one from @BotFather) in .env")
    asyncio.run(Bot(Telegram(token)).run())


if __name__ == "__main__":
    main()
