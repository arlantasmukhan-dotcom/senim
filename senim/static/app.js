"use strict";

/* ================= i18n ================= */
const I18N = {
  ru: {
    tagline: "Полиграф для ответов ИИ",
    answerLabel: "Ответ ИИ",
    answerPlaceholder: "Вставьте сюда ответ ChatGPT, Gemini или другого ИИ…",
    questionLabel: "Ваш вопрос к ИИ (необязательно)",
    authorLabel: "Какой ИИ написал ответ?",
    unknownAuthor: "Не знаю",
    modeQuick: "Быстро", modeQuickHint: "Алиби, известность, ссылки",
    modeDeep: "Полный допрос", modeDeepHint: "Все 5 датчиков + контрольный вопрос",
    run: "Допросить ответ", running: "Идёт допрос…", example: "Пример",
    answerHeading: "Ответ, разобранный на утверждения",
    stageExtract: "Разбиваю ответ на утверждения…", stageSensors: "Датчики работают: {done}/{total}", stageDone: "Готово",
    selectHint: "Нажмите на подчёркнутое утверждение, чтобы открыть его карточку полиграфа.",
    unlocated: "Утверждения без точного места в тексте",
    citationsHeading: "Ссылки из ответа",
    truncated: "Текст был слишком длинным — проверена только первая часть.",
    labels: { confirmed: "Подтверждено", unconfirmed: "Не подтверждено", suspicious: "Подозрительно",
      contradicted: "Опровергнуто", not_checkable: "Мнение / не факт", pending: "Проверяется…" },
    sensors: { alibi: "Алиби (источники)", reinterrogation: "Повторный допрос", phantom: "Фантом-двойник",
      fame: "Известность темы", citations: "Вскрытие ссылок" },
    sensorState: { off: "выключен", skipped: "не применим", error: "ошибка", pending: "…", none: "нет ссылок" },
    pWrong: "Вероятность ошибки", why: "Почему", sourceSays: "Что говорит источник",
    correction: "Возможное исправление", correctionNote: "предложено ИИ на основе цитаты выше — сверьте с источником",
    tip: "Как проверить самому", raw: "Сырые данные датчиков",
    evLocked: "цитата найдена на странице", evRejected: "цитата НЕ найдена на странице — отброшено",
    stance: { supports: "подтверждает", contradicts: "опровергает" },
    rel: { agree: "согласен", contradict: "другой ответ", unsure: "не знает" },
    phantomQ: "Вопрос про несуществующего двойника", phantomVerified: "нет ни в одной Википедии (kk/ru/en)",
    phantomUnverified: "несуществование не проверено", fabricated: "выдумал", honest: "не выдумал",
    fameViews: "просмотров Википедии за 12 мес.",
    citLabels: { fabricated: "Выдумана", frankenstein: "Детали перепутаны", not_supporting: "Не подтверждает",
      supports: "Подтверждает", dead_link: "Ссылка мертва", never_existed: "Никогда не существовала",
      unverifiable_text: "Текст недоступен", unchecked: "Не проверено" },
    footer: "{s} с · {calls} вызовов ИИ · ${cost} · веса: {w}",
    health: { llm: "ИИ подключён", nollm: "нет ключа OpenRouter", search: "поиск: {s}" },
    errors: { no_llm_key: "На сервере не задан OPENROUTER_API_KEY. Добавьте ключ в файл .env и перезапустите сервер.",
      too_short: "Текст слишком короткий для проверки.", network: "Сервер недоступен." },
  },
  kk: {
    tagline: "ЖИ жауаптарына арналған полиграф",
    answerLabel: "ЖИ жауабы",
    answerPlaceholder: "ChatGPT, Gemini немесе басқа ЖИ жауабын осында қойыңыз…",
    questionLabel: "ЖИ-ге қойған сұрағыңыз (міндетті емес)",
    authorLabel: "Жауапты қай ЖИ жазды?",
    unknownAuthor: "Білмеймін",
    modeQuick: "Жылдам", modeQuickHint: "Алиби, танымалдық, сілтемелер",
    modeDeep: "Толық тексеру", modeDeepHint: "5 датчиктің бәрі + бақылау сұрағы",
    run: "Жауапты тексеру", running: "Тексерілуде…", example: "Мысал",
    answerHeading: "Тұжырымдарға бөлінген жауап",
    stageExtract: "Жауапты тұжырымдарға бөлудемін…", stageSensors: "Датчиктер жұмыс істеуде: {done}/{total}", stageDone: "Дайын",
    selectHint: "Полиграф карточкасын ашу үшін астын сызылған тұжырымды басыңыз.",
    unlocated: "Мәтінде нақты орны жоқ тұжырымдар",
    citationsHeading: "Жауаптағы сілтемелер",
    truncated: "Мәтін тым ұзын — тек бірінші бөлігі тексерілді.",
    labels: { confirmed: "Расталды", unconfirmed: "Расталмады", suspicious: "Күдікті",
      contradicted: "Жоққа шығарылды", not_checkable: "Пікір / факт емес", pending: "Тексерілуде…" },
    sensors: { alibi: "Алиби (дереккөздер)", reinterrogation: "Қайта сұрау", phantom: "Фантом-егіз",
      fame: "Тақырып танымалдығы", citations: "Сілтемелерді тексеру" },
    sensorState: { off: "өшірулі", skipped: "қолданылмайды", error: "қате", pending: "…", none: "сілтеме жоқ" },
    pWrong: "Қате болу ықтималдығы", why: "Неге", sourceSays: "Дереккөз не дейді",
    correction: "Ықтимал түзету", correctionNote: "жоғарыдағы дәйексөз бойынша ЖИ ұсынды — дереккөзбен салыстырыңыз",
    tip: "Өзіңіз қалай тексеруге болады", raw: "Датчиктердің бастапқы деректері",
    evLocked: "дәйексөз бетте табылды", evRejected: "дәйексөз бетте ТАБЫЛМАДЫ — қабылданбады",
    stance: { supports: "растайды", contradicts: "жоққа шығарады" },
    rel: { agree: "келіседі", contradict: "басқа жауап", unsure: "білмейді" },
    phantomQ: "Жоқ егіз туралы сұрақ", phantomVerified: "ешбір Уикипедияда жоқ (kk/ru/en)",
    phantomUnverified: "жоқ екені тексерілмеді", fabricated: "ойдан шығарды", honest: "ойдан шығармады",
    fameViews: "Уикипедия қаралымы (12 ай)",
    citLabels: { fabricated: "Ойдан шығарылған", frankenstein: "Мәліметтер шатасқан", not_supporting: "Растамайды",
      supports: "Растайды", dead_link: "Сілтеме өлі", never_existed: "Ешқашан болмаған",
      unverifiable_text: "Мәтін қолжетімсіз", unchecked: "Тексерілмеді" },
    footer: "{s} с · ЖИ-ге {calls} сұраныс · ${cost} · салмақтар: {w}",
    health: { llm: "ЖИ қосулы", nollm: "OpenRouter кілті жоқ", search: "іздеу: {s}" },
    errors: { no_llm_key: "Серверде OPENROUTER_API_KEY берілмеген. Кілтті .env файлына қосып, серверді қайта іске қосыңыз.",
      too_short: "Мәтін тексеру үшін тым қысқа.", network: "Сервер қолжетімсіз." },
  },
  en: {
    tagline: "A polygraph for AI answers",
    answerLabel: "AI answer",
    answerPlaceholder: "Paste an answer from ChatGPT, Gemini or another AI…",
    questionLabel: "Your question to the AI (optional)",
    authorLabel: "Which AI wrote it?",
    unknownAuthor: "Not sure",
    modeQuick: "Quick", modeQuickHint: "Alibi, fame, references",
    modeDeep: "Full interrogation", modeDeepHint: "All 5 sensors + control question",
    run: "Interrogate", running: "Interrogating…", example: "Example",
    answerHeading: "The answer, split into claims",
    stageExtract: "Splitting the answer into claims…", stageSensors: "Sensors running: {done}/{total}", stageDone: "Done",
    selectHint: "Click an underlined claim to open its polygraph card.",
    unlocated: "Claims without an exact place in the text",
    citationsHeading: "References in the answer",
    truncated: "The text was too long — only the first part was checked.",
    labels: { confirmed: "Confirmed", unconfirmed: "Unconfirmed", suspicious: "Suspicious",
      contradicted: "Contradicted", not_checkable: "Opinion / not a fact", pending: "Checking…" },
    sensors: { alibi: "Alibi (sources)", reinterrogation: "Re-interrogation", phantom: "Phantom Twin",
      fame: "Fame Meter", citations: "Citation Autopsy" },
    sensorState: { off: "off", skipped: "n/a", error: "error", pending: "…", none: "no refs" },
    pWrong: "Chance it's wrong", why: "Why", sourceSays: "What the source says",
    correction: "Possible correction", correctionNote: "suggested by AI from the quote above — compare with the source",
    tip: "Check it yourself", raw: "Raw sensor data",
    evLocked: "quote found on the page", evRejected: "quote NOT on the page — rejected",
    stance: { supports: "supports", contradicts: "contradicts" },
    rel: { agree: "agrees", contradict: "different answer", unsure: "doesn't know" },
    phantomQ: "Question about a non-existent twin", phantomVerified: "not on any Wikipedia (kk/ru/en)",
    phantomUnverified: "non-existence not verified", fabricated: "invented facts", honest: "didn't invent",
    fameViews: "Wikipedia views in 12 months",
    citLabels: { fabricated: "Fabricated", frankenstein: "Details wrong", not_supporting: "Doesn't support",
      supports: "Supports", dead_link: "Dead link", never_existed: "Never existed",
      unverifiable_text: "Text unavailable", unchecked: "Unchecked" },
    footer: "{s} s · {calls} AI calls · ${cost} · weights: {w}",
    health: { llm: "AI connected", nollm: "no OpenRouter key", search: "search: {s}" },
    errors: { no_llm_key: "OPENROUTER_API_KEY is not set on the server. Add it to .env and restart.",
      too_short: "The text is too short to check.", network: "Server unreachable." },
  },
};

const EXAMPLES = {
  ru: "Абай Кунанбаев — великий казахский поэт и мыслитель. Он родился в 1847 году в Чингизских горах. " +
      "Абай перевёл на казахский язык произведения Пушкина и Лермонтова. Его главный прозаический труд — «Слова назидания», " +
      "состоящий из 45 «слов». Поэт умер в 1904 году. Согласно исследованию (Seitkali, 2021, doi:10.5555/senim.demo.2021), " +
      "Абай написал около 170 стихотворений. Я считаю, что это лучший поэт в истории Казахстана.",
  kk: "Қазақстан тәуелсіздігін 1991 жылы 25 желтоқсанда жариялады. Елорда 1997 жылы Алматыдан Ақмолаға көшірілді. " +
      "Балқаш көлінің батыс бөлігі тұщы, ал шығыс бөлігі тұзды. Менің ойымша, Балқаш — Қазақстандағы ең әдемі көл.",
  en: "Al-Farabi, known as the \"Second Teacher\" after Aristotle, was born around 870 in Farab on the Syr Darya. " +
      "The Semipalatinsk nuclear test site was closed in 1989 " +
      "(source: https://www.stat.gov.kz/en/semipalatinsk-test-site-closure-1989). " +
      "Kazakhstan is the largest landlocked country in the world.",
};

const ORDER = ["contradicted", "suspicious", "unconfirmed", "confirmed", "not_checkable", "pending"];
const SENSORS = ["alibi", "reinterrogation", "phantom", "fame", "citations"];

/* ================= state ================= */
const state = {
  lang: localGet("senim.lang") || "ru",
  mode: localGet("senim.mode") || "deep",
  text: "", claims: [], citations: [], cits: null,
  sensors: {}, verdicts: {}, selected: null, running: false, sensorTotal: 0, sensorDone: 0,
};

function localGet(k) { try { return localStorage.getItem(k); } catch { return null; } }
function localSet(k, v) { try { localStorage.setItem(k, v); } catch { /* private mode */ } }
const L = () => I18N[state.lang];
const fmt = (s, o) => s.replace(/\{(\w+)\}/g, (_, k) => (o[k] ?? ""));
const $ = (id) => document.getElementById(id);

/** Safe element builder: text is always inserted as text nodes (no innerHTML → no XSS from AI answers). */
function h(tag, attrs = {}, ...children) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v == null || v === false) continue;
    if (k === "class") el.className = v;
    else if (k.startsWith("on")) el.addEventListener(k.slice(2), v);
    else el.setAttribute(k, v);
  }
  for (const c of children.flat()) {
    if (c == null || c === false) continue;
    el.append(c instanceof Node ? c : document.createTextNode(String(c)));
  }
  return el;
}

/* ================= static UI ================= */
function applyI18n() {
  document.documentElement.lang = state.lang;
  document.querySelectorAll("[data-i18n]").forEach((el) => { el.textContent = L()[el.dataset.i18n]; });
  document.querySelectorAll("[data-i18n-placeholder]").forEach((el) => { el.placeholder = L()[el.dataset.i18nPlaceholder]; });
  document.querySelectorAll(".lang button").forEach((b) => b.classList.toggle("active", b.dataset.lang === state.lang));
  document.querySelectorAll(".seg").forEach((b) => {
    b.classList.toggle("active", b.dataset.mode === state.mode);
    b.setAttribute("aria-checked", b.dataset.mode === state.mode);
  });
  $("run").textContent = state.running ? L().running : L().run;
  const unknown = $("author").querySelector('option[value=""]');
  if (unknown) unknown.textContent = L().unknownAuthor;
  renderHealth();
  if (state.claims.length) renderAll();
}

let health = null;
async function loadHealth() {
  try {
    health = await (await fetch("/api/health")).json();
    const sel = $("author");
    sel.replaceChildren(...health.author_models.map((m) => h("option", { value: m.id }, m.label)),
      h("option", { value: "" }, L().unknownAuthor));
  } catch { health = null; }
  renderHealth();
}

function renderHealth() {
  const box = $("health");
  if (!health) { box.replaceChildren(); return; }
  box.replaceChildren(
    h("span", { class: "pill " + (health.llm ? "on" : "off") }, health.llm ? L().health.llm : L().health.nollm),
    h("span", { class: "pill" }, fmt(L().health.search, { s: health.search })),
  );
}

/* ================= running a check ================= */
async function run() {
  const text = $("answer").value.trim();
  if (!text || state.running) return;
  Object.assign(state, { text, claims: [], citations: [], cits: null, sensors: {}, verdicts: {}, selected: null,
    running: true, sensorTotal: 0, sensorDone: 0, stage: "extract", truncated: false });
  $("error").hidden = true;
  $("results").hidden = false;
  $("footer").textContent = "";
  $("run").disabled = true;
  applyI18n();
  renderAll();
  try {
    const res = await fetch("/api/check", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, question: $("question").value.trim() || null,
        author_model: $("author").value || null, ui_lang: state.lang, mode: state.mode }),
    });
    if (!res.ok || !res.body) throw new Error("HTTP " + res.status);
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buf = "";
    for (;;) {
      const { value, done } = await reader.read();
      if (done) break;
      buf += decoder.decode(value, { stream: true });
      let i;
      while ((i = buf.indexOf("\n\n")) >= 0) {
        const block = buf.slice(0, i); buf = buf.slice(i + 2);
        const ev = /^event: (.*)$/m.exec(block)?.[1];
        const data = /^data: (.*)$/m.exec(block)?.[1];
        if (ev && data) onEvent(ev, JSON.parse(data));
      }
    }
  } catch (e) {
    showError(L().errors.network + " " + e.message);
  } finally {
    state.running = false;
    state.stage = "done";
    $("run").disabled = false;
    applyI18n();
    renderProgress();
  }
}

function onEvent(ev, data) {
  switch (ev) {
    case "status":
      state.stage = data.stage; state.truncated = data.truncated; break;
    case "claims": {
      state.text = data.text; state.claims = data.claims; state.citations = data.citations;
      state.stage = "sensors";
      const checkable = data.claims.filter((c) => c.checkable).length;
      state.sensorTotal = checkable * (state.mode === "deep" ? 4 : 2) + 1;
      if (!state.selected) {
        const first = data.claims.find((c) => c.checkable) || data.claims[0];
        state.selected = first?.id ?? null;
      }
      break;
    }
    case "sensor":
      (state.sensors[data.claim_id] ||= {})[data.sensor] = data.result;
      state.sensorDone++;
      break;
    case "citations":
      state.cits = data; state.sensorDone++; break;
    case "verdict":
      state.verdicts[data.claim_id] = data; break;
    case "error":
      showError(L().errors[data.code] || data.message); break;
    case "done":
      $("footer").textContent = fmt(L().footer, { s: data.elapsed_s, calls: data.llm_calls, cost: data.cost_usd.toFixed(4), w: data.weights });
      break;
  }
  renderAll();
}

function showError(msg) {
  const box = $("error");
  box.textContent = msg;
  box.hidden = false;
}

/* ================= rendering ================= */
function labelOf(claimId) {
  return state.verdicts[claimId]?.label || "pending";
}

function renderAll() {
  renderProgress();
  renderLegend();
  renderAnswer();
  renderCitations();
  renderCard();
}

function renderProgress() {
  const p = $("progress");
  if (state.stage === "extract" && state.running) {
    p.replaceChildren(h("span", { class: "spinner" }), L().stageExtract);
  } else if (state.running) {
    p.replaceChildren(h("span", { class: "spinner" }),
      fmt(L().stageSensors, { done: Math.min(state.sensorDone, state.sensorTotal), total: state.sensorTotal }));
  } else {
    p.replaceChildren(state.claims.length ? L().stageDone : "");
  }
}

function renderLegend() {
  const counts = {};
  for (const c of state.claims) counts[labelOf(c.id)] = (counts[labelOf(c.id)] || 0) + 1;
  const items = ORDER.filter((k) => counts[k]).map((k) => h("span", { class: `badge b-${k}` }, `${L().labels[k]} · ${counts[k]}`));
  if (state.truncated) items.push(h("span", { class: "badge b-pending" }, L().truncated));
  $("legend").replaceChildren(...items);
}

function worst(ids) {
  return ids.map(labelOf).sort((a, b) => ORDER.indexOf(a) - ORDER.indexOf(b))[0];
}

function renderAnswer() {
  const text = state.text || "";
  const located = state.claims.filter((c) => c.start != null && c.end != null);
  const cuts = new Set([0, text.length]);
  located.forEach((c) => { cuts.add(c.start); cuts.add(c.end); });
  const points = [...cuts].sort((a, b) => a - b);
  const nodes = [];
  for (let i = 0; i < points.length - 1; i++) {
    const [a, b] = [points[i], points[i + 1]];
    const piece = text.slice(a, b);
    const covering = located.filter((c) => c.start <= a && c.end >= b).map((c) => c.id);
    if (!covering.length) { nodes.push(piece); continue; }
    const target = covering.includes(state.selected) ? state.selected : covering[0];
    nodes.push(h("span", {
      class: `hl v-${worst(covering)}` + (covering.includes(state.selected) ? " selected" : ""),
      title: covering.map((id) => L().labels[labelOf(id)]).join(" / "),
      onclick: () => select(target),
    }, piece));
  }
  $("answerView").replaceChildren(...nodes);

  const lost = state.claims.filter((c) => c.start == null);
  $("unlocated").replaceChildren(...(lost.length ? [
    h("h3", {}, L().unlocated),
    ...lost.map((c) => h("button", { class: "chip", onclick: () => select(c.id) },
      h("span", { class: `badge b-${labelOf(c.id)}` }, L().labels[labelOf(c.id)]), " ", c.text)),
  ] : []));
}

function select(id) {
  state.selected = id;
  renderAnswer();
  renderCard();
  if (window.innerWidth < 900) $("polygraph").scrollIntoView({ behavior: "smooth" });
}

function renderCitations() {
  const box = $("citations");
  if (!state.citations.length) { box.replaceChildren(); return; }
  const results = Object.fromEntries((state.cits || []).map((r) => [r.citation_id, r]));
  box.replaceChildren(h("h3", {}, L().citationsHeading), ...state.citations.map((c) => {
    const r = results[c.id];
    const cls = !r ? "pending" : ({ supports: "confirmed", fabricated: "contradicted", never_existed: "contradicted",
      frankenstein: "suspicious", not_supporting: "suspicious", dead_link: "unconfirmed" }[r.verdict] || "not_checkable");
    return h("div", { class: "cit" },
      h("span", { class: `badge b-${cls}` }, r ? L().citLabels[r.verdict] : L().labels.pending),
      h("div", {}, h("div", { class: "raw" }, c.raw),
        r?.found_title ? h("div", { class: "note" }, `→ ${r.found_title}${r.found_year ? ` (${r.found_year})` : ""}`) : null,
        r?.reason ? h("div", { class: "note" }, r.reason) : null));
  }));
}

/* ---------- polygraph card ---------- */
function sensorRisk(claimId, name) {
  if (name === "citations") {
    if (!state.cits) return { state: "pending" };
    const mine = state.cits.filter((r) => r.claim_ids.includes(claimId));
    if (!mine.length) return { state: "none" };
    const w = { fabricated: 1, frankenstein: 1, never_existed: 1, not_supporting: 0.6, dead_link: 0.3 };
    return { risk: Math.max(...mine.map((r) => w[r.verdict] || 0)) };
  }
  const r = state.sensors[claimId]?.[name];
  if (!r) return { state: state.running ? "pending" : "skipped" };
  if (r.status !== "ok") return { state: r.status };
  switch (name) {
    case "alibi": {
      const locked = r.evidence.filter((e) => e.locked);
      if (locked.some((e) => e.stance === "contradicts")) return { risk: 1 };
      if (r.support_domains.length) return { risk: Math.max(0.05, 0.45 - 0.15 * r.support_domains.length) };
      return { risk: 0.6 };
    }
    case "reinterrogation": return r.answers.length ? { risk: 1 - r.agree_share } : { state: "skipped" };
    case "phantom": return { risk: r.bluff };
    case "fame": return { risk: r.tail_risk };
  }
  return { state: "skipped" };
}

function tracePath(risk, seed) {
  // A polygraph needle: calm line for low risk, violent swings for high risk.
  const W = 300, H = 30, mid = H / 2, n = 60;
  let d = `M0 ${mid}`;
  let x = 0;
  for (let i = 1; i <= n; i++) {
    x = (i / n) * W;
    const noise = Math.sin(i * 1.7 + seed) * 0.6 + Math.sin(i * 0.37 + seed * 2) * 0.4;
    const spike = risk > 0.5 && (i + seed) % 9 === 0 ? (risk - 0.5) * 2.2 : 0;
    const amp = (1.5 + risk * 11) * (noise + (i % 2 ? spike : -spike));
    d += ` L${x.toFixed(1)} ${(mid - Math.max(-mid + 1, Math.min(mid - 1, amp))).toFixed(1)}`;
  }
  return d;
}

function riskColor(risk) {
  if (risk >= 0.75) return "var(--bad)";
  if (risk >= 0.5) return "var(--sus)";
  if (risk >= 0.25) return "var(--warn)";
  return "var(--ok)";
}

function traceRow(claimId, name, i) {
  const r = sensorRisk(claimId, name);
  const svgNS = "http://www.w3.org/2000/svg";
  const svg = document.createElementNS(svgNS, "svg");
  svg.setAttribute("viewBox", "0 0 300 30");
  svg.setAttribute("preserveAspectRatio", "none");
  const base = document.createElementNS(svgNS, "line");
  Object.entries({ x1: 0, y1: 15, x2: 300, y2: 15, class: "base" }).forEach(([k, v]) => base.setAttribute(k, v));
  const line = document.createElementNS(svgNS, "path");
  if (r.risk != null) {
    line.setAttribute("d", tracePath(r.risk, i * 3 + claimId.length));
    line.setAttribute("pathLength", "100");
    line.setAttribute("class", "line");
    line.style.stroke = riskColor(r.risk);
  } else {
    line.setAttribute("d", "M0 15 L300 15");
    line.setAttribute("class", "line flat");
    line.style.stroke = "var(--pending)";
  }
  svg.append(base, line);
  const val = r.risk != null ? `${Math.round(r.risk * 100)}%` : L().sensorState[r.state] || r.state;
  return h("div", { class: "trace" }, h("div", { class: "tname" }, L().sensors[name]), svg, h("div", { class: "tval" }, val));
}

function renderCard() {
  const box = $("polygraph");
  const claim = state.claims.find((c) => c.id === state.selected);
  if (!claim) { box.replaceChildren(h("p", { class: "hint" }, L().selectHint)); return; }
  const v = state.verdicts[claim.id];
  const label = labelOf(claim.id);
  const parts = [
    h("span", { class: `badge b-${label}` }, L().labels[label]),
    h("div", { class: "claim-text" }, claim.text),
  ];
  if (v?.p_wrong != null) {
    parts.push(h("div", { class: "meter" },
      h("div", { class: "meter-top" }, h("span", {}, L().pWrong), h("b", {}, `${Math.round(v.p_wrong * 100)}%`)),
      h("div", { class: "meter-bar" }, h("div", { class: "meter-fill", style: `width:${Math.max(3, v.p_wrong * 100)}%;background:${riskColor(v.p_wrong)}` }))));
  }
  if (claim.checkable) {
    parts.push(h("div", { class: "traces" }, SENSORS.map((s, i) => traceRow(claim.id, s, i))));
  }
  if (v?.reasons?.length) {
    parts.push(h("h3", {}, L().why), h("ul", { class: "reasons" }, v.reasons.map((r) => h("li", {}, r))));
  }
  if (v?.source_quote) {
    parts.push(h("h3", {}, L().sourceSays), h("blockquote", { class: "quote" }, `«${v.source_quote}»`,
      v.source_url ? h("a", { href: v.source_url, target: "_blank", rel: "noopener noreferrer" }, v.source_url) : null));
  }
  if (v?.suggested_correction) {
    parts.push(h("h3", {}, L().correction), h("div", { class: "fix" }, h("small", {}, L().correctionNote), v.suggested_correction));
  }
  if (v?.tip) parts.push(h("h3", {}, L().tip), h("div", { class: "tip" }, v.tip));
  if (claim.checkable) parts.push(rawDetails(claim));
  box.replaceChildren(...parts);
}

function rawDetails(claim) {
  const s = state.sensors[claim.id] || {};
  const blocks = [];
  if (s.alibi?.evidence?.length) {
    blocks.push(h("div", { class: "raw-block" }, h("b", {}, L().sensors.alibi + (s.alibi.backend ? ` · ${s.alibi.backend}` : "")),
      h("ul", {}, s.alibi.evidence.map((e) => h("li", {},
        h("span", { class: e.locked ? "lock-ok" : "lock-no" }, e.locked ? "✓ " : "✗ "),
        `[T${e.tier}] ${e.domain} ${L().stance[e.stance] || e.stance}: «${e.quote}» — `,
        h("i", {}, e.locked ? L().evLocked : L().evRejected))))));
  }
  if (s.reinterrogation?.answers?.length) {
    blocks.push(h("div", { class: "raw-block" }, h("b", {}, L().sensors.reinterrogation),
      h("ul", {}, s.reinterrogation.answers.map((a) => h("li", {},
        h("span", { class: "mono" }, a.model.split("/").pop()), ` [${L().rel[a.relation]}] `, a.answer)))));
  }
  if (s.phantom?.status === "ok") {
    const p = s.phantom;
    blocks.push(h("div", { class: "raw-block" }, h("b", {}, `${L().sensors.phantom} · ${p.target_model.split("/").pop()}`),
      h("div", {}, `${L().phantomQ}: `, h("i", {}, p.twin_question)),
      h("div", {}, `«${p.fake_entity}»: ${p.nonexistence_verified ? L().phantomVerified : L().phantomUnverified}`),
      h("ul", {}, p.answers.map((a) => h("li", {},
        h("span", { class: a.fabricated ? "lock-no" : "lock-ok" }, a.fabricated ? L().fabricated : L().honest), ": ", a.answer)))));
  }
  if (s.fame?.status === "ok" && s.fame.qid) {
    const f = s.fame;
    blocks.push(h("div", { class: "raw-block" }, h("b", {}, L().sensors.fame),
      h("div", {}, `${f.label} — ${f.description || ""} (`, h("a", { href: `https://www.wikidata.org/wiki/${f.qid}`, target: "_blank", rel: "noopener noreferrer" }, f.qid), ")"),
      h("div", {}, `${f.total_views.toLocaleString()} ${L().fameViews}: ` +
        Object.entries(f.views).map(([l, n]) => `${l} ${n.toLocaleString()}`).join(" · "))));
  }
  return h("details", {}, h("summary", {}, L().raw), blocks);
}

/* ================= wiring ================= */
document.querySelectorAll(".lang button").forEach((b) => b.addEventListener("click", () => {
  state.lang = b.dataset.lang; localSet("senim.lang", state.lang); applyI18n();
}));
document.querySelectorAll(".seg").forEach((b) => b.addEventListener("click", () => {
  state.mode = b.dataset.mode; localSet("senim.mode", state.mode); applyI18n();
}));
$("run").addEventListener("click", run);
$("example").addEventListener("click", () => { $("answer").value = EXAMPLES[state.lang]; $("answer").focus(); });
$("answer").addEventListener("keydown", (e) => { if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) run(); });

applyI18n();
loadHealth();
