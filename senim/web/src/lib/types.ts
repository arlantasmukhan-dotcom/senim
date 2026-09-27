// Mirrors senim/senim/models.py. Keep in sync when the backend schema changes.

export type Lang = "ru" | "kk" | "en";
export type Mode = "quick" | "deep";

export type VerdictLabel = "confirmed" | "unconfirmed" | "suspicious" | "contradicted" | "not_checkable";
export type Label = VerdictLabel | "pending";
export type SensorStatus = "ok" | "off" | "skipped" | "error";
export type SensorName = "alibi" | "reinterrogation" | "phantom" | "fame";

export interface Claim {
  id: string;
  text: string;
  span: string | null;
  start: number | null;
  end: number | null;
  type: string;
  checkable: boolean;
  lang: string;
  entity: string | null;
  question: string | null;
}

export interface Citation {
  id: string;
  raw: string;
  doi: string | null;
  url: string | null;
  title: string | null;
  claim_ids: string[];
}

export interface Evidence {
  url: string;
  domain: string;
  title: string;
  tier: number;
  stance: "supports" | "contradicts" | "irrelevant";
  quote: string;
  locked: boolean;
  snippet_only: boolean;
}

export interface AlibiResult {
  status: SensorStatus;
  backend: string;
  evidence: Evidence[];
  rejected_quotes: number;
  weak_quotes: number;
  support_domains: string[];
  contradict_domains: string[];
  contradict_tier12: boolean;
  contradict_other: boolean;
  suggested_correction: string | null;
  note: string;
}

export interface WitnessAnswer {
  model: string;
  phrasing: number;
  answer: string;
  relation: "agree" | "contradict" | "unsure";
}

export interface ReinterrogationResult {
  status: SensorStatus;
  answers: WitnessAnswer[];
  agree_share: number;
  contradict_share: number;
  unsure_share: number;
  note: string;
}

export interface PhantomResult {
  status: SensorStatus;
  fake_entity: string;
  twin_question: string;
  nonexistence_verified: boolean;
  verified_by: string;
  target_model: string;
  answers: { answer: string; fabricated: boolean }[];
  bluff: number;
  note: string;
}

export interface FameResult {
  status: SensorStatus;
  qid: string | null;
  label: string | null;
  description: string | null;
  views: Record<string, number>;
  total_views: number;
  bucket: "famous" | "known" | "rare" | "unknown";
  tail_risk: number;
  note: string;
}

export type CitationVerdict =
  | "fabricated"
  | "frankenstein"
  | "not_supporting"
  | "unverifiable_text"
  | "supports"
  | "dead_link"
  | "never_existed"
  | "unchecked";

export interface CitationResult {
  citation_id: string;
  raw: string;
  verdict: CitationVerdict;
  exists: boolean | null;
  found_title: string | null;
  found_year: number | null;
  mismatches: string[];
  lookup: string;
  claim_ids: string[];
  reason: string;
}

export interface Verdict {
  claim_id: string;
  label: VerdictLabel;
  p_wrong: number | null;
  reasons: string[];
  source_quote: string | null;
  source_url: string | null;
  suggested_correction: string | null;
  tip: string;
}

export interface SensorMap {
  alibi?: AlibiResult;
  reinterrogation?: ReinterrogationResult;
  phantom?: PhantomResult;
  fame?: FameResult;
}

export interface DoneInfo {
  elapsed_s: number;
  llm_calls: number;
  tokens: number;
  cost_usd: number;
  weights: string;
}

export interface Health {
  llm: boolean;
  search: string;
  author_models: { id: string; label: string }[];
  max_input_chars: number;
}
