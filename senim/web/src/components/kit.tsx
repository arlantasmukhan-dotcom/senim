import type { Icon } from "@phosphor-icons/react";
import {
  BooksIcon,
  ChatTextIcon,
  CheckCircleIcon,
  CircleNotchIcon,
  EyeIcon,
  GhostIcon,
  LinkSimpleIcon,
  QuestionIcon,
  UsersThreeIcon,
  WarningCircleIcon,
  XCircleIcon,
} from "@phosphor-icons/react/dist/ssr";
import { cn } from "@/lib/utils";
import type { Tone } from "@/lib/i18n";
import type { Label } from "@/lib/types";

/** Page containers. Landing: 1200px content (mockup 1440 - 2×120). App: 1280px (1440 - 2×80). */
export const wrap = "mx-auto w-full max-w-[1248px] px-4 sm:px-6";
export const wrapApp = "mx-auto w-full max-w-[1328px] px-4 sm:px-6";

/** Mockup card: 16px radius, hairline border, surface fill. */
export const card = "rounded-card border border-line bg-surface";

export const SENSOR_ICON: Record<string, Icon> = {
  alibi: BooksIcon,
  reinterrogation: UsersThreeIcon,
  phantom: GhostIcon,
  fame: EyeIcon,
  citations: LinkSimpleIcon,
};

export const LABEL_META: Record<Label, { Icon: Icon; cls: string }> = {
  contradicted: { Icon: XCircleIcon, cls: "text-bad" },
  suspicious: { Icon: WarningCircleIcon, cls: "text-sus" },
  unconfirmed: { Icon: QuestionIcon, cls: "text-ink-3" },
  confirmed: { Icon: CheckCircleIcon, cls: "text-ok" },
  not_checkable: { Icon: ChatTextIcon, cls: "text-faint" },
  pending: { Icon: CircleNotchIcon, cls: "text-faint" },
};

export function VerdictTag({ label, text, className }: { label: Label; text: string; className?: string }) {
  const { Icon, cls } = LABEL_META[label];
  return (
    <span className={cn("inline-flex items-center gap-2 text-[15px] font-semibold", cls, className)}>
      <Icon aria-hidden size={20} className={label === "pending" ? "motion-safe:animate-spin" : undefined} />
      {text}
    </span>
  );
}

export function Spinner({ size = 16, className }: { size?: number; className?: string }) {
  return <CircleNotchIcon aria-hidden size={size} className={cn("motion-safe:animate-spin", className)} />;
}

const TONE_MARK: Partial<Record<Tone, { Icon: Icon; cls: string }>> = {
  against: { Icon: XCircleIcon, cls: "text-bad" },
  for: { Icon: CheckCircleIcon, cls: "text-ok" },
  risk: { Icon: WarningCircleIcon, cls: "text-sus" },
  mixed: { Icon: WarningCircleIcon, cls: "text-sus" },
};

/** A sensor's verdict as a shape + color glyph instead of a word; the label stays for screen readers. */
export function ToneMark({ tone, label, size = 18 }: { tone: Tone; label: string; size?: number }) {
  if (tone === "pending") {
    return (
      <span role="img" aria-label={label} title={label} className="inline-flex text-faint">
        <Spinner size={size - 2} />
      </span>
    );
  }
  const mark = TONE_MARK[tone];
  if (!mark) return <span className="sr-only">{label}</span>;
  const { Icon: M, cls } = mark;
  return (
    <span role="img" aria-label={label} title={label} className={cn("inline-flex", cls)}>
      <M aria-hidden size={size} weight="fill" />
    </span>
  );
}
