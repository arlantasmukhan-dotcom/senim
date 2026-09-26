# SENIM (Сенім) — a polygraph for AI answers
### WIT Teens Hackathon · Case 1 «AI Trust: можно ли доверять ответу ИИ?»

> *«Сенім» = "trust" in Kazakh.*
> Detectives don't just ask a suspect "are you lying?". They check the alibi, ask the same question again later, and ask a **control question they already know the answer to**. SENIM interrogates an AI answer the same way, then explains in plain words *why* each sentence can or can't be trusted.

---

## 0. 200-WORD PITCH SUMMARY (paste-ready, under 200 words)

**Problem.** 76% of young Kazakhstanis use AI, mostly for studying. AI sounds equally confident when right and when wrong, especially on Kazakh-language and local topics. In one study, 18% of GPT-4's academic citations were fabricated.

**SENIM is a polygraph for AI answers**, available as a Telegram bot and a browser extension. It splits an answer into claims and runs five "sensors":
1. **Alibi check.** Searches trusted sources (including adilet.zan.kz and stat.gov.kz). Evidence counts only if the exact quote is really on the page, so the checker can't invent evidence either.
2. **Re-interrogation.** Asks three different AIs the same question again. Stories that change are guesses.
3. **Phantom Twin.** Our control question: we ask the same question about an invented person or place. If the AI answers the fake confidently, its confidence means nothing.
4. **Fame Meter.** Wikipedia popularity data shows how much the AI could have learned about the topic, since rare topics produce most errors.
5. **Citation Autopsy.** Checks that every reference exists and actually says what the AI claims.

Every verdict comes with a plain-language reason and a corrected version. **Trust Gym** turns this into AI-literacy lessons for Kazakhstan's 165,000 teachers.

---

## 1. Understanding the problem (15 pts)

### 1.1 Why AI answers are hard to trust
| Fact | Source |
|---|---|
| 76.2% of Kazakhstanis aged 18–29 use AI; study/self-development is the #1 use (48.7%) | KazISS survey, Oct–Nov 2025 |
| Kazakhstan leads Central Asia in ChatGPT use; 165,000 educators got ChatGPT Edu | OpenAI / Qazinform / EdTech Innovation Hub |
| LLMs are much weaker in **Kazakh** than Russian; the best models reach about 76% on Kazakhstan-specific school knowledge | KazMMLU (ACL 2025) |
| On the least popular ("long-tail") facts, even GPT-3-class models reached only 16–19% accuracy; scaling doesn't fix the tail | Mallen et al., ACL 2023 (PopQA) |
| 55% (GPT-3.5) and 18% (GPT-4) of generated academic citations were fabricated | Walters & Wilder, *Scientific Reports* 2023 |
| Some models confidently describe **non-existent** entities over 80% of the time | HalluLens, ACL 2025 |

### 1.2 The real root problem
AI errors are hard to catch because:
1. **Tone carries no information.** The wrong sentence sounds exactly as fluent as the right one.
2. **Errors hide inside correct answers.** Nine true sentences and one fake date; people check the whole answer or nothing.
3. **Users can't tell *where* AI is weak.** Nobody knows "AI is great on Newton, terrible on a district history of Zhetysu".
4. **Existing checkers are black boxes.** A tool that says "73% trustworthy" without explaining why is just *another AI you have to trust*.
5. **Local gap.** Kazakh-language and Kazakhstan-specific facts are where AI is weakest *and* where checkers have the fewest sources.

### 1.3 Target users
| Segment | Pain |
|---|---|
| **Students 14–22** (UNT/ENT prep, homework, essays, university papers) | Lose points or get accused of plagiarism for fake facts and citations |
| **Teachers** | Can't verify what students bring from AI, and must teach AI literacy with no tools |
| **Parents / everyday users** | Health, legal and money answers from AI |
| **Journalists, lawyers, researchers** | Fake quotes, laws and precedents |

## 2. Existing solutions and the gap
| Product | What it does | What it's missing |
|---|---|---|
| Gemini "Double-check" | Colors sentences green/orange using Google Search | Only one signal (search). Gemini-only. No "why". Nothing for Kazakh sources. |
| Aretify, Facticity, FactSentinel | Extract claims → web search → verdict | Same one-signal pipeline; the verdict itself comes from an LLM that can hallucinate |
| Perplexity | Answers with citations | Citations can still misrepresent the source; doesn't check *other* AIs |
| Research: SelfCheckGPT, semantic entropy, FActScore/SAFE | Strong detection methods | Lab code, not a product; English only; no explanation for normal people |

**The gap SENIM fills:** multi-signal detection (like a polygraph, not one sensor) + a checker that can't invent its own evidence + **explanations built only from measured signals** + Kazakh/Russian local sources + prevention and teaching.

## 3. The solution (20 pts)

### 3.1 User flow (under 20 seconds)
1. Forward an AI answer to the **@SenimBot** Telegram bot (text *or* a screenshot), or click **"Interrogate"** under a ChatGPT/Gemini/Claude answer in the browser extension.
2. SENIM splits the answer into **atomic claims** ("Abai was born in 1845", "the law requires X").
3. Results stream in claim by claim. Each sentence gets underlined like a spell-checker:
   - ✅ **Confirmed:** independent sources agree
   - 🟡 **Unconfirmed:** no contradiction found, but no proof either
   - 🟠 **Suspicious:** the signals say the AI was guessing
   - ❌ **Contradicted:** trusted sources say otherwise (with the correct fact)
   - ⚪ **Opinion / not checkable**
4. Tap any sentence to see its **polygraph card**: five sensor bars, a plain-language "why", the source quote, a corrected sentence, and "how to check this yourself".

### 3.2 Example output (one claim)
> **❌ "Абай Құнанбайұлы родился в 1847 году."**
> **Why you shouldn't trust this:**
> • Alibi: 2 of 2 trusted sources say **1845** (quote from kk.wikipedia.org: "1845 жылы 10 тамызда...").
> • Re-interrogation: asked again, the AIs gave 1845, 1845, 1847 and 1845. The story changes.
> • Fame: very well-known figure (high Wikipedia traffic), so the correct date is easy to confirm.
> **Correct version:** "Абай родился 10 августа 1845 года."
> **Check it yourself:** search "Абай туған жылы" on e-history.kz.

*(Illustrative example only. In the demo, use real errors collected during the hackathon.)*

### 3.3 The five sensors (how each one works)

#### Sensor 1: ALIBI CHECK (evidence + Quote-Lock)
- Each claim becomes 1–2 search queries in the claim's language **and** in Russian/English (Kazakh sources are scarce).
- A **source registry** ranks sources by trust tier:
  - Tier 1: adilet.zan.kz (laws), stat.gov.kz, egov.kz, official ministry sites, Crossref/PubMed, textbooks.
  - Tier 2: Wikipedia (kk/ru/en), e-history.kz, major encyclopedias.
  - Tier 3: news. Tier 4: forums (never used alone).
- An LLM judge reads the fetched page and must return **SUPPORTS / CONTRADICTS / NOT ENOUGH** plus an **exact quote**.
- **Quote-Lock:** our code checks that the quote *literally exists* in the downloaded page text (after normalizing spaces and letter case). If it doesn't, the evidence is thrown away. **The checker cannot hallucinate evidence.** This is our answer to "who checks the checker?".

#### Sensor 2: RE-INTERROGATION (story consistency)
- Turns the claim back into a question ("In what year was Abai born?").
- Asks **3 different model families × 2 phrasings** (6 short answers, temperature 0.7).
- Groups answers by meaning (numbers/dates matched exactly, text via an equivalence check) → **consistency score** = share of answers in the largest group, and whether that group matches the original claim.
- The science: models *confabulate* (guess) when their answers scatter across meanings. This is a simplified form of **semantic entropy** (Farquhar et al., *Nature* 2024) and SelfCheckGPT.

#### Sensor 3: PHANTOM TWIN (the control question) ⭐ *core novelty*
- A polygraph compares reactions to relevant questions against **comparison questions**. SENIM does the same with an important upgrade: **we *know* the correct answer to the control question**, because the entity doesn't exist.
- From the claim's question, SENIM builds a twin by swapping the key entity for a plausible **invented** one. Example: "When did Kazakh physicist *Nurlan Zhaksybekov* win the State Prize?" Existence is verified as fake: zero Wikipedia/Wikidata hits and near-zero web results.
- It asks the same model the twin question twice:
  - The model says "I don't know this person" → it knows its limits on this kind of question, so its confident answer on the real question means something.
  - The model **invents details about the fake** → it *bluffs* on this type of question, so its confidence on the real claim is **discounted** and the user sees *"This AI also wrote a detailed biography of a person who doesn't exist. Its confidence here proves nothing."*
- Why this matters: it's the most intuitive, convincing explanation a normal user can get. You *see* the AI lie about something you know is fake.
- Research roots: non-existent-entity tests (HalluLens) and counterfactual probing. Using it **live, per user question, as an explanation** is, as far as I found, not done by any product.

#### Sensor 4: FAME METER (knowledge-tail risk)
- Links the claim's main entity to Wikidata, then sums 12-month **Wikipedia pageviews** across kk/ru/en (free Wikimedia API). It also records whether articles exist in each language.
- Buckets: 🌍 famous (>1M views) · 🏙 known (10k–1M) · 🏘 rare (<10k) · 🕳 almost unknown (no article).
- The science: LLM accuracy collapses on long-tail entities, and scaling doesn't fix it (Mallen et al. 2023).
- Explanation shown: *"Few people have ever written about this village's history, so the AI almost certainly didn't learn it. Treat specifics as guesses."*
- **Also works before asking** (see 3.5).

#### Sensor 5: CITATION AUTOPSY
- Finds every reference, link or DOI in the answer.
- **Exists?** DOI → Crossref API. URL → HTTP check (dead or never-existed). Book/paper → Crossref/OpenAlex title search with fuzzy matching.
- **Matches?** Checks that the authors, year and journal fit the real record (catches "real paper, wrong details").
- **Says it?** Fetches the abstract/page and runs Quote-Lock: does the source actually support the sentence it's attached to?
- Verdict per citation: 👻 fabricated · ⚠️ real but misquoted · ✅ real and supports.

### 3.4 Combining the sensors (the "Trust Score")
Each claim gets a probability that it's wrong, from a small **logistic regression** (transparent, and every weight can be explained):

```
P(wrong) = sigmoid( b
  + w1·contradicted_by_tier1_2      − w2·supported_by_independent_sources
  + w3·(1 − consistency)            + w4·phantom_bluff
  + w5·tail_risk(fame)              + w6·claim_type_risk
  + w7·citation_failure )
```
- `claim_type_risk`: precise numbers, dates, quotes, citations, laws and anything after the model's training cutoff are riskier than general statements.
- Weights are **fitted on our own labeled dataset (KazTruth-200, see §7)**, not guessed.
- **Explanation rule ("glass box"):** every sentence in the "why" text is generated from a template tied to a measured signal. The LLM may rephrase it for readability but may not add facts. Nothing in the explanation comes from nowhere.

### 3.5 Prevention layer: "Risk Forecast" before you even ask
In the browser extension, while you type a question into ChatGPT/Gemini, a small meter predicts how risky the question is:
> 🟠 *High hallucination risk: rare local topic + exact numbers. Tips: ask for sources; ask in Russian/English (AI is weaker in Kazakh); ask "if you're not sure, say so."*

Based on Fame Meter + question type + language (KazMMLU shows models do worse in Kazakh than Russian). Most tools only check *after*; SENIM also helps you **ask better**.

### 3.6 Trust Gym (learning mode, for schools)
- Students get real AI answers with real (collected) errors. They mark the sentences they suspect, then SENIM reveals the sensors.
- It tracks an **AI Literacy Score** with skills: spotting fake numbers, fake citations, the tail-topic trap, and the "confident tone" trap.
- **Teacher mode:** create a class, assign 10-minute drills, see which error types the class misses. Content aligned with the school informatics subject.
- Goal: people who don't *need* SENIM after a year. That's real impact, not dependence.

## 4. Novelty (10 pts)
| Element | Exists already? | SENIM's twist |
|---|---|---|
| Claim extraction + web check | Yes (Gemini, Aretify, Facticity) | Only one of five sensors |
| **Phantom Twin control question**, live, per question, shown to the user | Research only (HalluLens, counterfactual probing); no product found | Turns research into the most convincing explanation a user can see |
| **Quote-Lock** (checker must prove its evidence literally exists) | Not seen in consumer tools | Answers "who checks the checker" |
| **Fame Meter** as a user-facing risk signal | Research (PopQA) | First "how much could the AI know about this?" meter |
| **Risk Forecast before asking** | Not found | Prevention, not only detection |
| **Kazakh/Russian source registry** (adilet, stat.gov, e-history) | Not found | Local ground truth where AI is weakest |
| **Glass-box explanations** built only from measured signals | Rare | The explanation can't hallucinate |
| Polygraph metaphor + Trust Gym | — | Makes it understandable and teachable |

Honest confidence that the *combination* is new: ~85%. That the Phantom Twin as a consumer feature is new: ~75%. I searched and found no product doing it, but I can't prove none exists.

## 5. User value, from every perspective (15 pts)
| Perspective | What they get |
|---|---|
| **Student** | Finds the one wrong sentence in 20 s, not "the whole thing is AI, rewrite it". Saves grades and prevents fake citations in papers. Works in Telegram, which they already use. |
| **Teacher** | Checks student work quickly, plus a ready AI-literacy curriculum (Trust Gym). |
| **Parent / everyday user** | Health/legal/money answers get a visible warning + the official source (adilet, egov). |
| **Journalist / lawyer** | Citation Autopsy catches fake quotes, laws and precedents. |
| **Engineer** | Async parallel pipeline, results streamed per claim (~10–20 s target for a 10-claim answer). A cheap "quick check" (Alibi + Fame) vs "deep interrogation". Caching of popular claims. Quote-Lock and glass-box design against the checker's own hallucinations. |
| **CEO / business** | Freemium: free 10 checks/day, Pro $3/month (unlimited, deep mode, PDF reports). **B2G:** Ministry of Education (AI literacy for 165k teachers already on ChatGPT Edu). **B2B:** universities (academic integrity), newsrooms, law firms, plus an API "trust layer" for companies deploying chatbots. Moat: the growing Kazakh claim-verdict dataset and source registry. |
| **Social** | Reduces misinformation in Kazakh, a language big tech underserves. Protects rural students who rely on AI most because they lack tutors. |
| **Global** | The same architecture plugs into any low-resource language (Uzbek, Kyrgyz, Tajik) by swapping in that country's source registry. The Phantom Twin works in any language. |
| **Ethics / privacy** | Texts aren't stored by default. Opt-in anonymous claim sharing only to improve the dataset. SENIM never says "100% true". It shows evidence and lets the human decide. |

## 6. Impact & scaling (15 pts)
**Roadmap**
1. **Hackathon MVP:** Telegram bot + web app, 5 sensors, KazTruth-200 evaluation.
2. **Month 1–3:** Chrome extension (ChatGPT/Gemini/Claude), Trust Gym pilot in 3 schools, public leaderboard of "which AI bluffs most on Kazakh topics".
3. **Month 3–12:** Partnership with the Ministry of Education / NIS / BIL schools, university integrity offices, and a public API.
4. **Year 2:** Other Central Asian languages, mobile share-sheet ("Share → SENIM" from any app), voice mode for AI voice assistants.

**Impact metrics:** errors caught per 100 answers; precision/recall on KazTruth; the share of Trust Gym students whose unaided error-spotting improves (pre/post test); time-to-verify vs manual Googling.

**Side effect for society:** the public "AI bluff leaderboard" pressures AI companies to improve Kazakh-language accuracy.

## 7. Data & technology (10 pts)
### 7.1 Architecture
```
Telegram bot / Chrome ext / Web app
            │  (text or screenshot → OCR kaz+rus)
            ▼
   FastAPI backend (async, Python)
            │
   1. Claim extractor (LLM, structured JSON: claim, type, entity, language)
            │
   ┌────────┼───────────┬────────────┬─────────────┐
   ▼        ▼           ▼            ▼             ▼
 Alibi   Re-interrog.  Phantom     Fame Meter   Citation
 search  3 models ×2   Twin probe  Wikidata +   Autopsy
 +Quote- (consistency) (bluff test) pageviews   Crossref/
 Lock                                           OpenAlex/HTTP
   └────────┴───────────┴────────────┴─────────────┘
            ▼
   Logistic-regression Trust Score → glass-box explanation templates
            ▼
   Streamed results per claim → UI (underlines + polygraph cards)
```

### 7.2 Stack
| Part | Tool | Why |
|---|---|---|
| Backend | Python + FastAPI + asyncio | Parallel sensors, easy AI libraries |
| Claim extraction, judge | Claude API (Claude Sonnet 5 for extraction/judging, Claude Haiku 4.5 for bulk sensor calls) | Strong multilingual structured output, cheap bulk calls |
| Model diversity for Re-interrogation | + 2 other model families via their APIs / OpenRouter | Different "witnesses" don't share the same mistakes |
| Search | Tavily or Brave Search API + direct site search on adilet/stat.gov | Returns page text quickly |
| Fame | Wikidata API + Wikimedia Pageviews REST API | Free and official |
| Citations | Crossref REST API, OpenAlex API | Free scholarly databases |
| OCR | Tesseract (kaz+rus+eng) or Google Cloud Vision | Screenshots from phones |
| Bot | aiogram (Telegram) | The biggest messaging channel for the audience |
| Extension | Chrome Manifest V3 content script | Adds a button under AI answers |
| Web | Next.js + Tailwind | Polygraph cards UI |
| DB | Supabase (Postgres) | Cache, Trust Gym progress, dataset |
| Model | scikit-learn logistic regression | Transparent weights, easy to explain to judges |

### 7.3 Proving accuracy: the KazTruth-200 benchmark
The case says "special attention to **accuracy**". Most teams will *claim* accuracy; SENIM **measures** it.
1. Generate ~60 AI answers on Kazakh history, geography, law, science and UNT topics (kk/ru/en).
2. Split them into ~200 claims. The team labels each as true/false/unverifiable using official sources (4 people ≈ 3 hours).
3. Run (a) the baseline "ask one LLM whether this is true" vs (b) SENIM's alibi-only mode vs (c) all 5 sensors.
4. Report **precision, recall and F1 for catching false claims** plus a chart. *(The numbers must be real and measured; don't invent them.)*
5. Publish the dataset open-source on GitHub/Hugging Face.

### 7.4 Cost & speed (estimates to verify)
A 10-claim deep check ≈ 1 extraction call + per claim (1 search + 1 judge + 6 short re-asks + 2 phantom calls) ≈ 100 short calls, mostly on a cheap model, costing on the order of a few cents. Quick mode (Alibi + Fame) costs about 10× less. Cache frequent claims.

### 7.5 Known limits (say them before judges do)
- Sources can be wrong or disagree. SENIM then shows "⚖️ sources disagree" and both quotes instead of choosing.
- Kazakh-language sources are scarce. SENIM says "unverifiable" rather than pretending.
- The Phantom Twin is strongest when we can query the same model that wrote the answer. For pasted answers from unknown models it becomes a "how much do AIs bluff on this *kind* of question" signal.
- Opinions, predictions and advice aren't fact-checkable. They're labeled ⚪, not judged.

## 8. Presentation & demo (10 pts): 2-minute video
1. **0:00** Hook: a student's essay with an AI answer that is 90% perfect, plus one fake date and one fake citation. *"Can you find them? Neither could the teacher."*
2. **0:15** Forward it to @SenimBot → underlines appear sentence by sentence.
3. **0:35** Tap the ❌ claim → the polygraph card: alibi quote, re-interrogation scatter, corrected fact.
4. **0:55** **The wow moment:** the Phantom Twin card. *"We asked the same AI about 'Nurlan Zhaksybekov', a physicist who doesn't exist. It wrote a full biography."* Show it side by side.
5. **1:15** Citation Autopsy: 👻 "this article does not exist" (Crossref).
6. **1:30** Risk Forecast while typing a question in Kazakh.
7. **1:40** KazTruth-200 results chart: SENIM vs a single-LLM check.
8. **1:50** Trust Gym + scale (165k teachers). Close: *"Don't trust the AI. Don't trust us either. Check the evidence. We show it."*

**Live on stage:** let a judge type any question into ChatGPT, forward the answer to the bot, and interrogate it live.

## 9. Case fit (5 pts)
✔ Helps tell reliable from invented facts ✔ **Explains why**, not only "error" ✔ Accuracy measured with a benchmark ✔ Understandable results (traffic lights + polygraph cards + plain language) ✔ Digital product + working MVP ✔ Female captain required ✔ Uses existing AI APIs, with a clear self-built contribution: sensors, Quote-Lock, scoring, dataset.

---

## 10. 48-hour MVP build plan (team of 4)
| Hours | Backend / AI | Sensors / data | Frontend / bot | Captain (research + pitch) |
|---|---|---|---|---|
| 0–4 | FastAPI skeleton, claim extractor | Source registry list (kk/ru sites) | Telegram bot echo | Collect 30 real AI errors on KZ topics |
| 4–14 | Alibi search + Quote-Lock | Fame Meter (Wikidata + pageviews) | Bot: send text → claims list | Build KazTruth questions |
| 14–24 | Re-interrogation (3 models) | Citation Autopsy (Crossref/HTTP) | Web polygraph cards UI | Label claims with the team |
| 24–32 | Phantom Twin generator + non-existence check | Logistic regression fitted on labels | Screenshot OCR in bot | Deck structure |
| 32–40 | Streaming, caching, glass-box explanations | Run benchmark, make chart | Trust Gym mini (5 drills) | Video script |
| 40–48 | Bug fixing, speed | Final numbers | Polish, deploy (Render/Vercel) | Record video, rehearse |

*If time is short, cut in this order:* Trust Gym → Risk Forecast → extension. **Never cut:** Phantom Twin, Quote-Lock, the benchmark.

## 11. Learning roadmap (in order)
1. **Python fundamentals + async** (asyncio, httpx): concurrency for parallel sensors.
2. **FastAPI**: build and deploy a small API.
3. **LLM APIs**: the Claude API (Messages, structured JSON output, tool use), prompt design, temperature/sampling.
4. **Hallucination science**: read the abstracts and figures of SelfCheckGPT, semantic entropy (*Nature* 2024), FActScore, SAFE (Long-form factuality), HalluLens, PopQA (Mallen 2023), KazMMLU.
5. **Information retrieval**: search APIs, HTML-to-text extraction (trafilatura), text normalization for Quote-Lock.
6. **Natural language inference** (supports/contradicts/neutral): the idea behind the judge.
7. **Wikidata & Wikimedia APIs** (entity linking, pageviews).
8. **Crossref / OpenAlex APIs** (DOI lookup, fuzzy title matching with rapidfuzz).
9. **Basic ML evaluation**: labeling, train/test split, logistic regression, precision/recall/F1, calibration (scikit-learn).
10. **Telegram bots** (aiogram) + **OCR** (Tesseract for Kazakh/Russian).
11. **Frontend**: Next.js + Tailwind basics; Chrome extension Manifest V3.
12. **Supabase** (Postgres, auth).
13. **Media literacy**: lateral reading (Stanford History Education Group, "Civic Online Reasoning"). This is the basis of Trust Gym.
14. **Pitching**: problem → live demo → numbers → impact.

## 12. Sources & inspiration
- **Polygraph Comparison Question Technique**, the core metaphor for Phantom Twin: https://sgp.fas.org/othergov/polygraph/ota/varieties.html · https://www.nationalacademies.org/read/10420/chapter/12
- Semantic entropy (*Nature* 2024), for Re-interrogation: https://www.nature.com/articles/s41586-024-07421-0
- PopQA, "When Not to Trust Language Models" (Mallen et al., ACL 2023), for the Fame Meter: https://aclanthology.org/2023.acl-long.546/
- HalluLens, non-existent entity tests, for Phantom Twin: https://arxiv.org/abs/2504.17550
- Fabricated citations (Walters & Wilder 2023), for Citation Autopsy: https://www.nature.com/articles/s41598-023-41032-5
- KazMMLU, Kazakh vs Russian performance gap: https://aclanthology.org/2025.acl-long.701/
- Hallucination detection paper list: https://github.com/EdinburghNLP/awesome-hallucination-detection
- Gemini Double-check (what we go beyond): https://support.google.com/gemini/answer/14143489
- Existing fact-check extensions (the competition): https://chromewebstore.google.com/detail/facticity-ai-fact-checker/mlackneplpmmomaobipjjpebhgcgmocp · https://factsentinel.com/ai-fact-checker-browser-extension
- Kazakhstan AI usage (KazISS): https://kisi.kz/en/kazakhstanis-most-often-turn-to-digital-tools-for-study-and-self-development-kaziss-survey/
- ChatGPT Edu for 165k Kazakh educators: https://www.edtechinnovationhub.com/news/openai-partners-with-government-of-kazakhstan-giving-165000-educators-access-to-chatgpt-edu
- Kazakhstan leads Central Asia in ChatGPT use: https://qazinform.com/news/kazakhstan-tops-central-asia-in-chatgpt-use-openai-says-0afd63
