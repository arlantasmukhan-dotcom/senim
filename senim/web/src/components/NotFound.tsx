"use client";

import { ArrowLeftIcon } from "@phosphor-icons/react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { useLang } from "@/lib/lang";
import { Footer } from "./Footer";
import { h2, lead, wrap } from "./kit";
import { LangSwitch } from "./SiteHeader";

export function NotFound() {
  const { t } = useLang();
  const n = t.notFound;
  return (
    <>
      <header className="border-b border-line">
        <div className={`${wrap} flex h-(--c-header-h) items-center justify-between`}>
          <Link href="/" translate="no" className="text-[21px] font-bold tracking-[-0.01em] text-ink">
            SENIM
          </Link>
          <LangSwitch />
        </div>
      </header>
      <main id="main" className={`${wrap} rise flex flex-1 flex-col items-start gap-5 pt-24 lg:pt-36`}>
        <span className="font-mono text-[64px] font-medium leading-none tracking-[-0.03em] text-faint sm:text-[88px]">404</span>
        <h1 className={h2}>{n.h1}</h1>
        <p className={lead}>{n.text}</p>
        <Button asChild size="lg" className="mt-3">
          <Link href="/">
            <ArrowLeftIcon aria-hidden size={18} /> {n.back}
          </Link>
        </Button>
      </main>
      <div className="min-h-24 flex-1" />
      <Footer />
    </>
  );
}
