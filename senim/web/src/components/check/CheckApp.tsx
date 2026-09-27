"use client";

import {
  ArrowClockwiseIcon,
  ArrowRightIcon,
  CheckCircleIcon,
  ShareNetworkIcon,
  StopIcon,
} from "@phosphor-icons/react";
import { m } from "motion/react";
import { useCallback, useEffect, useMemo, useRef, useState, useSyncExternalStore } from "react";
import { useForm } from "react-hook-form";
import { Footer } from "@/components/Footer";
import { LABEL_META, Spinner, card, wrapApp } from "@/components/kit";
import { AppHeader } from "@/components/SiteHeader";
import { Button } from "@/components/ui/button";
import { Drawer, DrawerContent, DrawerDescription, DrawerTitle } from "@/components/ui/drawer";
import { ORDER, TONE_CLASS, buildReport, citationTone, isLocated, labelOf, segments } from "@/lib/claims";
import { fmt, plural, tidy } from "@/lib/i18n";
import { useLang } from "@/lib/lang";
import { PENDING_KEY } from "@/lib/pending";
import type { Health, Label } from "@/lib/types";
import { useCheck, type CheckState } from "@/lib/useCheck";
import { cn } from "@/lib/utils";
import { CheckForm, ErrorNote, UNKNOWN_AUTHOR, type CheckFormValues } from "./CheckForm";
import { PolygraphCard } from "./PolygraphCard";

type HealthState = Health | "down" | null;

function useHealth(): HealthState {
  const [h, setH] = useState<HealthState>(null);
  useEffect(() => {
    let alive = true;
    fetch("/api/health")
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then((j: Health) => alive && setH(j))
      .catch(() => alive && setH("down"));
    return () => {
      alive = false;
    };
  }, []);
  return h;
}

const desktopQuery = "(min-width: 1024px)";
function useIsDesktop(): boolean {
  return useSyncExternalStore(
    (cb) => {
      const q = window.matchMedia(desktopQuery);
      q.addEventListener("change", cb);
      return () => q.removeEventListener("change", cb);
    },
    () => window.matchMedia(desktopQuery).matches,
    () => true,
  );
}

export function CheckApp() {
  const { t, lang } = useLang();
  const health = useHealth();
  const { state, run, stop, reset } = useCheck();
  const form = useForm<CheckFormValues>({
    defaultValues: { text: "", question: "", author: UNKNOWN_AUTHOR, mode: "deep" },
  });
  const [selected, setSelected] = useState<string | null>(null);
  const [editing, setEditing] = useState(true);
  const [sheetOpen, setSheetOpen] = useState(false);
  const [sheetFull, setSheetFull] = useState(false);
  const isDesktop = useIsDesktop();

  const start = useCallback(
    (v: CheckFormValues) => {
      setSelected(null);
      setEditing(false);
      run({
        text: v.text.trim(),
        question: v.question.trim() || null,
        author_model: v.author === UNKNOWN_AUTHOR ? null : v.author,
        ui_lang: lang,
        mode: v.mode,
      });
    },
    [lang, run],
  );

  // Hand-off from the landing hero. Deferred one tick so a dev StrictMode remount doesn't abort it.
  const startRef = useRef(start);
  useEffect(() => {
    startRef.current = start;
  });
  useEffect(() => {
    let raw: string | null = null;
    try {
      raw = sessionStorage.getItem(PENDING_KEY);
    } catch {
      return;
    }
    if (!raw) return;
    const id = setTimeout(() => {
      sessionStorage.removeItem(PENDING_KEY);
      const { text } = JSON.parse(raw!) as { text: string };
      form.setValue("text", text);
      startRef.current({ ...form.getValues(), text });
    }, 0);
    return () => clearTimeout(id);
  }, [form]);

  const firstId = state.claims.find((c) => c.checkable)?.id ?? state.claims[0]?.id ?? null;
  const current = state.claims.find((c) => c.id === selected) ?? state.claims.find((c) => c.id === firstId) ?? null;

  const open = useCallback(
    (id: string) => {
      setSelected(id);
      if (!isDesktop) {
        setSheetFull(false);
        setSheetOpen(true);
      }
    },
    [isDesktop],
  );

  const nav = useCallback(
    (dir: -1 | 1) => {
      if (!current) return;
      const i = state.claims.findIndex((c) => c.id === current.id);
      const next = state.claims[i + dir];
      if (next) setSelected(next.id);
    },
    [current, state.claims],
  );

  const showResults = !editing && (state.claims.length > 0 || state.running);

  return (
    <>
      <AppHeader />
      <main id="main" className={cn(wrapApp, "flex flex-1 flex-col gap-7 pt-5 lg:pt-9", showResults ? "pb-32 lg:pb-0" : "pb-16")}>
        {showResults ? (
          <Results
            state={state}
            current={current}
            onOpen={open}
            onNav={nav}
            onStop={stop}
            onEdit={() => {
              stop();
              setEditing(true);
            }}
            health={health}
            isDesktop={isDesktop}
          />
        ) : (
          <CheckForm
            form={form}
            health={health}
            serverError={state.error}
            onRun={(v) => {
              if (state.error) reset();
              start(v);
            }}
          />
        )}
      </main>

      {showResults && !isDesktop && <MobileBar state={state} onOpen={open} />}

      {!isDesktop && current && (
        <Drawer open={sheetOpen} onOpenChange={setSheetOpen}>
          <DrawerContent>
            <DrawerTitle className="sr-only">{current.text}</DrawerTitle>
            <DrawerDescription className="sr-only">{t.labels[labelOf(state.verdicts, current.id)]}</DrawerDescription>
            <div className="flex min-h-0 flex-col overflow-y-auto overscroll-contain px-5 pb-6 pt-4">
              <PolygraphCard state={state} claim={current} onNav={nav} compact={!sheetFull} />
              <Button variant="strong" className="mt-5 h-12 w-full shrink-0" onClick={() => setSheetFull((f) => !f)}>
                {sheetFull ? t.check.less : t.check.details}
              </Button>
            </div>
          </DrawerContent>
        </Drawer>
      )}

      {state.claims.length > 0 && <PrintReport state={state} />}

      <div className="hidden min-h-[120px] flex-1 lg:block" />
      <div className="hidden lg:block">
        <Footer />
      </div>
    </>
  );
}

/* --------------------------------- results -------------------------------- */

interface ResultsProps {
  state: CheckState;
  current: CheckState["claims"][number] | null;
  onOpen: (id: string) => void;
  onNav: (dir: -1 | 1) => void;
  onStop: () => void;
  onEdit: () => void;
  health: HealthState;
  isDesktop: boolean;
}

function Results({ state, current, onOpen, onNav, onStop, onEdit, health, isDesktop }: ResultsProps) {
  const { t } = useLang();

  return (
    <div className="no-print flex flex-col gap-5 lg:gap-7">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div className="flex flex-col gap-2">
          <h1 className="sr-only text-[30px] font-bold tracking-[-0.02em] lg:not-sr-only">{t.check.title}</h1>
          <Summary state={state} health={health} />
        </div>
        {isDesktop && <Actions state={state} onStop={onStop} />}
      </div>

      {state.running && <Progress state={state} />}
      {state.error && <ErrorNote code={state.error.code} message={state.error.message} />}

      <div className="grid grid-cols-1 items-start gap-7 lg:grid-cols-[minmax(0,1fr)_minmax(420px,560px)]">
        <div className="flex flex-col gap-7">
          <section className={cn("flex flex-col gap-[18px] lg:gap-6", "lg:rounded-card lg:border lg:border-line lg:bg-surface lg:px-9 lg:py-8")}>
            {state.claims.length > 0 && <Legend state={state} onOpen={onOpen} />}
            <AnswerText state={state} selected={current?.id ?? null} onOpen={onOpen} />
            {!isDesktop && state.claims.length > 0 && <p className="text-[13.5px] text-faint">{t.check.selectHint}</p>}
            <Unlocated state={state} onOpen={onOpen} />
            <Citations state={state} />
            {!state.running && state.stage === "done" && state.claims.length === 0 && !state.error && (
              <p className="text-[15px] text-ink-3">{t.check.noClaims}</p>
            )}
          </section>

          <section className="flex flex-col gap-3 lg:px-1">
            <span className="text-[15px] font-semibold">{t.check.original}</span>
            <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:gap-4">
              <span className="min-w-0 flex-1 truncate text-[15px] text-ink-4">{state.request?.text}</span>
              <Button variant="link" size="text" className="gap-1.5 self-start" onClick={onEdit}>
                <ArrowClockwiseIcon aria-hidden size={16} /> {t.check.edit}
              </Button>
            </div>
            {state.done && (
              <span className="text-[13px] text-faint">
                {fmt(t.check.cost, { cost: state.done.cost_usd.toFixed(2) })}
              </span>
            )}
            {!isDesktop && (
              <div className="pt-2">
                <Actions state={state} onStop={onStop} />
              </div>
            )}
          </section>
        </div>

        {isDesktop && (
          <aside className={cn(card, "sticky top-6 px-[30px] py-7 shadow-aside")}>
            {current ? <PolygraphCard state={state} claim={current} onNav={onNav} /> : <CardSkeleton />}
          </aside>
        )}
      </div>
    </div>
  );
}

/** Mockup: "Поделиться" (outline) + "Сохранить отчёт" (primary). While running: stop. */
function Actions({ state, onStop }: { state: CheckState; onStop: () => void }) {
  const { t } = useLang();
  const [shared, setShared] = useState(false);
  if (state.running) {
    return (
      <Button variant="outline" onClick={onStop} className="self-start">
        <StopIcon aria-hidden size={18} /> {t.check.stop}
      </Button>
    );
  }
  if (!state.claims.length) return null;

  async function share() {
    const text = buildReport(state, t);
    try {
      if (navigator.share) {
        await navigator.share({ title: t.report.title, text });
        return;
      }
    } catch {
      /* the share sheet was dismissed or is unavailable: fall back to the clipboard */
    }
    await navigator.clipboard?.writeText(text);
    setShared(true);
    setTimeout(() => setShared(false), 1600);
  }

  return (
    <div className="flex flex-wrap gap-2.5">
      <Button variant="outline" onClick={share}>
        {shared ? <CheckCircleIcon aria-hidden size={18} className="text-ok" /> : <ShareNetworkIcon aria-hidden size={18} />}
        {shared ? t.check.copied : t.check.share}
      </Button>
      <Button onClick={() => window.print()}>{t.check.save}</Button>
    </div>
  );
}

function Summary({ state, health }: { state: CheckState; health: HealthState }) {
  const { t, lang } = useLang();
  if (state.running || !state.done) return null;
  const n = state.claims.length;
  const c = state.citations.length;
  const s = Math.round(state.done.elapsed_s);
  const authorId = state.request?.author_model;
  const author = authorId && health && health !== "down" ? health.author_models.find((x) => x.id === authorId)?.label : null;
  const mode = state.request?.mode === "quick" ? t.check.quick : t.check.deep;
  const parts = [
    `${n} ${plural(lang, n, t.check.claims)}`,
    c ? `${c} ${plural(lang, c, t.check.refs)}` : null,
    author ? fmt(t.check.answerBy, { model: author }) : null,
    mode.charAt(0).toLocaleLowerCase(lang) + mode.slice(1),
  ].filter(Boolean);
  return (
    <m.span initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex items-start gap-2 text-[15px] leading-[1.5] text-ink-3">
      <CheckCircleIcon aria-hidden size={18} className="mt-0.5 shrink-0 text-brand" />
      <span>
        {fmt(t.check.doneIn, { s, sec: plural(lang, s, t.check.sec) })} {parts.join(", ")}.
      </span>
    </m.span>
  );
}

/** Mockup "MobileResults": sensors running, N of M claims done, thin bar. */
function Progress({ state }: { state: CheckState }) {
  const { t } = useLang();
  const extracting = state.stage === "extract";
  const total = state.claims.length;
  const done = state.claims.filter((c) => state.verdicts[c.id]).length;
  const share = extracting || !total ? 0.06 : Math.max(0.04, done / total);
  return (
    <div className="flex flex-col gap-2.5" aria-live="polite">
      <div className="flex items-baseline justify-between gap-4">
        <span className="flex items-center gap-2 text-[15px] font-semibold">
          <Spinner size={16} className="text-brand" />
          {extracting ? t.check.extract : t.check.sensors}
        </span>
        {!extracting && total > 0 && (
          <span className="font-mono text-[13px] font-medium text-ink-4 tabular-nums">{fmt(t.check.progress, { done, total })}</span>
        )}
      </div>
      <div className="h-[3px] overflow-hidden rounded-full bg-line">
        <m.div
          className="h-full origin-left rounded-full bg-brand"
          initial={{ scaleX: 0 }}
          animate={{ scaleX: share }}
          transition={{ type: "spring", stiffness: 120, damping: 24 }}
        />
      </div>
    </div>
  );
}

function Legend({ state, onOpen }: { state: CheckState; onOpen: (id: string) => void }) {
  const { t, lang } = useLang();
  const groups = new Map<Label, string[]>();
  for (const c of state.claims) {
    const l = labelOf(state.verdicts, c.id);
    groups.set(l, [...(groups.get(l) ?? []), c.id]);
  }
  return (
    <div className="flex flex-wrap gap-x-6 gap-y-1.5 text-[13.5px] lg:gap-y-2 lg:text-sm">
      {ORDER.filter((l) => groups.has(l)).map((l) => (
        <button
          key={l}
          type="button"
          onClick={() => onOpen(groups.get(l)![0])}
          className={cn(
            "flex min-h-8 items-center gap-2 font-medium transition-colors duration-150 hover:text-brand",
            l === "not_checkable" || l === "pending" ? "text-faint" : "text-ink",
          )}
        >
          <span className={cn("swatch", `sw-${l}`)} />
          {groups.get(l)!.length} {plural(lang, groups.get(l)!.length, t.legend[l])}
        </button>
      ))}
      {state.truncated && <span className="flex min-h-8 items-center text-faint">{t.check.truncated}</span>}
    </div>
  );
}

function AnswerText({ state, selected, onOpen }: { state: CheckState; selected: string | null; onOpen: (id: string) => void }) {
  const { t } = useLang();
  const segs = useMemo(() => segments(state.text, state.claims), [state.text, state.claims]);
  const base = "whitespace-pre-wrap text-[17px] leading-[1.95] lg:text-xl lg:leading-[2.05]";
  if (!state.claims.length) {
    return <p className={cn(base, "text-pending-ink motion-safe:animate-pulse")}>{state.text}</p>;
  }
  return (
    <p className={base}>
      {segs.map((s, i) => {
        if (!s.claimIds.length) return <span key={i}>{s.text}</span>;
        const label = s.claimIds
          .map((id) => labelOf(state.verdicts, id))
          .sort((a, b) => ORDER.indexOf(a) - ORDER.indexOf(b))[0];
        const target = selected && s.claimIds.includes(selected) ? selected : s.claimIds[0];
        return (
          <span
            key={i}
            role="button"
            tabIndex={0}
            aria-pressed={s.claimIds.includes(selected ?? "")}
            onClick={() => onOpen(target)}
            onKeyDown={(e) => {
              if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                onOpen(target);
              }
            }}
            title={t.labels[label]}
            className={cn("claim", `v-${label}`)}
          >
            {s.text}
          </span>
        );
      })}
    </p>
  );
}

function Unlocated({ state, onOpen }: { state: CheckState; onOpen: (id: string) => void }) {
  const { t } = useLang();
  const lost = state.claims.filter((c) => !isLocated(c, state.text));
  if (!lost.length) return null;
  return (
    <div className="flex flex-col gap-2.5 border-t border-line pt-5">
      <span className="text-[15px] font-semibold">{t.check.unlocated}</span>
      {lost.map((c) => {
        const l = labelOf(state.verdicts, c.id);
        return (
          <button
            key={c.id}
            type="button"
            onClick={() => onOpen(c.id)}
            className="flex items-start gap-2.5 rounded-well px-2 py-1.5 text-left text-[15px] leading-[1.5] transition-colors duration-150 hover:bg-well"
          >
            <span className={cn("mt-0.5 shrink-0 font-semibold", LABEL_META[l].cls)}>{t.labels[l]}</span>
            <span>{c.text}</span>
          </button>
        );
      })}
    </div>
  );
}

function Citations({ state }: { state: CheckState }) {
  const { t } = useLang();
  if (!state.citations.length) return null;
  const results = new Map((state.cits ?? []).map((r) => [r.citation_id, r]));
  return (
    <div className="flex flex-col gap-3 border-t border-line pt-[22px]">
      <span className="text-[15px] font-semibold">{t.check.citations}</span>
      {state.citations.map((c) => {
        const r = results.get(c.id);
        const tone = r ? citationTone(r.verdict) : "pending";
        const Icon = r ? (tone === "for" ? CheckCircleIcon : LABEL_META[tone === "against" ? "contradicted" : "suspicious"].Icon) : null;
        return (
          <div key={c.id} className="grid grid-cols-[22px_minmax(0,1fr)] gap-x-3 gap-y-1">
            <span className={cn("row-span-2 pt-0.5", TONE_CLASS[tone])}>{Icon ? <Icon aria-hidden size={20} /> : <Spinner size={18} />}</span>
            <span className="break-words font-mono text-[14.5px] font-medium">{c.raw}</span>
            <span className="text-[14.5px] leading-[1.5] text-ink-3">
              {r ? (
                <>
                  <strong className={cn("font-semibold", TONE_CLASS[tone])}>{t.cit.labels[r.verdict]}.</strong> {r.reason ? tidy(r.reason) : ""}
                </>
              ) : (
                t.labels.pending
              )}
            </span>
          </div>
        );
      })}
    </div>
  );
}

function CardSkeleton() {
  return (
    <div className="flex flex-col gap-5" aria-hidden>
      <div className="h-5 w-40 rounded-md bg-line-soft motion-safe:animate-pulse" />
      <div className="h-7 w-full rounded-md bg-line-soft motion-safe:animate-pulse" />
      <div className="h-7 w-3/4 rounded-md bg-line-soft motion-safe:animate-pulse" />
      {[0, 1, 2, 3, 4].map((i) => (
        <div key={i} className="flex gap-3 border-t border-line pt-4">
          <div className="size-5 rounded-md bg-line-soft motion-safe:animate-pulse" />
          <div className="flex flex-1 flex-col gap-2">
            <div className="h-4 w-1/3 rounded-md bg-line-soft motion-safe:animate-pulse" />
            <div className="h-3.5 w-2/3 rounded-md bg-line-soft motion-safe:animate-pulse" />
          </div>
        </div>
      ))}
    </div>
  );
}

/* --------------------------------- mobile --------------------------------- */

/** Mockup "MobileResults": one full-width primary action pinned to the bottom. */
function MobileBar({ state, onOpen }: { state: CheckState; onOpen: (id: string) => void }) {
  const { t } = useLang();
  if (!state.claims.length) return null;
  const find = (l: Label) => state.claims.find((c) => labelOf(state.verdicts, c.id) === l);
  const target = find("contradicted") ?? find("suspicious") ?? state.claims.find((c) => c.checkable) ?? state.claims[0];
  const l = labelOf(state.verdicts, target.id);
  const text = l === "contradicted" || l === "suspicious" ? t.check.openCard[l] : t.check.openCard.other;
  return (
    <div className="no-print fixed inset-x-0 bottom-0 border-t border-line bg-surface px-4 pb-[max(1.5rem,env(safe-area-inset-bottom))] pt-3">
      <Button size="lg" className="w-full" onClick={() => onOpen(target.id)}>
        {text} <ArrowRightIcon aria-hidden size={18} />
      </Button>
    </div>
  );
}

/* ---------------------------------- print --------------------------------- */

/** "Сохранить отчёт" prints this: every claim with its verdict, correction and source. */
function PrintReport({ state }: { state: CheckState }) {
  const { t } = useLang();
  return (
    <section className="hidden px-10 py-8 print:block">
      <h1 className="mb-6 text-2xl font-bold">{t.report.title}</h1>
      <ol className="flex flex-col gap-5">
        {state.claims.map((c) => {
          const v = state.verdicts[c.id];
          const l = labelOf(state.verdicts, c.id);
          return (
            <li key={c.id} className="flex flex-col gap-1 border-b border-line pb-4">
              <span className={cn("text-sm font-semibold", LABEL_META[l].cls)}>
                {t.labels[l]}
                {v?.p_wrong != null ? `, ${t.report.pWrong} ${Math.round(v.p_wrong * 100)}%` : ""}
              </span>
              <span className="text-base">{c.text}</span>
              {v?.suggested_correction && (
                <span className="text-sm">
                  {t.report.correction}: {v.suggested_correction}
                </span>
              )}
              {v?.source_url && <span className="font-mono text-xs text-ink-4">{v.source_url}</span>}
            </li>
          );
        })}
      </ol>
    </section>
  );
}
