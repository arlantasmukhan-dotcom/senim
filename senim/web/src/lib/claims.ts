import { fmt, formatInt, plural, tidy, type Dict, type Tone } from "./i18n";
import type {
  AlibiResult,
  CitationResult,
  Claim,
  Evidence,
  FameResult,
  Label,
  Lang,
  PhantomResult,
  ReinterrogationResult,
  SensorMap,
  Verdict,
  WitnessAnswer,
} from "./types";
import type { CheckState } from "./useCheck";

/** Worst first: this order decides legend order and which label wins on overlapping claims. */
export const ORDER: Label[] = ["contradicted", "suspicious", "unconfirmed", "confirmed", "not_checkable", "pending"];

export function labelOf(verdicts: Record<string, Verdict>, id: string): Label {
  return verdicts[id]?.label ?? "pending";
}

export function worst(labels: Label[]): Label {
  return [...labels].sort((a, b) => ORDER.indexOf(a) - ORDER.indexOf(b))[0] ?? "pending";
}

export interface Segment {
  text: string;
  claimIds: string[];
}

/** Splits the answer at claim boundaries. Backend offsets count code points (Python), JS counts UTF-16 units. */
export function segments(text: string, claims: Claim[]): Segment[] {
  const cps = Array.from(text);
  const unitAt: number[] = [0];
  for (const ch of cps) unitAt.push(unitAt[unitAt.length - 1] + ch.length);
  const located = claims.filter((c) => isLocatedIn(c, cps.length));
  const cuts = new Set<number>([0, cps.length]);
  for (const c of located) {
    cuts.add(c.start!);
    cuts.add(c.end!);
  }
  const points = [...cuts].sort((a, b) => a - b);
  const out: Segment[] = [];
  for (let i = 0; i < points.length - 1; i++) {
    const [a, b] = [points[i], points[i + 1]];
    out.push({
      text: text.slice(unitAt[a], unitAt[b]),
      claimIds: located.filter((c) => c.start! <= a && c.end! >= b).map((c) => c.id),
    });
  }
  return out;
}

function isLocatedIn(c: Claim, length: number): boolean {
  return c.start != null && c.end != null && c.end > c.start && c.end <= length;
}

export function isLocated(c: Claim, text: string): boolean {
  return isLocatedIn(c, Array.from(text).length);
}

export type SensorKey = "alibi" | "reinterrogation" | "phantom" | "fame" | "citations";
export const SENSOR_KEYS: SensorKey[] = ["alibi", "reinterrogation", "phantom", "fame", "citations"];

export interface SensorRow<T = unknown> {
  key: SensorKey;
  tone: Tone;
  /** Full sentence for the desktop card and the expanded phone sheet. */
  line: string;
  /** Shorter sentence for the compact phone sheet (mockup "MobileCard"). */
  short: string;
  data?: T;
}

/** Tone to text color. Only verdict-bearing tones get a color; everything else stays faint. */
export const TONE_CLASS: Record<Tone, string> = {
  against: "text-bad",
  for: "text-ok",
  mixed: "text-sus",
  risk: "text-sus",
  neutral: "text-faint",
  pending: "text-faint",
  off: "text-faint",
  skipped: "text-faint",
  quick: "text-faint",
  error: "text-faint",
};

/** Rows that carry no information for this claim; the compact phone sheet hides them. */
export function isQuietTone(t: Tone): boolean {
  return t === "skipped" || t === "quick" || t === "off";
}

export function lockedEvidence(a: AlibiResult): Evidence[] {
  const rank = { contradicts: 0, supports: 1, irrelevant: 2 };
  return a.evidence
    .filter((e) => e.locked && e.stance !== "irrelevant")
    .sort((x, y) => rank[x.stance] - rank[y.stance] || x.tier - y.tier);
}

/** Tier 1 (official) reads as reliability 4 of 4, tier 4 (unknown site) as 1 of 4. */
export function reliability(tier: number): number {
  return Math.min(4, Math.max(1, 5 - tier));
}

function row<T>(key: SensorKey, tone: Tone, line = "", short = line, data?: T): SensorRow<T> {
  return { key, tone, line, short, data };
}

function alibiRow(a: AlibiResult | undefined, running: boolean, t: Dict): SensorRow<AlibiResult> {
  if (!a) return row("alibi", running ? "pending" : "skipped");
  if (a.status !== "ok") return row("alibi", a.status === "error" ? "error" : a.status, t.alibi.off, t.alibi.off, a);
  const top = lockedEvidence(a)[0];
  const quoted = top ? fmt(t.alibi.short, { domain: top.domain, quote: top.quote }) : "";
  const contra = a.contradict_domains.length > 0;
  const support = a.support_domains.length > 0;
  if (contra && support) return row("alibi", "mixed", t.alibi.mixed, t.alibi.mixed, a);
  if (contra) return row("alibi", "against", a.contradict_tier12 ? t.alibi.contraT12 : t.alibi.contra, quoted, a);
  if (support) {
    const line = fmt(t.alibi.support, { domains: a.support_domains.slice(0, 3).join(", ") });
    return row("alibi", "for", line, quoted || line, a);
  }
  const line = a.evidence.length ? t.alibi.none : t.alibi.nosources;
  return row("alibi", "neutral", line, line, a);
}

function reiRow(r: ReinterrogationResult | undefined, s: CheckState, t: Dict, lang: Lang): SensorRow<ReinterrogationResult> {
  if (!r) {
    if (s.request?.mode === "quick") return row("reinterrogation", "quick");
    return row("reinterrogation", s.running ? "pending" : "skipped");
  }
  if (r.status !== "ok" || !r.answers.length)
    return row("reinterrogation", r.status === "error" ? "error" : "skipped", t.rei.none, t.rei.none, r);
  const n = r.answers.length;
  const agree = r.answers.filter((a) => a.relation === "agree").length;
  const line = fmt(plural(lang, agree, t.rei.line), { agree, n });
  const tone: Tone = r.agree_share >= 0.67 ? "for" : r.contradict_share >= 0.34 ? "against" : "neutral";
  return row("reinterrogation", tone, line, line, r);
}

function phantomRow(p: PhantomResult | undefined, s: CheckState, t: Dict): SensorRow<PhantomResult> {
  if (!p) {
    if (s.request?.mode === "quick") return row("phantom", "quick", t.phantom.quick);
    return row("phantom", s.running ? "pending" : "skipped");
  }
  if (p.status !== "ok" || !p.answers.length)
    return row("phantom", p.status === "error" ? "error" : "skipped", t.phantom.off, t.phantom.off, p);
  const n = p.answers.length;
  const k = p.answers.filter((a) => a.fabricated).length;
  if (p.bluff >= 0.5) return row("phantom", "against", t.phantom.bluff, t.phantom.bluffShort, p);
  if (k > 0) {
    const line = fmt(t.phantom.partial, { k, n });
    return row("phantom", "risk", line, line, p);
  }
  return row("phantom", "for", t.phantom.honest, t.phantom.honest, p);
}

function fameRow(f: FameResult | undefined, running: boolean, t: Dict, lang: Lang): SensorRow<FameResult> {
  if (!f) return row("fame", running ? "pending" : "skipped");
  if (f.status !== "ok") return row("fame", f.status === "error" ? "error" : f.status, t.fame.off, t.fame.off, f);
  const views = formatInt(lang, f.total_views);
  const tone: Tone = f.bucket === "rare" || f.bucket === "unknown" ? "risk" : "neutral";
  return row("fame", tone, fmt(t.fame[f.bucket], { views }), t.fame.short[f.bucket], f);
}

const CIT_TONE: Record<string, Tone> = {
  fabricated: "against",
  never_existed: "against",
  frankenstein: "against",
  not_supporting: "risk",
  supports: "for",
};
const CIT_RANK = ["fabricated", "never_existed", "frankenstein", "not_supporting", "dead_link", "unverifiable_text", "unchecked", "supports"];

function citationsRow(claimId: string, cits: CitationResult[] | null, running: boolean, t: Dict): SensorRow<CitationResult[]> {
  if (!cits) return row("citations", running ? "pending" : "skipped");
  const mine = cits.filter((c) => c.claim_ids.includes(claimId));
  if (!mine.length) return row("citations", "skipped", t.cit.none);
  mine.sort((a, b) => CIT_RANK.indexOf(a.verdict) - CIT_RANK.indexOf(b.verdict));
  const top = mine[0];
  const line = top.reason ? tidy(top.reason) : t.cit.labels[top.verdict];
  return row("citations", CIT_TONE[top.verdict] ?? "neutral", line, line, mine);
}

export function sensorRows(claim: Claim, s: CheckState, t: Dict, lang: Lang) {
  const m: SensorMap = s.sensors[claim.id] ?? {};
  return {
    alibi: alibiRow(m.alibi, s.running, t),
    reinterrogation: reiRow(m.reinterrogation, s, t, lang),
    phantom: phantomRow(m.phantom, s, t),
    fame: fameRow(m.fame, s.running, t, lang),
    citations: citationsRow(claim.id, s.cits, s.running, t),
  };
}

export function citationTone(verdict: string): Tone {
  return CIT_TONE[verdict] ?? "neutral";
}

export function modelName(id: string): string {
  return id ? id.split("/").pop()! : "AI";
}

const VALUE_TYPES = new Set(["number", "date", "law", "citation"]);

/** What a witness actually said, reduced to the value at stake (mockup: 1845 / 1847 / не знает). */
export function witnessValue(a: WitnessAnswer, claimType: string, t: Dict): string {
  if (a.relation === "unsure") return t.rei.rel.unsure;
  const text = a.answer.trim();
  if (VALUE_TYPES.has(claimType)) {
    const m = text.match(/\d[\d\s.,]*\d|\d/);
    if (m) return m[0].trim();
  }
  if (text.length <= 16) return text.replace(/[.。]$/, "");
  return t.rei.rel[a.relation];
}

/** Plain-text report for teachers to paste into a chat or a document. */
export function buildReport(s: CheckState, t: Dict): string {
  const lines = [t.report.title, ""];
  s.claims.forEach((c, i) => {
    const v = s.verdicts[c.id];
    const label = t.labels[labelOf(s.verdicts, c.id)];
    const pct = v?.p_wrong != null ? `, ${t.report.pWrong} ${Math.round(v.p_wrong * 100)}%` : "";
    lines.push(`${i + 1}. [${label}${pct}] ${c.text}`);
    if (v?.suggested_correction) lines.push(`   ${t.report.correction}: ${v.suggested_correction}`);
    if (v?.source_url) lines.push(`   ${v.source_url}`);
  });
  return lines.join("\n");
}
