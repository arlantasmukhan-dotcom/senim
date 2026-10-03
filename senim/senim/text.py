"""Text helpers: normalization, Quote-Lock, span location, passage selection."""

from __future__ import annotations

import difflib
import json
import re
import unicodedata
from dataclasses import dataclass

_QUOTES = str.maketrans({
    "«": '"', "»": '"', "„": '"', "“": '"', "”": '"', "‟": '"', "″": '"',
    "‘": "'", "’": "'", "‚": "'", "‛": "'", "′": "'", "`": "'",
    "–": "-", "—": "-", "―": "-", "‐": "-", "‑": "-", "−": "-",
    " ": " ", " ": " ", " ": " ", " ": " ",
})
_INVISIBLE = re.compile(r"[­​‌‍⁠﻿]")
_SPACES = re.compile(r"\s+")
_WORD = re.compile(r"\w+", re.UNICODE)


def normalize(text: str) -> str:
    """Lower-case, unify quotes/dashes/spaces, drop invisible characters.

    Only formatting is normalized, never wording: Quote-Lock must stay strict.
    """
    text = unicodedata.normalize("NFC", text or "")
    text = _INVISIBLE.sub("", text).translate(_QUOTES)
    text = text.replace("ё", "е").replace("Ё", "Е")
    return _SPACES.sub(" ", text).strip().casefold()


def quote_lock(quote: str, page_text: str, min_len: int = 12) -> bool:
    """True only if `quote` literally occurs in `page_text` (after formatting normalization).

    This is the guard that stops the LLM judge from inventing evidence: a quote that
    is not on the page is thrown away, whatever the judge said about it.
    """
    q = normalize(quote).strip(" .\"'")
    if len(q) < min_len:
        return False
    return q in normalize(page_text)


def locate_span(span: str | None, text: str) -> tuple[int, int] | None:
    """Find `span` inside the original `text`; returns (start, end) in original indices."""
    if not span:
        return None
    idx = text.find(span)
    if idx >= 0:
        return idx, idx + len(span)
    # Formatting-tolerant search: walk the original text and compare normalized windows.
    target = normalize(span)
    if not target:
        return None
    sentences = split_sentences_with_offsets(text)
    for start, end in sentences:
        if target in normalize(text[start:end]):
            return start, end
    # Last resort: best fuzzy sentence match.
    best, best_ratio = None, 0.0
    for start, end in sentences:
        ratio = difflib.SequenceMatcher(None, target, normalize(text[start:end])).ratio()
        if ratio > best_ratio:
            best, best_ratio = (start, end), ratio
    return best if best_ratio >= 0.6 else None


_SENT_END = re.compile(r"(?<=[.!?…])\s+|\n+")


def split_sentences_with_offsets(text: str) -> list[tuple[int, int]]:
    spans, pos = [], 0
    for m in _SENT_END.finditer(text):
        if m.start() > pos:
            spans.append((pos, m.start()))
        pos = m.end()
    if pos < len(text):
        spans.append((pos, len(text)))
    return [(s, e) for s, e in spans if text[s:e].strip()]


def words(text: str) -> list[str]:
    return [w for w in _WORD.findall(normalize(text)) if len(w) > 2 or w.isdigit()]


def best_passages(page_text: str, query: str, max_chars: int = 2400, window: int = 600) -> str:
    """Pick the parts of a long page that overlap most with the claim (cheap BM25-like scoring)."""
    page_text = page_text or ""
    if len(page_text) <= max_chars:
        return page_text
    q = set(words(query))
    if not q:
        return page_text[:max_chars]
    q_nums = quantities(query)
    chunks = [page_text[i:i + window] for i in range(0, len(page_text), window // 2)]
    scored = []
    for i, chunk in enumerate(chunks):
        w = words(chunk)
        if not w:
            continue
        hits = sum(1 for t in w if t in q and not t.isdigit())
        nums = quantities(chunk) if q_nums else []
        digits = sum(1 for n in q_nums if has_number(n, nums))  # numbers matter most; "2 700 000" = "2,7 млн"
        scored.append((hits + 3 * digits, i))
    scored.sort(reverse=True)
    picked, total = [], 0
    for _, i in scored:
        if total + len(chunks[i]) > max_chars:
            break
        picked.append(i)
        total += len(chunks[i])
    return "\n…\n".join(chunks[i] for i in sorted(picked))


@dataclass(frozen=True)
class Num:
    """A number as a value plus the rounding step its writing implies ("2,7 млн" → 2 700 000 ± 50 000)."""
    value: float
    step: float
    scaled: bool
    raw: str

    @property
    def kind(self) -> str:
        """Only numbers of the same kind are compared: a day never contradicts a year or a population."""
        if self.scaled or self.value != int(self.value):
            return "other"
        if 1000 <= self.value <= 2100:
            return "year"
        return "day" if 1 <= self.value <= 31 else "other"


_NUM_SPACES = str.maketrans({" ": " ", " ": " ", " ": " ", " ": " "})
_DATE = re.compile(r"(?<![\d.,])(\d{1,2})([./])(\d{1,2})\2(\d{4}|\d{2})(?![\d.,]*\d)")
_NUMBER = re.compile(
    r"(?<![\d.,])"
    r"(?P<num>(?P<grouped>\d{1,3}(?P<sep>[ ,.'’])\d{3}(?:(?P=sep)\d{3})*)(?P<gfrac>[.,]\d+)?(?!\d)"  # 20 000 / 20,000
    r"|(?P<whole>\d+)(?:[.,](?P<frac>\d+))?)"                                                      # 1845 / 2,7
    r"(?:\s?(?P<scale>тыс|тысяч\w*|мың\w*|thousand\w*|k|млн|миллион\w*|million\w*|mln|mn|"
    r"млрд|миллиард\w*|billion\w*|bn|трлн|триллион\w*|trillion\w*)(?![^\W\d_]))?",
    re.I,
)
_SCALE = (("тыс", 1e3), ("мың", 1e3), ("thousand", 1e3), ("k", 1e3), ("млн", 1e6), ("миллион", 1e6),
          ("million", 1e6), ("mln", 1e6), ("mn", 1e6), ("млрд", 1e9), ("миллиард", 1e9), ("billion", 1e9),
          ("bn", 1e9), ("трлн", 1e12), ("триллион", 1e12), ("trillion", 1e12))


def _scale_of(word: str | None) -> float:
    if not word:
        return 1.0
    w = word.lower()
    return next(v for prefix, v in _SCALE if w.startswith(prefix))


def quantities(text: str) -> list[Num]:
    """All numbers in `text` by value. Understands thousands separators ("20 000", "20,000"), decimal commas
    ("2,7"), scale words ("2,7 млн", "3 мың", "1.5 billion") and dotted dates ("10.08.1845" → 10, 8, 1845)."""
    text = (text or "").translate(_NUM_SPACES)
    out: list[Num] = []

    def date(m: re.Match) -> str:
        year = int(m.group(4)) if len(m.group(4)) == 4 else None
        for part in (m.group(1), m.group(3), m.group(4) if year else None):
            if part:
                out.append(Num(float(int(part)), 1.0, False, part))
        return " " * len(m.group(0))

    text = _DATE.sub(date, text)
    for m in _NUMBER.finditer(text):
        if m.group("grouped"):
            whole = m.group("grouped").replace(m.group("sep"), "")
            frac = (m.group("gfrac") or "")[1:]
        else:
            whole, frac = m.group("whole"), m.group("frac") or ""
        scale = _scale_of(m.group("scale"))
        value = float(f"{whole}.{frac}" if frac else whole) * scale
        step = (10 ** -len(frac) if frac else 1.0) * scale
        out.append(Num(value, step, scale != 1.0, m.group(0).strip()))
    return out


def same_number(a: Num, b: Num, strict: bool = False) -> bool:
    """Equal up to the coarser rounding of the two: "2,7 млн" equals "2 700 000" and "2 683 000".
    strict: up to the finer rounding, so "3 млн" is not "2,7 млн" (a rewrite, not a rounding)."""
    steps = (a.step, b.step)
    return abs(a.value - b.value) <= (min(steps) if strict else max(steps)) / 2 + 1e-9


def has_number(n: Num, pool: list[Num], strict: bool = False) -> bool:
    return any(same_number(n, p, strict) for p in pool)


def parse_json_block(text: str):
    """Parse the first JSON object/array in an LLM reply (tolerates ```json fences and chatter)."""
    if text is None:
        raise ValueError("empty reply")
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*(.*?)```", text, re.S)
    if fence:
        text = fence.group(1).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    for opener, closer in (("{", "}"), ("[", "]")):
        start = text.find(opener)
        end = text.rfind(closer)
        if start != -1 and end > start:
            try:
                return json.loads(text[start:end + 1])
            except json.JSONDecodeError:
                continue
    raise ValueError("no JSON found in reply")


def title_similarity(a: str | None, b: str | None) -> float:
    if not a or not b:
        return 0.0
    na = " ".join(words(a))
    nb = " ".join(words(b))
    return difflib.SequenceMatcher(None, na, nb).ratio()
