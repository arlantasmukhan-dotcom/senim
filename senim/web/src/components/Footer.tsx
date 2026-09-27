"use client";

import Link from "next/link";
import { useLang } from "@/lib/lang";
import { wrap } from "./kit";

export const REPO = "https://github.com/yv7m8fchnb-dev/Wit-teens";
/** Set NEXT_PUBLIC_TELEGRAM_URL once the bot exists; until then the Telegram links stay hidden. */
export const TELEGRAM_URL = process.env.NEXT_PUBLIC_TELEGRAM_URL ?? "";

export function Footer() {
  const { t } = useLang();
  const f = t.footer;
  const link = "text-ink transition-colors duration-150 hover:text-brand";
  return (
    <footer className={`${wrap} no-print`}>
      <div className="grid grid-cols-1 gap-10 border-t border-line-strong pb-11 pt-9 md:grid-cols-[minmax(0,1.4fr)_repeat(2,minmax(0,1fr))] md:gap-12">
        <div className="flex flex-col gap-2.5">
          <span translate="no" className="text-[19px] font-bold">
            SENIM <span className="text-sm font-normal text-faint">{f.tagline}</span>
          </span>
          <p className="max-w-[30em] text-sm leading-[1.55] text-ink-4">{f.privacy}</p>
        </div>
        <nav className="flex flex-col gap-2.5 text-[14.5px]">
          <Link href="/#sensors" className={link}>
            {f.method}
          </Link>
          <a href={`${REPO}/tree/main/senim/bench`} target="_blank" rel="noopener noreferrer" className={link}>
            {f.dataset}
          </a>
          <a href={REPO} target="_blank" rel="noopener noreferrer" className={link}>
            {f.github}
          </a>
        </nav>
        <nav className="flex flex-col gap-2.5 text-[14.5px]">
          {TELEGRAM_URL && (
            <a href={TELEGRAM_URL} target="_blank" rel="noopener noreferrer" className={link}>
              {f.bot}
            </a>
          )}
          <Link href="/#gym" className={link}>
            Trust Gym
          </Link>
          <span className="text-faint">{f.event}</span>
        </nav>
      </div>
    </footer>
  );
}
