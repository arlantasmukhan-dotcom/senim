"use client";

import { CheckCircleIcon, CopyIcon } from "@phosphor-icons/react";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export function CopyButton({ text, label, className }: { text: string; label: string; className?: string }) {
  const [done, setDone] = useState(false);
  return (
    <Button
      type="button"
      variant="icon"
      size="icon"
      aria-label={label}
      title={label}
      className={cn(className)}
      onClick={() => {
        navigator.clipboard?.writeText(text).then(() => {
          setDone(true);
          setTimeout(() => setDone(false), 1400);
        });
      }}
    >
      {done ? <CheckCircleIcon aria-hidden size={18} className="text-ok" /> : <CopyIcon aria-hidden size={18} />}
    </Button>
  );
}
