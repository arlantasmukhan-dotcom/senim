"use client";

import {
  ArrowCounterClockwiseIcon,
  ArrowRightIcon,
  ChalkboardTeacherIcon,
  CheckCircleIcon,
  GhostIcon,
  LockSimpleIcon,
  NewspaperIcon,
  StudentIcon,
  TelegramLogoIcon,
  UsersThreeIcon,
  WarningCircleIcon,
} from "@phosphor-icons/react";
import { m, useReducedMotion } from "motion/react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { useLang } from "@/lib/lang";
import { PENDING_KEY } from "@/lib/pending";
import { cn } from "@/lib/utils";
import { CopyButton } from "./CopyButton";
import { Footer, REPO, TELEGRAM_URL } from "./Footer";
import { SENSOR_ICON, ToneMark, VerdictTag, card, h2, lead, section, wrap } from "./kit";
import { LandingHeader } from "./SiteHeader";

export function Landing() {
  return (
    <>
      <LandingHeader />
      <main id="main" className="flex-1">
        <Hero />
        <Facts />
        <Sensors />
        <PhantomDemo />
        <Bench />
        <Audience />
        <FinalCta />
      </main>
      <div className="min-h-24 flex-1 lg:min-h-32" />
      <Footer />
    </>
  );
}

/* ------------------------------------------------------------------ hero -- */

function Hero() {
  const { t } = useLang();
  const router = useRouter();
  const [text, setText] = useState<string | null>(null);
  const [tooShort, setTooShort] = useState(false);
  const value = text ?? t.hero.prefill;

  function submit(e: React.FormEvent) {
    e.preventDefault();
    if (value.trim().length < 20) {
      setTooShort(true);
      document.getElementById("hero-answer")?.focus();
      return;
    }
    try {
      sessionStorage.setItem(PENDING_KEY, JSON.stringify({ text: value.trim() }));
    } catch {
      /* private mode: the check page simply opens empty */
    }
    router.push("/check");
  }

  return (
    <section
      className={`${wrap} grid grid-cols-1 items-center gap-12 pt-10 sm:pt-14 lg:grid-cols-[minmax(0,1.14fr)_minmax(0,0.86fr)] lg:gap-16 lg:pt-20`}
    >
      <div className="rise flex flex-col gap-6">
        <h1 className="text-[31px] font-bold leading-[1.08] tracking-[-0.025em] sm:text-[46px] lg:text-[50px] xl:text-[54px]">
          {t.hero.h1a}
          <br />
          <span className="text-brand">{t.hero.h1b}</span>
        </h1>
        <p className="max-w-[32em] text-lg leading-[1.55] text-ink-3 sm:text-[19px]">{t.hero.sub}</p>
        <form onSubmit={submit} className="mt-2 flex flex-col gap-2.5">
          <label htmlFor="hero-answer" className="text-sm font-semibold">
            {t.hero.answerLabel}
          </label>
          <div
            className={cn(
              "flex flex-col rounded-well border bg-surface transition-[border-color,box-shadow] duration-150 focus-within:border-ring focus-within:ring-3 focus-within:ring-ring/25",
              tooShort ? "border-bad" : "border-input",
            )}
          >
            <textarea
              id="hero-answer"
              name="answer"
              rows={4}
              value={value}
              onChange={(e) => {
                setText(e.target.value);
                setTooShort(false);
              }}
              aria-invalid={tooShort}
              aria-describedby={tooShort ? "hero-error" : undefined}
              autoComplete="off"
              onKeyDown={(e) => {
                if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) submit(e);
              }}
              placeholder={t.hero.placeholder}
              className="resize-none rounded-well bg-transparent px-4 pb-2 pt-3.5 text-base leading-[1.55] text-ink outline-none placeholder:text-faint focus-visible:outline-none"
            />
            <div className="flex flex-wrap items-center justify-between gap-3 px-2 pb-2 pl-4">
              <span className="hidden font-mono text-[13px] text-faint sm:inline">Ctrl + Enter</span>
              <Button type="submit" size="default" className="ml-auto px-5">
                {t.cta}
                <ArrowRightIcon aria-hidden size={18} />
              </Button>
            </div>
          </div>
          {tooShort && (
            <p id="hero-error" role="alert" className="text-sm text-bad">
              {t.errors.too_short}
            </p>
          )}
          {TELEGRAM_URL && (
            <a
              href={TELEGRAM_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="mt-2 flex items-center gap-2 self-start text-[15px] font-medium text-ink transition-colors duration-150 hover:text-brand"
            >
              <TelegramLogoIcon aria-hidden size={20} /> {t.hero.telegram}
            </a>
          )}
        </form>
      </div>
      <SampleCard />
    </section>
  );
}

/** Rows reveal one by one, then the verdict lands: the card shows how a check unfolds, not just its result. */
const STEP_MS = 520;

function SampleCard() {
  const { t } = useLang();
  const s = t.sample;
  const reduce = useReducedMotion();
  const total = s.rows.length;
  const [played, setPlayed] = useState(0);

  useEffect(() => {
    if (reduce) return;
    const timers = Array.from({ length: total + 1 }, (_, i) => setTimeout(() => setPlayed(i + 1), 450 + i * STEP_MS));
    return () => timers.forEach(clearTimeout);
  }, [reduce, total]);

  // Reduced motion: the finished card, no sequence.
  const step = reduce ? total + 1 : played;
  const done = step > total;
  return (
    <figure className="rise flex flex-col gap-3" style={{ animationDelay: "120ms" }}>
      <div className={`${card} shadow-card transition-[translate,scale,box-shadow] duration-500 ease-expo hover:-translate-y-1 hover:scale-[1.01] hover:shadow-card-hover motion-reduce:hover:translate-y-0 motion-reduce:hover:scale-100`}>
        <div className="flex flex-col gap-[18px] px-5 py-6 sm:px-7 sm:py-[26px]">
          <div className="flex flex-wrap items-center justify-between gap-3" aria-live="polite">
            <VerdictTag label={done ? "contradicted" : "pending"} text={done ? t.labels.contradicted : t.labels.pending} />
            <span className={cn("flex items-baseline gap-2 transition-opacity duration-300", done ? "opacity-100" : "opacity-0")} aria-hidden={!done}>
              <span className="font-mono text-[26px] font-semibold text-bad">96%</span>
              <span className="text-[13px] text-faint">{s.pWrong}</span>
            </span>
          </div>
          <p className="text-xl font-semibold leading-[1.4]">
            {s.before}
            <span className={cn("claim cursor-default hover:shadow-none", done ? "v-contradicted" : "v-pending")}>{s.mark}</span>
            {s.after}
          </p>
          <div className="flex flex-col border-t border-line">
            {s.rows.map((r, i) => {
              const Icon = SENSOR_ICON[r.icon];
              const shown = step > i;
              return (
                <div
                  key={r.icon}
                  className={cn(
                    "grid grid-cols-[24px_minmax(0,1fr)_auto] items-start gap-x-3 gap-y-0.5 border-b border-line-soft py-[11px] transition-opacity duration-300",
                    shown && r.tone === "skipped" && "opacity-60",
                  )}
                >
                  <span className="row-span-2 pt-px">
                    <Icon aria-hidden size={20} className="text-ink-3" />
                  </span>
                  <span className="text-[14.5px] font-semibold">{r.name}</span>
                  <ToneMark tone={shown ? r.tone : "pending"} label={t.tone[shown ? r.tone : "pending"]} size={18} />
                  {shown ? (
                    <span className="rise col-span-2 text-[13.5px] leading-[1.45] text-ink-4">{r.text}</span>
                  ) : (
                    <span aria-hidden className="col-span-2 mt-1 h-3.5 w-2/3 rounded-md bg-line-soft motion-safe:animate-pulse" />
                  )}
                </div>
              );
            })}
          </div>
          <div className={cn("flex items-center justify-between gap-4 transition-opacity duration-500", done ? "opacity-100" : "opacity-0")} aria-hidden={!done}>
            <div className="flex flex-col gap-1">
              <span className="text-[12.5px] text-faint">{t.card.correction}</span>
              <span className="text-base font-semibold">{s.correction}</span>
            </div>
            <CopyButton text={s.correction} label={t.card.copy} />
          </div>
        </div>
      </div>
      <figcaption className="text-[13px] text-faint">{t.hero.caption}</figcaption>
    </figure>
  );
}

/* ----------------------------------------------------------------- facts -- */

function Facts() {
  const { t } = useLang();
  return (
    <section className={`${wrap} ${section} flex flex-col gap-10`}>
      <h2 className={`${h2} reveal max-w-[18em]`}>{t.facts.h2}</h2>
      <div className="grid grid-cols-1 gap-10 border-t border-line-strong pt-8 md:grid-cols-[minmax(0,1.3fr)_minmax(0,1fr)_minmax(0,1fr)] md:gap-14">
        {t.facts.items.map((f, i) => (
          <div key={f.source} className="reveal group flex flex-col gap-2.5">
            <span className="origin-left self-start font-mono text-[44px] font-medium leading-none tracking-[-0.03em] transition-[scale,color] duration-300 ease-expo group-hover:scale-[1.05] motion-reduce:group-hover:scale-100 group-hover:text-brand lg:text-[64px]">{f.value}</span>
            <span className={cn("text-base leading-[1.5] text-ink-3", i === 0 && "max-w-[22em]")}>{f.text}</span>
            <span className="font-mono text-[12.5px] text-faint">{f.source}</span>
          </div>
        ))}
      </div>
    </section>
  );
}

/* --------------------------------------------------------------- sensors -- */

/** Pinned heading on the left, the five sensors scroll past on the right, each with the evidence it produces. */
function Sensors() {
  const { t } = useLang();
  const h = t.how;
  const stat = "font-mono text-[26px] font-medium leading-none tracking-[-0.02em] sm:text-[30px]";
  const items: { key: string; title: string; text: string; art: React.ReactNode }[] = [
    {
      key: "alibi",
      title: h.alibi.title,
      text: h.alibi.text,
      art: (
        <blockquote className="flex flex-col gap-1.5 border-l-2 border-brand py-0.5 pl-4">
          <span className="text-[15.5px] leading-[1.5]">{h.alibi.quote}</span>
          <span className="flex items-center gap-1.5 font-mono text-[12.5px] text-ink-4">
            <LockSimpleIcon aria-hidden size={14} className="shrink-0 text-brand" /> {h.alibi.meta}
          </span>
        </blockquote>
      ),
    },
    { key: "reinterrogation", title: h.rei.title, text: h.rei.text, art: <span className={stat}>{h.rei.stat}</span> },
    {
      key: "phantom",
      title: h.phantom.title,
      text: h.phantom.text,
      art: (
        <a
          href="#phantom"
          className="group inline-flex items-center gap-2.5 text-[15px] font-semibold text-brand transition-colors duration-150 hover:text-brand-hover"
        >
          <GhostIcon aria-hidden size={22} className="shrink-0" />
          {h.phantom.link}
          <ArrowRightIcon aria-hidden size={16} className="transition-transform duration-200 group-hover:translate-x-1" />
        </a>
      ),
    },
    { key: "fame", title: h.fame.title, text: h.fame.text, art: <span className={stat}>{h.fame.stat}</span> },
    {
      key: "citations",
      title: h.cit.title,
      text: h.cit.text,
      art: (
        <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-[14.5px]">
          <span className="font-mono text-sm font-medium text-ink-4 line-through decoration-bad">{h.cit.doi}</span>
          <span className="font-semibold text-bad">{h.cit.doiNote}</span>
        </div>
      ),
    },
  ];
  return (
    <section
      id="sensors"
      className={`${wrap} ${section} grid grid-cols-1 gap-12 lg:grid-cols-[minmax(0,0.85fr)_minmax(0,1.15fr)] lg:gap-20`}
    >
      <div className="reveal flex flex-col gap-4 lg:sticky lg:top-[calc(var(--c-header-h)+48px)] lg:self-start">
        <span className="text-[13px] font-semibold uppercase tracking-[0.08em] text-brand">{h.eyebrow}</span>
        <h2 className={h2}>{h.h2}</h2>
        <p className={lead}>{h.sub}</p>
      </div>
      <div className="flex flex-col">
        {items.map((it) => {
          const Icon = SENSOR_ICON[it.key];
          return (
            <article
              key={it.key}
              className="reveal group grid grid-cols-1 gap-x-5 gap-y-3 border-t border-line py-9 first:border-t-0 first:pt-0 last:pb-0 sm:grid-cols-[28px_minmax(0,1fr)]"
            >
              <span className="self-start text-brand transition-[scale] duration-300 ease-expo motion-reduce:group-hover:scale-100 group-hover:scale-[1.18] sm:pt-0.5">
                <Icon aria-hidden size={28} />
              </span>
              <div className="flex flex-col gap-3">
                <h3 className="text-xl font-semibold transition-colors duration-200 group-hover:text-brand">{it.title}</h3>
                <p className="max-w-[36em] text-[15.5px] leading-[1.6] text-ink-3 transition-colors duration-200 group-hover:text-ink-2">{it.text}</p>
                <div className="mt-2">{it.art}</div>
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
}

/* --------------------------------------------------------------- phantom -- */

function PhantomDemo() {
  const { t } = useLang();
  const p = t.phantomDemo;
  return (
    <section id="phantom" className={`${wrap} ${section} flex flex-col gap-10`}>
      <div className="reveal flex flex-col gap-4">
        <h2 className={`${h2} max-w-[20em]`}>{p.h2}</h2>
        <p className={lead}>{p.sub}</p>
      </div>
      <div className="reveal grid grid-cols-1 divide-y divide-line border-y border-line md:grid-cols-2 md:divide-x md:divide-y-0">
        <Transcript label={p.realLabel} q={p.realQ} a={p.realA} note={p.realNote} honest />
        <Transcript label={p.ctrlLabel} q={p.ctrlQ} a={p.ctrlA} note={p.ctrlNote} />
      </div>
      <p className="text-[13.5px] text-faint">{p.disclaimer}</p>
    </section>
  );
}

function Transcript({ label, q, a, note, honest = false }: { label: string; q: string; a: string; note: string; honest?: boolean }) {
  const Icon = honest ? CheckCircleIcon : WarningCircleIcon;
  return (
    <div className="group flex flex-col gap-5 py-8 md:px-10 md:first:pl-0 md:last:pr-0">
      <span className={cn("text-sm font-semibold", honest ? "text-ink-3" : "text-sus")}>{label}</span>
      <div className="max-w-[85%] origin-right self-end rounded-card bg-chip px-4 py-3 text-base leading-[1.45] transition-[scale] duration-300 ease-expo motion-reduce:group-hover:scale-100 group-hover:scale-[1.02]">{q}</div>
      <p className="text-[17px] leading-[1.9]">
        <span className={cn("claim cursor-default group-hover:shadow-glow-soft", honest ? "v-confirmed" : "v-suspicious")}>{a}</span>
      </p>
      <div className="flex-1" />
      <span className={cn("flex items-center gap-2 text-sm", honest ? "font-medium text-ok" : "font-semibold text-sus")}>
        <Icon aria-hidden size={18} weight="fill" className="shrink-0 transition-[scale] duration-300 ease-expo motion-reduce:group-hover:scale-100 group-hover:scale-[1.2]" /> {note}
      </span>
    </div>
  );
}

/* ----------------------------------------------------------------- bench -- */

function Bench() {
  const { t } = useLang();
  const b = t.bench;
  return (
    <section
      id="bench"
      className={`${wrap} ${section} grid grid-cols-1 items-start gap-10 lg:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)] lg:gap-[72px]`}
    >
      <div className="reveal flex flex-col gap-4">
        <h2 className={h2}>{b.h2}</h2>
        <p className={lead}>{b.sub}</p>
        <a
          href={`${REPO}/tree/main/senim/bench`}
          target="_blank"
          rel="noopener noreferrer"
          className="group mt-1.5 flex items-center gap-2 self-start text-[15px] font-semibold text-brand transition-colors duration-150 hover:text-brand-hover"
        >
          {b.link} <ArrowRightIcon aria-hidden size={16} className="transition-transform duration-200 group-hover:translate-x-1" />
        </a>
      </div>
      <div className="reveal flex flex-col">
        <div className="flex justify-between gap-4 border-b border-line-strong pb-3 text-[13px] text-faint">
          <span>{b.colSystem}</span>
          <span className="text-right">{b.colF1}</span>
        </div>
        {b.rows.map((r, i) => (
          <div key={r.name} className={cn("group flex items-baseline justify-between gap-4 py-[22px]", i < b.rows.length - 1 && "border-b border-line")}>
            <span className={cn("text-[17px] transition-colors duration-200 group-hover:text-ink", r.strong ? "font-semibold" : "text-ink-3")}>{r.name}</span>
            <span
              className={cn(
                "origin-right font-mono text-[28px] tabular-nums transition-[scale] duration-300 ease-expo motion-reduce:group-hover:scale-100 group-hover:scale-[1.06] sm:text-[40px]",
                r.strong ? "font-semibold text-brand" : i === 0 ? "font-medium text-faint" : "font-medium",
              )}
            >
              {r.value}
            </span>
          </div>
        ))}
        <p className="mt-2 max-w-[42em] text-sm leading-[1.55] text-faint">{b.note}</p>
      </div>
    </section>
  );
}

/* -------------------------------------------------------------- audience -- */

function Audience() {
  const { t } = useLang();
  const a = t.audience;
  const others = [
    { Icon: StudentIcon, ...a.students },
    { Icon: UsersThreeIcon, ...a.parents },
    { Icon: NewspaperIcon, ...a.press },
  ];
  return (
    <section id="gym" className={`${wrap} ${section} flex flex-col gap-10`}>
      <h2 className={`${h2} reveal`}>{a.h2}</h2>
      <div className="grid grid-cols-1 items-start gap-12 lg:grid-cols-[minmax(0,1.35fr)_minmax(0,0.65fr)] lg:gap-16">
        <TrustGym />
        <div className="flex flex-col">
          {others.map(({ Icon, title, text }) => (
            <div key={title} className="reveal group flex flex-col gap-2 border-t border-line py-7 first:border-t-0 first:pt-0 lg:first:pt-2">
              <h3 className="flex items-center gap-2.5 text-lg font-semibold transition-colors duration-200 group-hover:text-brand">
                <Icon aria-hidden size={22} className="shrink-0 text-brand transition-[scale] duration-300 ease-expo motion-reduce:group-hover:scale-100 group-hover:scale-[1.18]" /> {title}
              </h3>
              <p className="text-[15.5px] leading-[1.6] text-ink-3 transition-colors duration-200 group-hover:text-ink-2">{text}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

/** One Trust Gym task right on the page: pick the false sentence, then every sentence shows its verdict. */
function TrustGym() {
  const { t } = useLang();
  const g = t.audience.teacher;
  const [picked, setPicked] = useState<number | null>(null);
  const solved = picked === g.wrong;
  return (
    <div className="reveal flex flex-col gap-7">
      <div className="flex flex-col gap-3">
        <h3 className="flex items-center gap-3 text-[22px] font-semibold">
          <ChalkboardTeacherIcon aria-hidden size={30} className="shrink-0 text-brand" /> {g.title}
        </h3>
        <p className="max-w-[40em] text-[15.5px] leading-[1.6] text-ink-3">{g.text}</p>
      </div>
      <div className="flex flex-col gap-4 border-t border-line pt-7">
        <div className="flex min-h-9 flex-wrap items-center justify-between gap-x-4 gap-y-1">
          <span id="gym-task" className="text-base font-semibold">
            {g.task}
          </span>
          {picked !== null && (
            <Button variant="link" size="text" className="gap-1.5 text-sm" onClick={() => setPicked(null)}>
              <ArrowCounterClockwiseIcon aria-hidden size={16} /> {g.reset}
            </Button>
          )}
        </div>
        <div role="group" aria-labelledby="gym-task" aria-describedby="gym-hint" className="flex flex-col gap-2">
          {g.sentences.map((s, i) => {
            const isWrong = i === g.wrong;
            const mark = solved ? (isWrong ? "v-contradicted" : "v-confirmed") : picked === i ? "v-confirmed" : "";
            const revealed = solved || picked === i;
            return (
              <button
                key={s}
                type="button"
                aria-pressed={picked === i}
                disabled={solved}
                onClick={() => setPicked(i)}
                className={cn(
                  "grid grid-cols-[minmax(0,1fr)_20px] items-start gap-3 rounded-well border bg-surface px-4 py-3.5 text-left text-base leading-[1.6] transition-[border-color,scale,box-shadow] duration-200 ease-expo",
                  revealed
                    ? "border-line-strong"
                    : "border-line hover:scale-[1.012] hover:border-brand hover:shadow-glow-soft motion-reduce:hover:scale-100",
                  solved && "cursor-default",
                )}
              >
                <span>
                  <span className={cn(mark && `claim cursor-[inherit] hover:shadow-none ${mark}`)}>{s}</span>
                </span>
                <span className="pt-1">
                  {revealed && (
                    <ToneMark
                      tone={solved && isWrong ? "against" : "for"}
                      label={solved && isWrong ? t.labels.contradicted : t.labels.confirmed}
                      size={20}
                    />
                  )}
                </span>
              </button>
            );
          })}
        </div>
        <div aria-live="polite" className="min-h-6">
          {picked === null ? (
            <p id="gym-hint" className="text-[13.5px] text-ink-4">
              {g.hint}
            </p>
          ) : (
            <m.p
              key={picked}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              className={cn("flex items-start gap-2 text-[15px] leading-[1.5]", solved ? "text-ok" : "text-sus")}
            >
              {solved ? (
                <CheckCircleIcon aria-hidden size={18} weight="fill" className="mt-0.5 shrink-0" />
              ) : (
                <WarningCircleIcon aria-hidden size={18} weight="fill" className="mt-0.5 shrink-0" />
              )}
              {solved ? g.right : g.again}
            </m.p>
          )}
        </div>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------- final CTA -- */

function FinalCta() {
  const { t } = useLang();
  return (
    <section className={`${wrap} ${section}`}>
      <div className="reveal flex flex-col items-start gap-8 border-t border-line-strong pt-12 lg:flex-row lg:items-end lg:justify-between lg:gap-12 lg:pt-16">
        <h2 className="max-w-[15em] text-[32px] font-bold leading-[1.1] tracking-[-0.025em] sm:text-[44px]">
          {t.final.a} <span className="font-normal text-ink-3">{t.final.b}</span>
        </h2>
        <Button asChild size="xl" className="group shrink-0">
          <Link href="/check">
            {t.cta} <ArrowRightIcon aria-hidden size={18} className="transition-transform duration-200 group-hover:translate-x-1" />
          </Link>
        </Button>
      </div>
    </section>
  );
}

