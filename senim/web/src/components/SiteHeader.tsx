"use client";

import { ListIcon } from "@phosphor-icons/react";
import Link from "next/link";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Drawer, DrawerContent, DrawerDescription, DrawerTitle } from "@/components/ui/drawer";
import { LANG_LABEL, LANGS } from "@/lib/i18n";
import { useLang } from "@/lib/lang";
import { cn } from "@/lib/utils";

/** Sticky, frosted header (blur only on this fixed layer, never on scrolling content). */
const sticky = "sticky top-0 z-(--z-header) border-b border-line bg-page/85 backdrop-blur-md supports-[not(backdrop-filter:blur(1px))]:bg-page";

interface NavItem {
  href: string;
  label: string;
  current?: boolean;
}

export function LangSwitch({ className }: { className?: string }) {
  const { lang, setLang } = useLang();
  return (
    <div className={cn("flex gap-3.5 font-mono text-[13px] font-medium", className)} role="group" aria-label="Language">
      {LANGS.map((l) => (
        <button
          key={l}
          type="button"
          onClick={() => setLang(l)}
          aria-pressed={l === lang}
          className={cn(
            "px-0.5 py-1.5 transition-colors duration-150",
            l === lang ? "text-ink shadow-[inset_0_-2px_0_var(--ink)]" : "text-faint hover:text-ink",
          )}
        >
          {LANG_LABEL[l]}
        </button>
      ))}
    </div>
  );
}

function Brand({ size = "lg" }: { size?: "lg" | "md" }) {
  const { t } = useLang();
  return (
    <Link href="/" className="flex items-baseline gap-2 text-ink">
      <span translate="no" className={cn("font-bold tracking-[-0.01em]", size === "lg" ? "text-[21px]" : "text-[20px]")}>SENIM</span>
      <span className="hidden text-sm text-faint md:inline">{t.brandSub}</span>
    </Link>
  );
}

/** Phone header from the "MobileResults" mockup: brand, current language, menu. */
function MobileBar({ items }: { items: NavItem[] }) {
  const { t, lang, setLang } = useLang();
  const [open, setOpen] = useState(false);
  return (
    <div className="flex h-14 items-center gap-2 pl-4 pr-2 md:hidden">
      <Link href="/" translate="no" className="flex-1 text-lg font-bold text-ink">
        SENIM
      </Link>
      <Button variant="bare" size="icon-touch" className="w-auto rounded-full px-2.5 font-mono text-[13px] font-medium" onClick={() => setOpen(true)}>
        {LANG_LABEL[lang]}
      </Button>
      <Button variant="bare" size="icon-touch" aria-label={t.nav.menu} onClick={() => setOpen(true)}>
        <ListIcon aria-hidden size={22} />
      </Button>
      <Drawer open={open} onOpenChange={setOpen}>
        <DrawerContent>
          <DrawerTitle className="sr-only">{t.nav.menu}</DrawerTitle>
          <DrawerDescription className="sr-only">SENIM</DrawerDescription>
          <nav className="flex flex-col px-5 pb-2 pt-4">
            {items.map((i) => (
              <Link
                key={i.href}
                href={i.href}
                onClick={() => setOpen(false)}
                aria-current={i.current ? "page" : undefined}
                className={cn(
                  "flex h-12 items-center border-b border-line text-[17px]",
                  i.current ? "font-semibold text-ink" : "text-ink-3",
                )}
              >
                {i.label}
              </Link>
            ))}
          </nav>
          <div className="flex gap-2 px-5 pb-8 pt-4">
            {LANGS.map((l) => (
              <Button
                key={l}
                variant={l === lang ? "default" : "outline"}
                size="default"
                className="flex-1 font-mono"
                aria-pressed={l === lang}
                onClick={() => setLang(l)}
              >
                {LANG_LABEL[l]}
              </Button>
            ))}
          </div>
        </DrawerContent>
      </Drawer>
    </div>
  );
}

export function LandingHeader() {
  const { t } = useLang();
  const items: NavItem[] = [
    { href: "#sensors", label: t.nav.how },
    { href: "#gym", label: t.nav.gym },
    { href: "#bench", label: t.nav.accuracy },
    { href: "/check", label: t.cta },
  ];
  return (
    <header className={sticky}>
      <MobileBar items={items} />
      <div className="mx-auto hidden h-(--c-header-h) w-full max-w-[1248px] items-center gap-10 px-6 md:flex">
        <Brand />
        <nav className="flex flex-1 gap-7 text-[15px]">
          {items.slice(0, 3).map((i) => (
            <a key={i.href} href={i.href} className="text-ink-3 transition-colors duration-150 hover:text-ink">
              {i.label}
            </a>
          ))}
        </nav>
        <LangSwitch />
        <Button asChild size="default" className="px-[22px]">
          <Link href="/check">{t.cta}</Link>
        </Button>
      </div>
    </header>
  );
}

export function AppHeader() {
  const { t } = useLang();
  const items: NavItem[] = [
    { href: "/check", label: t.nav.check, current: true },
    { href: "/#gym", label: t.nav.gym },
    { href: "/#bench", label: t.nav.accuracy },
    { href: "/#sensors", label: t.nav.how },
  ];
  return (
    <header className={cn(sticky, "no-print")}>
      <MobileBar items={items} />
      <div className="mx-auto hidden h-(--c-header-h) w-full max-w-[1328px] items-center gap-10 px-6 md:flex">
        <Brand size="md" />
        <nav className="flex flex-1 gap-7 text-[15px]">
          {items.slice(0, 3).map((i) =>
            i.current ? (
              <span key={i.href} aria-current="page" className="py-[23px] font-semibold text-ink shadow-[inset_0_-2px_0_var(--ink)]">
                {i.label}
              </span>
            ) : (
              <Link key={i.href} href={i.href} className="py-[23px] text-ink-3 transition-colors duration-150 hover:text-ink">
                {i.label}
              </Link>
            ),
          )}
        </nav>
        <LangSwitch />
      </div>
    </header>
  );
}
