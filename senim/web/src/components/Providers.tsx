"use client";

import { LazyMotion, MotionConfig, domAnimation } from "motion/react";
import { TooltipProvider } from "@/components/ui/tooltip";
import { LangProvider, useLang } from "@/lib/lang";
import type { Lang } from "@/lib/types";

/** Client-side context for the whole app: language, Motion (lazy, 4.6 KB) and tooltips. */
export function Providers({ lang, children }: { lang: Lang; children: React.ReactNode }) {
  return (
    <LangProvider initial={lang}>
      <LazyMotion features={domAnimation} strict>
        <MotionConfig reducedMotion="user" transition={{ duration: 0.22, ease: [0.16, 1, 0.3, 1] }}>
          <TooltipProvider delayDuration={200}>
            <SkipLink />
            {children}
          </TooltipProvider>
        </MotionConfig>
      </LazyMotion>
    </LangProvider>
  );
}

function SkipLink() {
  const { t } = useLang();
  return (
    <a
      href="#main"
      className="sr-only rounded-full bg-primary px-5 py-3 font-semibold text-primary-foreground focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-50"
    >
      {t.skip}
    </a>
  );
}
