"use client";

import {
  ArrowRightIcon,
  BooksIcon,
  ChalkboardTeacherIcon,
  CheckCircleIcon,
  EyeIcon,
  GhostIcon,
  LinkSimpleIcon,
  LockSimpleIcon,
  NewspaperIcon,
  StudentIcon,
  TelegramLogoIcon,
  UsersThreeIcon,
  WarningCircleIcon,
  XCircleIcon,
} from "@phosphor-icons/react";
import { m } from "motion/react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogTitle } from "@/components/ui/dialog";
import { useLang } from "@/lib/lang";
import { PENDING_KEY } from "@/lib/pending";
import { cn } from "@/lib/utils";
import { CopyButton } from "./CopyButton";
import { Footer, REPO, TELEGRAM_URL } from "./Footer";
import { SENSOR_ICON, ToneMark, card, wrap } from "./kit";
import { LandingHeader } from "./SiteHeader";

const h2 = "text-[30px] font-semibold leading-[1.12] tracking-[-0.02em] sm:text-[40px]";
const lead = "text-[17px] leading-[1.6] text-ink-3";
const section = "pt-20 lg:pt-28";

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
      <div className="min-h-20 flex-1 lg:min-h-[120px]" />
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
      className={`${wrap} grid grid-cols-1 items-center gap-12 pt-10 sm:pt-14 lg:grid-cols-[minmax(0,1.12fr)_minmax(0,0.88fr)] lg:gap-[72px] lg:pt-[72px]`}
    >
      <div className="rise flex flex-col gap-6">
        <h1 className="text-[36px] font-bold leading-[1.06] tracking-[-0.025em] sm:text-[46px] lg:text-[52px]">
          {t.hero.h1a}
          <br />
          <span className="text-brand">{t.hero.h1b}</span>
        </h1>
        <p className="max-w-[34em] text-lg leading-[1.55] text-ink-3 sm:text-[19px]">{t.hero.sub}</p>
        <form onSubmit={submit} className="mt-2 flex flex-col gap-2.5">
          <label htmlFor="hero-answer" className="text-sm font-semibold">
            {t.hero.answerLabel}
          </label>
          <textarea
            id="hero-answer"
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
            className="resize-none rounded-well border border-input bg-surface px-4 py-3.5 text-base leading-[1.55] text-ink outline-none transition-colors duration-150 placeholder:text-faint focus-visible:border-ring focus-visible:outline-none focus-visible:ring-3 focus-visible:ring-ring/25"
          />
          {tooShort && (
            <p id="hero-error" role="alert" className="text-sm text-bad">
              {t.errors.too_short}
            </p>
          )}
          <div className="mt-1.5 flex flex-wrap items-center gap-5">
            <Button type="submit" size="lg">
              {t.cta}
              <ArrowRightIcon aria-hidden size={18} />
            </Button>
            {TELEGRAM_URL && (
              <a href={TELEGRAM_URL} target="_blank" rel="noopener noreferrer" className="flex items-center gap-2 text-[15px] font-medium text-ink hover:text-brand">
                <TelegramLogoIcon aria-hidden size={20} /> {t.hero.telegram}
              </a>
            )}
          </div>
        </form>
      </div>
      <SampleCard />
    </section>
  );
}

function SampleCard() {
  const { t } = useLang();
  const s = t.sample;
  return (
    <figure className="rise flex flex-col gap-3" style={{ animationDelay: "120ms" }}>
      <div className={`${card} flex flex-col gap-[18px] px-5 py-6 shadow-card sm:px-7 sm:py-[26px]`}>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <span className="flex items-center gap-2 text-[15px] font-semibold text-bad">
            <XCircleIcon aria-hidden size={20} /> {t.labels.contradicted}
          </span>
          <span className="flex items-baseline gap-2">
            <span className="font-mono text-[26px] font-semibold text-bad">96%</span>
            <span className="text-[13px] text-faint">{s.pWrong}</span>
          </span>
        </div>
        <p className="text-xl font-semibold leading-[1.4]">
          {s.before}
          <span className="claim v-contradicted cursor-default hover:shadow-none">{s.mark}</span>
          {s.after}
        </p>
        <div className="flex flex-col border-t border-line">
          {s.rows.map((r) => {
            const Icon = SENSOR_ICON[r.icon];
            return (
              <div key={r.icon} className={cn("grid grid-cols-[24px_minmax(0,1fr)_auto] items-start gap-x-3 gap-y-0.5 border-b border-line-soft py-[11px]", r.tone === "skipped" && "opacity-60")}>
                <span className="row-span-2 pt-px">
                  <Icon aria-hidden size={20} className="text-ink-3" />
                </span>
                <span className="text-[14.5px] font-semibold">{r.name}</span>
                <ToneMark tone={r.tone} label={t.tone[r.tone]} size={18} />
                <span className="col-span-2 text-[13.5px] leading-[1.45] text-ink-4">{r.text}</span>
              </div>
            );
          })}
        </div>
        <div className="flex items-center justify-between gap-4">
          <div className="flex flex-col gap-1">
            <span className="text-[12.5px] text-faint">{t.card.correction}</span>
            <span className="text-base font-semibold">{s.correction}</span>
          </div>
          <CopyButton text={s.correction} label={t.card.copy} />
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
      <h2 className={`${h2} max-w-[18em]`}>{t.facts.h2}</h2>
      <div className="grid grid-cols-1 gap-10 border-t border-line-strong pt-8 md:grid-cols-[minmax(0,1.3fr)_minmax(0,1fr)_minmax(0,1fr)] md:gap-14">
        {t.facts.items.map((f, i) => (
          <div key={f.source} className="flex flex-col gap-2.5">
            <span className="font-mono text-[44px] font-medium leading-none tracking-[-0.03em] lg:text-[60px]">{f.value}</span>
            <span className={cn("text-base leading-[1.5] text-ink-3", i === 0 && "max-w-[22em]")}>{f.text}</span>
            <span className="font-mono text-[12.5px] text-faint">{f.source}</span>
          </div>
        ))}
      </div>
    </section>
  );
}

/* --------------------------------------------------------------- sensors -- */

function Sensors() {
  const { t } = useLang();
  const h = t.how;
  const title = "flex items-center gap-2.5 text-xl font-semibold";
  const body = "text-[15.5px] leading-[1.55] text-ink-3";
  const cell = `${card} flex flex-col gap-3.5 p-6 sm:p-7`;
  return (
    <section id="sensors" className={`${wrap} ${section} flex scroll-mt-6 flex-col gap-9`}>
      <div className="flex max-w-[44em] flex-col gap-3.5">
        <span className="text-[13px] font-semibold uppercase tracking-[0.08em] text-brand">{h.eyebrow}</span>
        <h2 className={h2}>{h.h2}</h2>
        <p className={lead}>{h.sub}</p>
      </div>
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:auto-rows-[minmax(250px,auto)] lg:grid-cols-4">
        <div className={`${cell} md:col-span-2`}>
          <span className={title}>
            <BooksIcon aria-hidden size={24} className="text-brand" /> {h.alibi.title}
          </span>
          <p className={`${body} max-w-[36em]`}>{h.alibi.text}</p>
          <div className="flex-1" />
          <div className="flex items-start gap-3 rounded-well bg-well px-4 py-3.5">
            <LockSimpleIcon aria-hidden size={18} className="mt-0.5 shrink-0 text-brand" />
            <div className="flex flex-col gap-1">
              <span className="text-[15px]">{h.alibi.quote}</span>
              <span className="font-mono text-[12.5px] text-ink-4">{h.alibi.meta}</span>
            </div>
          </div>
        </div>
        <div className={cell}>
          <span className={title}>
            <UsersThreeIcon aria-hidden size={24} className="text-brand" /> {h.rei.title}
          </span>
          <p className={body}>{h.rei.text}</p>
          <div className="flex-1" />
          <span className="font-mono text-[15px] font-medium">{h.rei.stat}</span>
        </div>
        <div className={cell}>
          <span className={title}>
            <EyeIcon aria-hidden size={24} className="text-brand" /> {h.fame.title}
          </span>
          <p className={body}>{h.fame.text}</p>
          <div className="flex-1" />
          <span className="font-mono text-[15px] font-medium">{h.fame.stat}</span>
        </div>
        <div className="grid grid-cols-1 items-start gap-6 rounded-card bg-brand-soft p-6 sm:grid-cols-[minmax(0,1fr)_96px] sm:p-7 md:col-span-2">
          <div className="flex flex-col gap-3.5">
            <span className="text-xl font-semibold">{h.phantom.title}</span>
            <p className="text-[15.5px] leading-[1.55] text-brand-soft-ink">{h.phantom.text}</p>
            <a href="#phantom" className="mt-1 flex items-center gap-2 self-start text-[15px] font-semibold text-brand hover:text-brand-hover">
              {h.phantom.link} <ArrowRightIcon aria-hidden size={16} />
            </a>
          </div>
          <GhostIcon aria-hidden size={96} className="hidden text-brand sm:block" />
        </div>
        <div className={`${cell} md:col-span-2`}>
          <span className={title}>
            <LinkSimpleIcon aria-hidden size={24} className="text-brand" /> {h.cit.title}
          </span>
          <p className={`${body} max-w-[36em]`}>{h.cit.text}</p>
          <div className="flex-1" />
          <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-[14.5px]">
            <span className="font-mono text-sm font-medium text-ink-4 line-through decoration-bad">{h.cit.doi}</span>
            <span className="font-semibold text-bad">{h.cit.doiNote}</span>
          </div>
        </div>
      </div>
    </section>
  );
}

/* --------------------------------------------------------------- phantom -- */

function PhantomDemo() {
  const { t } = useLang();
  const p = t.phantomDemo;
  const bubble = "max-w-[80%] self-end rounded-card bg-chip px-4 py-3 text-base leading-[1.45]";
  return (
    <section id="phantom" className={`${wrap} ${section} flex scroll-mt-6 flex-col gap-9`}>
      <div className="flex max-w-[44em] flex-col gap-3.5">
        <h2 className={h2}>{p.h2}</h2>
        <p className={lead}>{p.sub}</p>
      </div>
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <div className={`${card} flex flex-col gap-[18px] p-6 sm:p-7`}>
          <span className="text-sm font-semibold text-ink-3">{p.realLabel}</span>
          <div className={bubble}>{p.realQ}</div>
          <p className="text-[17px] leading-[1.55]">{p.realA}</p>
          <div className="flex-1" />
          <span className="flex items-center gap-2 text-sm font-medium text-ok">
            <CheckCircleIcon aria-hidden size={18} className="shrink-0" /> {p.realNote}
          </span>
        </div>
        <div className="flex flex-col gap-[18px] rounded-card border border-sus-line bg-surface p-6 sm:p-7">
          <span className="text-sm font-semibold text-sus">{p.ctrlLabel}</span>
          <div className={bubble}>{p.ctrlQ}</div>
          <p className="text-[17px] leading-[1.55]">{p.ctrlA}</p>
          <div className="flex-1" />
          <span className="flex items-center gap-2 text-sm font-semibold text-sus">
            <WarningCircleIcon aria-hidden size={18} className="shrink-0" /> {p.ctrlNote}
          </span>
        </div>
      </div>
      <p className="text-[13.5px] text-faint">{p.disclaimer}</p>
    </section>
  );
}

/* ----------------------------------------------------------------- bench -- */

function Bench() {
  const { t } = useLang();
  const b = t.bench;
  return (
    <section
      id="bench"
      className={`${wrap} ${section} grid scroll-mt-6 grid-cols-1 items-start gap-10 lg:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)] lg:gap-[72px]`}
    >
      <div className="flex flex-col gap-4">
        <h2 className={h2}>{b.h2}</h2>
        <p className={lead}>{b.sub}</p>
        <a
          href={`${REPO}/tree/main/senim/bench`}
          target="_blank"
          rel="noopener noreferrer"
          className="mt-1.5 flex items-center gap-2 self-start text-[15px] font-semibold text-brand hover:text-brand-hover"
        >
          {b.link} <ArrowRightIcon aria-hidden size={16} />
        </a>
      </div>
      <div className="flex flex-col">
        <div className="flex justify-between gap-4 border-b border-line-strong pb-3 text-[13px] text-faint">
          <span>{b.colSystem}</span>
          <span className="text-right">{b.colF1}</span>
        </div>
        {b.rows.map((r, i) => (
          <div key={r.name} className={cn("flex items-baseline justify-between gap-4 py-[22px]", i < b.rows.length - 1 && "border-b border-line")}>
            <span className={cn("text-[17px]", r.strong ? "font-semibold" : "text-ink-3")}>{r.name}</span>
            <span
              className={cn(
                "font-mono text-[28px] tabular-nums sm:text-[36px]",
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
  const [gymOpen, setGymOpen] = useState(false);
  const tile = "grid grid-cols-1 items-start gap-[18px] p-6 sm:grid-cols-[44px_minmax(0,1fr)] sm:p-7";
  const title = "text-xl font-semibold";
  const body = "text-[15.5px] leading-[1.55]";
  return (
    <section id="gym" className={`${wrap} ${section} flex scroll-mt-6 flex-col gap-9`}>
      <h2 className={h2}>{a.h2}</h2>
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <div className={`${card} ${tile}`}>
          <ChalkboardTeacherIcon aria-hidden size={40} className="text-brand" />
          <div className="flex flex-col gap-2.5">
            <span className={title}>{a.teacher.title}</span>
            <p className={`${body} max-w-[34em] text-ink-3`}>{a.teacher.text}</p>
            <Button variant="strong" className="mt-2 h-12 self-start px-[22px]" onClick={() => setGymOpen(true)}>
              {a.teacher.cta}
            </Button>
          </div>
        </div>
        <div className={`${card} ${tile}`}>
          <StudentIcon aria-hidden size={40} className="text-brand" />
          <div className="flex flex-col gap-2.5">
            <span className={title}>{a.students.title}</span>
            <p className={`${body} text-ink-3`}>{a.students.text}</p>
          </div>
        </div>
        <div className={`${card} ${tile}`}>
          <UsersThreeIcon aria-hidden size={40} className="text-brand" />
          <div className="flex flex-col gap-2.5">
            <span className={title}>{a.parents.title}</span>
            <p className={`${body} text-ink-3`}>{a.parents.text}</p>
          </div>
        </div>
        <div className={`rounded-card bg-brand-soft ${tile}`}>
          <NewspaperIcon aria-hidden size={40} className="text-brand" />
          <div className="flex flex-col gap-2.5">
            <span className={title}>{a.press.title}</span>
            <p className={`${body} text-brand-soft-ink`}>{a.press.text}</p>
          </div>
        </div>
      </div>
      <GymExercise open={gymOpen} onOpenChange={setGymOpen} />
    </section>
  );
}

/** One Trust Gym task: find the false sentence, then see the verdicts. */
function GymExercise({ open, onOpenChange }: { open: boolean; onOpenChange: (o: boolean) => void }) {
  const { t } = useLang();
  const g = t.audience.teacher;
  const [picked, setPicked] = useState<number | null>(null);
  const solved = picked === g.wrong;
  return (
    <Dialog
      open={open}
      onOpenChange={(o) => {
        onOpenChange(o);
        if (!o) setPicked(null);
      }}
    >
      <DialogContent className="gap-5 rounded-card border-line bg-surface p-7 sm:max-w-[520px]">
        <DialogTitle className="text-xl font-semibold">{g.task}</DialogTitle>
        <DialogDescription className="sr-only">{g.title}</DialogDescription>
        <p className="text-[17px] leading-[2]">
          {g.sentences.map((s, i) => {
            const shown = solved ? (i === g.wrong ? "claim v-contradicted" : "claim v-confirmed") : "claim hover:bg-well";
            return (
              <span key={s}>
                <button
                  type="button"
                  aria-pressed={picked === i}
                  onClick={() => setPicked(i)}
                  className={cn(shown, "text-left")}
                >
                  {s}
                </button>{" "}
              </span>
            );
          })}
        </p>
        {picked !== null && (
          <m.p
            key={picked}
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            className={cn("flex items-start gap-2 text-[15px] leading-[1.5]", solved ? "text-ok" : "text-sus")}
          >
            {solved ? <CheckCircleIcon aria-hidden size={18} className="mt-0.5 shrink-0" /> : <WarningCircleIcon aria-hidden size={18} className="mt-0.5 shrink-0" />}
            {solved ? g.right : g.again}
          </m.p>
        )}
      </DialogContent>
    </Dialog>
  );
}

/* ------------------------------------------------------------- final CTA -- */

function FinalCta() {
  const { t } = useLang();
  return (
    <section className={`${wrap} flex flex-col items-start gap-6 pt-24 lg:pt-[136px]`}>
      <h2 className="max-w-[16em] text-[34px] font-bold leading-[1.08] tracking-[-0.025em] sm:text-[48px]">
        {t.final.a} <span className="text-brand">{t.final.b}</span>
      </h2>
      <Button asChild size="xl">
        <Link href="/check">
          {t.cta} <ArrowRightIcon aria-hidden size={18} />
        </Link>
      </Button>
    </section>
  );
}
