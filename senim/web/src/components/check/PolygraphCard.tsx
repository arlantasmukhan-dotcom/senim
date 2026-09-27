"use client";

import {
  CaretLeftIcon,
  CaretRightIcon,
  CheckCircleIcon,
  LockSimpleIcon,
  MagnifyingGlassIcon,
  WarningCircleIcon,
} from "@phosphor-icons/react";
import { AnimatePresence, m } from "motion/react";
import { Fragment } from "react";
import { CopyButton } from "@/components/CopyButton";
import { LABEL_META, SENSOR_ICON, ToneMark, VerdictTag } from "@/components/kit";
import { Button } from "@/components/ui/button";
import {
  SENSOR_KEYS,
  isQuietTone,
  labelOf,
  lockedEvidence,
  modelName,
  sensorRows,
  witnessValue,
  type SensorRow,
} from "@/lib/claims";
import { fmt, plural, tidy, type Dict } from "@/lib/i18n";
import { useLang } from "@/lib/lang";
import type { AlibiResult, CitationResult, Claim, Label, PhantomResult, ReinterrogationResult } from "@/lib/types";
import type { CheckState } from "@/lib/useCheck";
import { cn } from "@/lib/utils";

interface Props {
  state: CheckState;
  claim: Claim;
  onNav: (dir: -1 | 1) => void;
  /** Phone sheet: short sensor lines, no evidence blocks (mockup "MobileCard"). */
  compact?: boolean;
}

export function PolygraphCard({ state, claim, onNav, compact = false }: Props) {
  const { t, lang } = useLang();
  const v = state.verdicts[claim.id];
  const label = labelOf(state.verdicts, claim.id);
  const idx = state.claims.findIndex((c) => c.id === claim.id);
  const rows = sensorRows(claim, state, t, lang);
  const mode = state.request?.mode ?? "deep";
  const counter = fmt(t.card.counter, { i: idx + 1, n: state.claims.length });
  const keys = compact ? SENSOR_KEYS.filter((k) => !isQuietTone(rows[k].tone)) : SENSOR_KEYS;

  const prev = (
    <Button variant={compact ? "bare" : "icon"} size={compact ? "icon-touch" : "icon-sm"} aria-label={t.card.prev} disabled={idx <= 0} onClick={() => onNav(-1)}>
      <CaretLeftIcon aria-hidden size={compact ? 18 : 16} />
    </Button>
  );
  const next = (
    <Button
      variant={compact ? "bare" : "icon"}
      size={compact ? "icon-touch" : "icon-sm"}
      aria-label={t.card.next}
      disabled={idx >= state.claims.length - 1}
      onClick={() => onNav(1)}
    >
      <CaretRightIcon aria-hidden size={compact ? 18 : 16} />
    </Button>
  );

  return (
    <div className={cn("flex flex-col", compact ? "gap-4" : "gap-[22px]")}>
      {compact ? (
        <div className="flex items-center gap-1.5">
          <VerdictTag label={label} text={t.labels[label]} className="flex-1" />
          {prev}
          <span className="font-mono text-[13px] font-medium text-faint">{counter}</span>
          {next}
        </div>
      ) : (
        <div className="flex items-center gap-2.5">
          <VerdictTag label={label} text={t.labels[label]} className="flex-1" />
          <span className="font-mono text-[13px] font-medium text-faint">{counter}</span>
          {prev}
          {next}
        </div>
      )}

      <AnimatePresence mode="wait" initial={false}>
        <m.div
          key={claim.id}
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, transition: { duration: 0.12 } }}
          className={cn("flex flex-col", compact ? "gap-4" : "gap-[22px]")}
        >
          <h2 className={cn("font-semibold leading-[1.35]", compact ? "text-xl" : "text-[23px] tracking-[-0.01em]")}>{claim.text}</h2>

          {v?.p_wrong != null && (
            <div className={cn("flex items-baseline", compact ? "gap-2.5" : "gap-3")}>
              <span
                className={cn(
                  "font-mono font-medium leading-none tracking-[-0.03em] tabular-nums",
                  compact ? "text-[34px]" : "text-[44px]",
                  LABEL_META[label].cls,
                )}
              >
                {Math.round(v.p_wrong * 100)}%
              </span>
              {compact ? (
                <span className="text-[13.5px] text-ink-4">{t.card.pWrong}</span>
              ) : (
                <span className="text-sm leading-[1.4] text-ink-4">
                  {t.card.pWrong}
                  <br />
                  {t.card.pWrongBy[mode]}
                </span>
              )}
            </div>
          )}

          {v?.suggested_correction &&
            (compact ? (
              <div className="flex flex-col gap-1 rounded-well bg-fix px-4 py-3.5">
                <span className="text-[12.5px] text-brand-soft-ink">{t.card.correction}</span>
                <span className="text-base font-semibold leading-[1.4]">{v.suggested_correction}</span>
              </div>
            ) : (
              <div className="flex items-center gap-4 rounded-well bg-fix px-[18px] py-4">
                <div className="flex flex-1 flex-col gap-1">
                  <span className="text-[13px] text-brand-soft-ink">{t.card.correction}</span>
                  <span className="text-[17px] font-semibold leading-[1.4]">{v.suggested_correction}</span>
                  <span className="text-[12.5px] text-brand-soft-ink/85">{t.card.correctionNote}</span>
                </div>
                <CopyButton text={v.suggested_correction} label={t.card.copy} className="border-fix-line" />
              </div>
            ))}

          {!claim.checkable ? (
            <p className="border-t border-line pt-5 text-[15px] leading-[1.55] text-ink-3">{t.card.opinion}</p>
          ) : (
            <div className="flex flex-col border-b border-line">
              {keys.map((k) => (
                <SensorBlock key={k} row={rows[k]} t={t} compact={compact} claim={claim} label={label} />
              ))}
            </div>
          )}

          {!compact && v?.tip && (
            <div className="grid grid-cols-[24px_minmax(0,1fr)] gap-x-3 gap-y-1">
              <MagnifyingGlassIcon aria-hidden size={20} className="row-span-2 mt-px text-brand" />
              <span className="text-[15.5px] font-semibold">{t.card.tip}</span>
              <span className="text-[14.5px] leading-[1.5] text-ink-2">{tidy(v.tip)}</span>
            </div>
          )}
        </m.div>
      </AnimatePresence>
    </div>
  );
}

function SensorBlock({ row, t, compact, claim, label }: { row: SensorRow; t: Dict; compact: boolean; claim: Claim; label: Label }) {
  const Icon = SENSOR_ICON[row.key];
  const pending = row.tone === "pending";
  const text = compact ? row.short : row.line;
  const quiet = isQuietTone(row.tone) || row.tone === "error";
  return (
    <div
      className={cn(
        "grid grid-cols-[24px_minmax(0,1fr)_auto] items-start border-t border-line transition-opacity duration-300",
        compact ? "gap-x-2.5 gap-y-0.5 py-3" : "gap-x-3 gap-y-1 py-[18px]",
        quiet && "opacity-60",
      )}
    >
      <span className="row-span-3 pt-px">
        <Icon aria-hidden size={compact ? 18 : 20} className="text-ink-3" />
      </span>
      <span className={cn("font-semibold", compact ? "text-[14.5px]" : "text-[15.5px]")}>{t.sensorNames[row.key]}</span>
      <ToneMark tone={row.tone} label={t.tone[row.tone]} size={compact ? 18 : 20} />
      <div className="col-span-2">
        {pending ? (
          <div className="mt-1 h-3.5 w-2/3 rounded-md bg-line-soft motion-safe:animate-pulse" />
        ) : (
          text && (
            <m.p
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className={cn("leading-[1.5]", compact ? "text-[13.5px] leading-[1.45] text-ink-3" : "text-[14.5px] text-ink-2")}
            >
              {text}
            </m.p>
          )
        )}
        {!compact && !pending && row.data != null && <Details row={row} t={t} claim={claim} label={label} />}
      </div>
    </div>
  );
}

function Details({ row, t, claim, label }: { row: SensorRow; t: Dict; claim: Claim; label: Label }) {
  switch (row.key) {
    case "alibi":
      return <AlibiDetails a={row.data as AlibiResult} t={t} />;
    case "reinterrogation":
      return <WitnessTable r={row.data as ReinterrogationResult} t={t} claim={claim} label={label} />;
    case "phantom":
      return <PhantomBox p={row.data as PhantomResult} t={t} />;
    case "citations":
      return <CitationDetails list={row.data as CitationResult[]} t={t} />;
    default:
      return null;
  }
}

function AlibiDetails({ a, t }: { a: AlibiResult; t: Dict }) {
  const { lang } = useLang();
  if (a.status !== "ok") return null;
  const ev = lockedEvidence(a).slice(0, 3);
  if (!ev.length && !a.rejected_quotes && !a.weak_quotes) return null;
  return (
    <div className="mt-2 flex flex-col gap-2">
      {ev.map((e, i) => (
        <a
          key={i}
          href={e.url}
          target="_blank"
          rel="noopener noreferrer"
          className="group flex items-start gap-2.5 rounded-well bg-well px-3.5 py-3 transition-colors duration-150 hover:bg-line-soft"
        >
          <LockSimpleIcon aria-hidden size={16} className="mt-0.5 shrink-0 text-brand" />
          <span className="flex min-w-0 flex-col gap-1">
            <span className="text-[15px] leading-[1.45] text-ink">«{e.quote}»</span>
            <span className="break-words font-mono text-[12.5px] text-ink-4 group-hover:text-brand">
              {e.domain}, {t.alibi.tier[e.tier] ?? t.alibi.tier[4]}, {e.snippet_only ? t.alibi.snippet : t.alibi.locked}
            </span>
          </span>
        </a>
      ))}
      {a.rejected_quotes > 0 && (
        <span className="text-[13px] leading-[1.45] text-faint">{fmt(plural(lang, a.rejected_quotes, t.alibi.rejected), { n: a.rejected_quotes })}</span>
      )}
      {a.weak_quotes > 0 && <span className="text-[13px] leading-[1.45] text-faint">{fmt(t.alibi.weak, { n: a.weak_quotes })}</span>}
    </div>
  );
}

/** Mockup: model × phrasing grid with the value each witness gave; agreement with a refuted claim is marked. */
function WitnessTable({ r, t, claim, label }: { r: ReinterrogationResult; t: Dict; claim: Claim; label: Label }) {
  if (!r.answers.length) return null;
  const models = [...new Set(r.answers.map((a) => a.model))];
  const phrasings = [...new Set(r.answers.map((a) => a.phrasing))].sort();
  const agreeCls = label === "contradicted" ? "font-semibold text-bad" : label === "suspicious" ? "font-semibold text-sus" : "font-semibold";
  return (
    <div
      className="mt-2 grid gap-y-1.5 font-mono text-[13.5px] tabular-nums"
      style={{ gridTemplateColumns: `minmax(0,1fr) repeat(${phrasings.length}, 80px)` }}
    >
      <span className="font-sans text-[12.5px] text-faint">{t.rei.model}</span>
      {phrasings.map((p) => (
        <span key={p} className="font-sans text-[12.5px] text-faint">
          {fmt(t.rei.q, { i: p })}
        </span>
      ))}
      {models.map((model) => (
        <Fragment key={model}>
          <span className="truncate pr-2">{modelName(model)}</span>
          {phrasings.map((p) => {
            const a = r.answers.find((x) => x.model === model && x.phrasing === p);
            if (!a) return <span key={p} className="text-faint">-</span>;
            return (
              <span
                key={p}
                title={a.answer}
                className={cn("truncate", a.relation === "agree" ? agreeCls : a.relation === "unsure" ? "text-faint" : "")}
              >
                {witnessValue(a, claim.type, t)}
              </span>
            );
          })}
        </Fragment>
      ))}
    </div>
  );
}

function PhantomBox({ p, t }: { p: PhantomResult; t: Dict }) {
  const { lang } = useLang();
  if (p.status !== "ok" || !p.answers.length) return null;
  const k = p.answers.filter((a) => a.fabricated).length;
  const shown = p.answers.find((a) => a.fabricated) ?? p.answers[0];
  const verified = !p.nonexistence_verified ? t.phantom.unverified : p.verified_by === "web" ? t.phantom.web : t.phantom.wiki;
  return (
    <div className="mt-2 flex flex-col gap-2 rounded-well border border-sus-line px-3.5 py-3">
      <span className="text-[13px] text-faint">{fmt(t.phantom.box, { model: modelName(p.target_model) })}</span>
      <span className="text-[14.5px] font-medium">{p.twin_question}</span>
      <span className="line-clamp-3 text-[14.5px] leading-[1.5] text-ink-2">«{shown.answer}»</span>
      <span className={cn("flex items-start gap-1.5 text-[13px] font-semibold", k ? "text-sus" : "text-ok")}>
        {k ? <WarningCircleIcon aria-hidden size={16} className="mt-px shrink-0" /> : <CheckCircleIcon aria-hidden size={16} className="mt-px shrink-0" />}
        {verified} {fmt(plural(lang, k, t.phantom.count), { k, n: p.answers.length })}
      </span>
    </div>
  );
}

function CitationDetails({ list, t }: { list: CitationResult[]; t: Dict }) {
  if (list.length < 2 && !list[0]?.found_title) return null;
  return (
    <ul className="mt-2 flex flex-col gap-2">
      {list.map((c) => (
        <li key={c.citation_id} className="flex flex-col gap-0.5 text-[13.5px]">
          <span className="break-words font-mono">{c.raw}</span>
          <span className="text-ink-3">
            {t.cit.labels[c.verdict]}
            {c.found_title ? `: ${c.found_title}${c.found_year ? ` (${c.found_year})` : ""}` : ""}
          </span>
        </li>
      ))}
    </ul>
  );
}
