"use client";

import { ArrowRightIcon, InfoIcon, WarningCircleIcon } from "@phosphor-icons/react";
import { m } from "motion/react";
import { Controller, type UseFormReturn } from "react-hook-form";
import { Button } from "@/components/ui/button";
import { Field, FieldDescription, FieldError, FieldLabel, FieldLegend, FieldSet } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { EXAMPLES, fmt } from "@/lib/i18n";
import { useLang } from "@/lib/lang";
import type { Health, Mode } from "@/lib/types";
import { cn } from "@/lib/utils";

export const UNKNOWN_AUTHOR = "unknown";

export interface CheckFormValues {
  text: string;
  question: string;
  author: string;
  mode: Mode;
}

interface Props {
  form: UseFormReturn<CheckFormValues>;
  health: Health | "down" | null;
  serverError: { code: string; message: string } | null;
  onRun: (v: CheckFormValues) => void;
}

const control = "rounded-well border-input bg-surface text-base text-ink shadow-none placeholder:text-faint focus-visible:ring-ring/25 md:text-base";

export function CheckForm({ form, health, serverError, onRun }: Props) {
  const { t, lang } = useLang();
  const max = health && health !== "down" ? health.max_input_chars : 8000;
  const models = health && health !== "down" ? health.author_models : [];
  const textError = form.formState.errors.text;
  const length = form.watch("text").length;

  return (
    <form
      className="rise flex flex-col gap-7"
      onSubmit={form.handleSubmit(onRun)}
      noValidate
    >
      <h1 className="text-[28px] font-bold tracking-[-0.02em] sm:text-[30px]">{t.check.title}</h1>
      {serverError ? (
        <ErrorNote code={serverError.code} message={serverError.message} />
      ) : (
        <SetupNote health={health} />
      )}

      <div className="grid grid-cols-1 items-start gap-7 lg:grid-cols-[minmax(0,1fr)_380px]">
        <Field data-invalid={!!textError}>
          <FieldLabel htmlFor="answer" className="text-sm font-semibold">
            {t.check.answerLabel}
          </FieldLabel>
          <div
            className={cn(
              "flex flex-col rounded-well border bg-surface transition-[border-color,box-shadow] duration-150 focus-within:border-ring focus-within:ring-3 focus-within:ring-ring/25",
              textError ? "border-bad" : "border-input",
            )}
          >
            <Textarea
              id="answer"
              rows={12}
              maxLength={max}
              aria-invalid={!!textError}
              aria-describedby="answer-help"
              autoComplete="off"
              placeholder={t.hero.placeholder}
              className={cn(
                control,
                "min-h-[260px] resize-y rounded-b-none border-0 bg-transparent px-4 py-3.5 leading-[1.6] [field-sizing:fixed] focus-visible:border-0 focus-visible:ring-0 aria-invalid:ring-0",
              )}
              onKeyDown={(e) => {
                if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) form.handleSubmit(onRun)();
              }}
              {...form.register("text", {
                validate: (v) => v.trim().length >= 20 || t.errors.too_short,
              })}
            />
            <div className="flex items-center justify-between gap-3 border-t border-line-soft px-4 py-2">
              <Button
                type="button"
                variant="link"
                size="text"
                className="text-sm"
                onClick={() => form.setValue("text", EXAMPLES[lang], { shouldValidate: form.formState.isSubmitted })}
              >
                {t.check.example}
              </Button>
              <span className={cn("font-mono text-[13px]", length > max * 0.9 ? "text-sus" : "text-faint")} aria-hidden>
                {length} / {max}
              </span>
            </div>
          </div>
          <FieldDescription id="answer-help" className="text-[13px] text-ink-4">
            {fmt(t.check.answerHelp, { n: max })}
          </FieldDescription>
          <FieldError errors={textError ? [{ message: textError.message }] : undefined} />
        </Field>

        <div className="flex flex-col gap-5">
          <div className="flex flex-col gap-6">
            <Field>
              <FieldLabel htmlFor="question" className="text-sm font-semibold">
                {t.check.questionLabel}
              </FieldLabel>
              <Input id="question" autoComplete="off" className={cn(control, "h-12 px-4")} {...form.register("question")} />
              <FieldDescription className="text-[13px] text-ink-4">{t.check.questionHelp}</FieldDescription>
            </Field>

            <Field>
              <FieldLabel htmlFor="author" className="text-sm font-semibold">
                {t.check.authorLabel}
              </FieldLabel>
              <Controller
                control={form.control}
                name="author"
                render={({ field }) => (
                  <Select value={field.value} onValueChange={field.onChange}>
                    <SelectTrigger id="author" className={cn(control, "h-12 w-full px-4 data-[size=default]:h-12")}>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="rounded-well bg-surface">
                      {models.map((mdl) => (
                        <SelectItem key={mdl.id} value={mdl.id} className="h-10 text-[15px]">
                          {mdl.label}
                        </SelectItem>
                      ))}
                      <SelectItem value={UNKNOWN_AUTHOR} className="h-10 text-[15px]">
                        {t.check.unknownAuthor}
                      </SelectItem>
                    </SelectContent>
                  </Select>
                )}
              />
              <FieldDescription className="text-[13px] text-ink-4">{t.check.authorHelp}</FieldDescription>
            </Field>

            <FieldSet>
              <FieldLegend className="mb-2 text-sm font-semibold" variant="label">{t.check.modeLabel}</FieldLegend>
              <Controller
                control={form.control}
                name="mode"
                render={({ field }) => (
                  <RadioGroup value={field.value} onValueChange={field.onChange} className="gap-2">
                    {(["deep", "quick"] as Mode[]).map((mode) => (
                      <label
                        key={mode}
                        htmlFor={`mode-${mode}`}
                        className={cn(
                          "flex cursor-pointer items-start gap-3 rounded-well border px-4 py-3 transition-colors duration-150",
                          field.value === mode ? "border-ink bg-surface" : "border-line hover:border-line-strong",
                        )}
                      >
                        <RadioGroupItem id={`mode-${mode}`} value={mode} className="mt-1 size-4" />
                        <span className="flex flex-col gap-0.5">
                          <span className="text-[15px] font-semibold">{mode === "deep" ? t.check.deep : t.check.quick}</span>
                          <span className="text-[13px] leading-[1.45] text-ink-4">{mode === "deep" ? t.check.deepHint : t.check.quickHint}</span>
                        </span>
                      </label>
                    ))}
                  </RadioGroup>
                )}
              />
            </FieldSet>
          </div>

          <Button type="submit" size="lg" className="group">
            {t.check.run} <ArrowRightIcon aria-hidden size={18} className="transition-transform duration-200 group-hover:translate-x-1" />
          </Button>
        </div>
      </div>
    </form>
  );
}

export function ErrorNote({ code, message }: { code: string; message: string }) {
  const { t } = useLang();
  const text = t.errors[code] ? fmt(t.errors[code], { msg: message }) : message || t.errors.backend_error;
  return (
    <m.div
      role="alert"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="flex items-start gap-3 rounded-well border border-bad/40 bg-surface px-4 py-3.5 text-[15px] leading-[1.5] text-bad"
    >
      <WarningCircleIcon aria-hidden size={20} className="mt-px shrink-0" />
      <span>{text}</span>
    </m.div>
  );
}

/** Shown before any check when the backend has no LLM key or is not running, so the prototype explains itself. */
function SetupNote({ health }: { health: Health | "down" | null }) {
  const { t } = useLang();
  if (!health || (health !== "down" && health.llm)) return null;
  return (
    <m.div
      role="status"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="flex items-start gap-3 rounded-well border border-line-strong bg-surface px-4 py-3.5 text-[15px] leading-[1.5] text-ink-2"
    >
      <InfoIcon aria-hidden size={20} className="mt-px shrink-0 text-brand" />
      <span>{health === "down" ? t.setup.down : t.setup.noKey}</span>
    </m.div>
  );
}
