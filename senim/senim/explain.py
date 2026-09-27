"""Glass-box explanations: every sentence is a template filled ONLY with measured sensor data.

No LLM writes the "why" text, so the explanation itself cannot hallucinate.
"""

from __future__ import annotations

from .models import (AlibiResult, CitationResult, Claim, FameResult, PhantomResult,
                     ReinterrogationResult, Verdict)
from .scoring import TYPE_RISK

T: dict[str, dict[str, str]] = {
    "alibi_support": {
        "ru": "Подтверждают независимые источники ({n}): {domains}.",
        "kk": "Тәуелсіз дереккөздер растайды ({n}): {domains}.",
        "en": "Independent sources confirm it ({n}): {domains}.",
    },
    "alibi_contradict": {
        "ru": "{domain} говорит иначе: «{quote}»",
        "kk": "{domain} басқаша айтады: «{quote}»",
        "en": "{domain} says otherwise: “{quote}”",
    },
    "alibi_disagree": {
        "ru": "⚖️ Источники расходятся: одни подтверждают, другие опровергают. Сравните цитаты и проверьте сами.",
        "kk": "⚖️ Дереккөздер келіспейді: біреулері растайды, біреулері жоққа шығарады. Дәйексөздерді салыстырып, өзіңіз тексеріңіз.",
        "en": "⚖️ Sources disagree: some confirm, some contradict. Compare the quotes and check for yourself.",
    },
    "alibi_none": {
        "ru": "В найденных источниках нет надёжного подтверждения.",
        "kk": "Табылған дереккөздерде сенімді растау жоқ.",
        "en": "No reliable confirmation in the sources found.",
    },
    "alibi_nosources": {
        "ru": "Поиск не нашёл источников по этому утверждению.",
        "kk": "Іздеу бұл тұжырым бойынша дереккөз таппады.",
        "en": "The search found no sources for this claim.",
    },
    "alibi_rejected": {
        "ru": "Отброшено доказательств: {n} — цитата не найдена на странице (Quote-Lock).",
        "kk": "Қабылданбаған дәлелдер: {n} — дәйексөз бетте табылмады (Quote-Lock).",
        "en": "{n} piece(s) of evidence rejected: the quote is not on the page (Quote-Lock).",
    },
    "alibi_off": {
        "ru": "Поиск доказательств не работал ({note}).",
        "kk": "Дәлел іздеу жұмыс істемеді ({note}).",
        "en": "Evidence search did not run ({note}).",
    },
    "alibi_weak": {
        "ru": "Не засчитано цитат: {n} — в них нет самого числа или даты.",
        "kk": "Есепке алынбаған дәйексөздер: {n} — оларда санның не күннің өзі жоқ.",
        "en": "{n} quote(s) not counted: they don't contain the number or date itself.",
    },
    "rei_summary": {
        "ru": "Переспросили {n} {times} у {m} {models}: согласны — {agree}, другой ответ — {contra}, не знают — {unsure}.",
        "kk": "{m} модельден {n} рет қайта сұрадық: келіседі — {agree}, басқа жауап — {contra}, білмейді — {unsure}.",
        "en": "Re-asked {n} times across {m} models: {agree} agree, {contra} gave a different answer, {unsure} don't know.",
    },
    "rei_values": {
        "ru": "Другие ответы: {values}.",
        "kk": "Басқа жауаптар: {values}.",
        "en": "Other answers: {values}.",
    },
    "phantom_bluff": {
        "ru": "Контрольный вопрос: {model} уверенно рассказал о «{fake}», которого не существует. Его уверенность в таких вопросах ничего не доказывает.",
        "kk": "Бақылау сұрағы: {model} мүлде жоқ «{fake}» туралы сенімді түрде айтып берді. Мұндай сұрақтардағы сенімділігі ештеңені дәлелдемейді.",
        "en": "Control question: {model} confidently described “{fake}”, which does not exist. Its confidence on this kind of question proves nothing.",
    },
    "phantom_partial": {
        "ru": "Контрольный вопрос: про несуществующего «{fake}» {model} выдумал факты в {k} из {n} попыток.",
        "kk": "Бақылау сұрағы: {model} жоқ «{fake}» туралы {n} рет сұрағанда {k} рет фактілерді ойдан шығарды.",
        "en": "Control question: about the non-existent “{fake}”, {model} invented facts in {k} of {n} tries.",
    },
    "phantom_honest": {
        "ru": "Контрольный вопрос: {model} честно ответил, что не знает несуществующего «{fake}», — хороший знак.",
        "kk": "Бақылау сұрағы: {model} жоқ «{fake}» туралы білмейтінін адал айтты — жақсы белгі.",
        "en": "Control question: {model} honestly said it doesn't know the non-existent “{fake}” — a good sign.",
    },
    "fame_famous": {
        "ru": "«{label}» — очень известная тема ({views} просмотров Википедии за год): ИИ знает её хорошо, а ошибки здесь легко проверить.",
        "kk": "«{label}» — өте танымал тақырып (Уикипедияда жылына {views} қаралым): ЖИ оны жақсы біледі, қатені тексеру оңай.",
        "en": "“{label}” is very well known ({views} Wikipedia views a year): AI knows it well and errors are easy to check.",
    },
    "fame_known": {
        "ru": "«{label}» — умеренно известная тема ({views} просмотров Википедии за год).",
        "kk": "«{label}» — орташа танымал тақырып (Уикипедияда жылына {views} қаралым).",
        "en": "“{label}” is moderately known ({views} Wikipedia views a year).",
    },
    "fame_rare": {
        "ru": "«{label}» — редкая тема (всего {views} просмотров Википедии за год): ИИ мало о ней читал, конкретные детали могут быть догадкой.",
        "kk": "«{label}» — сирек тақырып (Уикипедияда жылына бар болғаны {views} қаралым): ЖИ бұл туралы аз оқыған, нақты мәліметтер болжам болуы мүмкін.",
        "en": "“{label}” is a rare topic (only {views} Wikipedia views a year): AI has read little about it, so specifics may be guesses.",
    },
    "fame_unknown": {
        "ru": "Для «{entity}» нет статьи в казахской, русской или английской Википедии — ИИ почти ничего не мог об этом прочитать.",
        "kk": "«{entity}» туралы қазақ, орыс не ағылшын Уикипедиясында мақала жоқ — ЖИ бұл туралы ештеңе дерлік оқи алмады.",
        "en": "There is no kk/ru/en Wikipedia article for “{entity}” — AI could have read almost nothing about it.",
    },
    "type_risk": {
        "ru": "Точные числа, даты, цитаты, законы и ссылки — самые частые места ошибок ИИ.",
        "kk": "Нақты сандар, күндер, дәйексөздер, заңдар мен сілтемелер — ЖИ-дің ең жиі қателесетін тұстары.",
        "en": "Exact numbers, dates, quotes, laws and references are where AI errs most often.",
    },
    "not_checkable": {
        "ru": "Это мнение, совет или прогноз — проверить его как факт нельзя.",
        "kk": "Бұл пікір, кеңес не болжам — оны факт ретінде тексеру мүмкін емес.",
        "en": "This is an opinion, advice or prediction — it can't be fact-checked.",
    },
    "cit_fabricated": {
        "ru": "👻 Источник «{raw}» не существует.",
        "kk": "👻 «{raw}» дереккөзі жоқ.",
        "en": "👻 The source “{raw}” does not exist.",
    },
    "cit_frankenstein": {
        "ru": "🧟 Источник «{raw}» реальный, но детали перепутаны: {fields}.",
        "kk": "🧟 «{raw}» дереккөзі шын, бірақ мәліметтері шатастырылған: {fields}.",
        "en": "🧟 “{raw}” is real, but its details are wrong: {fields}.",
    },
    "cit_never_existed": {
        "ru": "👻 Страницы {raw} никогда не существовало (её нет даже в Интернет-архиве).",
        "kk": "👻 {raw} беті ешқашан болмаған (Интернет-мұрағатта да жоқ).",
        "en": "👻 The page {raw} never existed (not even in the Internet Archive).",
    },
    "cit_dead_link": {
        "ru": "Ссылка {raw} больше не работает (копия есть в Интернет-архиве).",
        "kk": "{raw} сілтемесі енді жұмыс істемейді (көшірмесі Интернет-мұрағатта бар).",
        "en": "The link {raw} is dead (a copy exists in the Internet Archive).",
    },
    "cit_not_supporting": {
        "ru": "⚠️ Источник «{raw}» существует, но не говорит этого.",
        "kk": "⚠️ «{raw}» дереккөзі бар, бірақ мұны айтпайды.",
        "en": "⚠️ “{raw}” exists but does not say this.",
    },
    "cit_supports": {
        "ru": "✅ Источник «{raw}» существует и подтверждает это.",
        "kk": "✅ «{raw}» дереккөзі бар және мұны растайды.",
        "en": "✅ “{raw}” exists and supports this.",
    },
    "cit_unverifiable_text": {
        "ru": "Источник «{raw}» существует, но его текст недоступен для проверки утверждения.",
        "kk": "«{raw}» дереккөзі бар, бірақ тұжырымды тексеруге мәтіні қолжетімсіз.",
        "en": "“{raw}” exists, but its text is not available to check the claim.",
    },
    "cit_unchecked": {
        "ru": "Источник «{raw}» проверить автоматически не удалось — проверьте вручную.",
        "kk": "«{raw}» дереккөзін автоматты түрде тексеру мүмкін болмады — қолмен тексеріңіз.",
        "en": "Could not check “{raw}” automatically — check it by hand.",
    },
    "tip_number": {
        "ru": "Проверьте сами: найдите это число или дату на официальном сайте (stat.gov.kz, egov.kz) или в Википедии — не в ответе другого ИИ.",
        "kk": "Өзіңіз тексеріңіз: бұл санды не күнді ресми сайттан (stat.gov.kz, egov.kz) немесе Уикипедиядан іздеңіз — басқа ЖИ жауабынан емес.",
        "en": "Check it yourself: find this number or date on an official site or Wikipedia — not in another AI's answer.",
    },
    "tip_law": {
        "ru": "Проверьте сами: найдите номер и дату закона на adilet.zan.kz.",
        "kk": "Өзіңіз тексеріңіз: заңның нөмірі мен күнін adilet.zan.kz сайтынан табыңыз.",
        "en": "Check it yourself: look up the law's number and date on adilet.zan.kz.",
    },
    "tip_citation": {
        "ru": "Проверьте сами: вставьте название статьи или цитату в кавычках в Google Scholar или поиск.",
        "kk": "Өзіңіз тексеріңіз: мақала атауын не дәйексөзді тырнақшамен Google Scholar-ға немесе іздеуге қойыңыз.",
        "en": "Check it yourself: paste the article title or the quote in quotation marks into Google Scholar or a search engine.",
    },
    "tip_default": {
        "ru": "Проверьте сами: найдите два независимых источника, не связанных с ИИ.",
        "kk": "Өзіңіз тексеріңіз: ЖИ-ге қатысы жоқ екі тәуелсіз дереккөз табыңыз.",
        "en": "Check it yourself: find two independent sources that are not AI-generated.",
    },
}

FIELD_NAMES = {
    "title": {"ru": "название", "kk": "атауы", "en": "title"},
    "year": {"ru": "год", "kk": "жылы", "en": "year"},
    "authors": {"ru": "авторы", "kk": "авторлары", "en": "authors"},
}


def ru_plural(n: int, one: str, few: str, many: str) -> str:
    if n % 10 == 1 and n % 100 != 11:
        return one
    if 2 <= n % 10 <= 4 and not 12 <= n % 100 <= 14:
        return few
    return many


def t(key: str, lang: str, **kw) -> str:
    table = T[key]
    return table.get(lang, table["en"]).format(**kw)


def _short(s: str, n: int = 160) -> str:
    s = " ".join((s or "").split())
    return s if len(s) <= n else s[: n - 1] + "…"


def _model_name(model_id: str) -> str:
    return model_id.split("/")[-1] if model_id else "AI"


def _fmt_views(v: int) -> str:
    return f"{v:,}".replace(",", " ")


def tip_for(claim: Claim, lang: str) -> str:
    if claim.type in ("number", "date"):
        return t("tip_number", lang)
    if claim.type == "law":
        return t("tip_law", lang)
    if claim.type in ("citation", "quote"):
        return t("tip_citation", lang)
    return t("tip_default", lang)


def citation_reason(c: CitationResult, lang: str) -> str:
    raw = _short(c.raw, 90)
    if c.verdict == "frankenstein":
        fields = ", ".join(FIELD_NAMES.get(m, {}).get(lang, m) for m in c.mismatches)
        return t("cit_frankenstein", lang, raw=raw, fields=fields)
    return t(f"cit_{c.verdict}", lang, raw=raw)


def reasons(claim: Claim, alibi: AlibiResult, rei: ReinterrogationResult, ph: PhantomResult,
            fame: FameResult, cits: list[CitationResult], lang: str) -> list[str]:
    out: list[str] = []
    has_contra = False
    # 1. Alibi
    if alibi.status in ("off", "error"):
        out.append(t("alibi_off", lang, note=alibi.note or alibi.status))
    elif alibi.status == "ok":
        locked = [e for e in alibi.evidence if e.locked]
        contra = [e for e in locked if e.stance == "contradicts"]
        has_contra = bool(contra)
        for e in sorted(contra, key=lambda e: e.tier)[:2]:
            out.append(t("alibi_contradict", lang, domain=e.domain, quote=_short(e.quote)))
        if alibi.support_domains:
            out.append(t("alibi_support", lang, n=len(alibi.support_domains), domains=", ".join(alibi.support_domains[:4])))
        witnesses_agree = rei.status == "ok" and rei.answers and rei.agree_share >= 0.8 and rei.contradict_share == 0
        if contra and (alibi.support_domains or (len(alibi.contradict_domains) <= 1 and witnesses_agree)):
            out.append(t("alibi_disagree", lang))
        elif not contra:
            out.append(t("alibi_nosources" if alibi.note == "no sources found" else "alibi_none", lang))
        if alibi.rejected_quotes:
            out.append(t("alibi_rejected", lang, n=alibi.rejected_quotes))
        if alibi.weak_quotes:
            out.append(t("alibi_weak", lang, n=alibi.weak_quotes))
    # 2. Re-interrogation
    if rei.status == "ok" and rei.answers:
        n = len(rei.answers)
        m = len({a.model for a in rei.answers})
        out.append(t("rei_summary", lang, n=n, m=m, times=ru_plural(n, "раз", "раза", "раз"),
                     models="модели" if m == 1 else "моделей",
                     agree=sum(a.relation == "agree" for a in rei.answers),
                     contra=sum(a.relation == "contradict" for a in rei.answers),
                     unsure=sum(a.relation == "unsure" for a in rei.answers)))
        others = list(dict.fromkeys(f"{_model_name(a.model)}: «{_short(a.answer, 60)}»"
                                     for a in rei.answers if a.relation == "contradict"))
        if others:
            out.append(t("rei_values", lang, values="; ".join(others[:3])))
    # 3. Phantom twin
    if ph.status == "ok" and ph.answers:
        k, n = sum(a.fabricated for a in ph.answers), len(ph.answers)
        key = "phantom_bluff" if k == n else ("phantom_honest" if k == 0 else "phantom_partial")
        out.append(t(key, lang, model=_model_name(ph.target_model), fake=ph.fake_entity, k=k, n=n))
    # 4. Fame
    if fame.status == "ok":
        if fame.bucket == "unknown":
            out.append(t("fame_unknown", lang, entity=claim.entity or "?"))
        else:
            out.append(t(f"fame_{fame.bucket}", lang, label=fame.label or claim.entity, views=_fmt_views(fame.total_views)))
    # 5. Citations
    for c in cits:
        out.append(citation_reason(c, lang))
    # Claim type
    if TYPE_RISK.get(claim.type, 0) >= 1.0 and not has_contra:
        out.append(t("type_risk", lang))
    return out


def build_verdict(claim: Claim, label: str, p: float | None, feats: dict[str, float],
                  alibi: AlibiResult, rei: ReinterrogationResult, ph: PhantomResult,
                  fame: FameResult, cits: list[CitationResult], lang: str) -> Verdict:
    if label == "not_checkable":
        return Verdict(claim_id=claim.id, label="not_checkable", reasons=[t("not_checkable", lang)])
    v = Verdict(claim_id=claim.id, label=label, p_wrong=round(p, 3) if p is not None else None,
                features={k: round(x, 3) for k, x in feats.items()},
                reasons=reasons(claim, alibi, rei, ph, fame, cits, lang), tip=tip_for(claim, lang))
    locked = [e for e in alibi.evidence if e.locked]
    pick = next((e for e in sorted(locked, key=lambda e: e.tier) if e.stance == "contradicts"), None) \
        or next((e for e in sorted(locked, key=lambda e: e.tier) if e.stance == "supports"), None)
    if pick:
        v.source_quote, v.source_url = pick.quote, pick.url
    if label == "contradicted" and alibi.suggested_correction:
        v.suggested_correction = alibi.suggested_correction
    return v
