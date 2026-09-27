"use client";

import { useCallback, useEffect, useReducer, useRef } from "react";
import type {
  Citation,
  CitationResult,
  Claim,
  DoneInfo,
  Lang,
  Mode,
  SensorMap,
  SensorName,
  Verdict,
} from "./types";

export interface CheckRequest {
  text: string;
  question: string | null;
  author_model: string | null;
  ui_lang: Lang;
  mode: Mode;
}

export interface CheckState {
  running: boolean;
  stage: "idle" | "extract" | "sensors" | "done";
  request: CheckRequest | null;
  text: string;
  claims: Claim[];
  citations: Citation[];
  cits: CitationResult[] | null;
  sensors: Record<string, SensorMap>;
  verdicts: Record<string, Verdict>;
  sensorTotal: number;
  sensorDone: number;
  truncated: boolean;
  error: { code: string; message: string } | null;
  done: DoneInfo | null;
}

const initial: CheckState = {
  running: false,
  stage: "idle",
  request: null,
  text: "",
  claims: [],
  citations: [],
  cits: null,
  sensors: {},
  verdicts: {},
  sensorTotal: 0,
  sensorDone: 0,
  truncated: false,
  error: null,
  done: null,
};

type Action =
  | { type: "start"; request: CheckRequest }
  | { type: "event"; event: string; data: unknown }
  | { type: "fail"; code: string; message?: string }
  | { type: "end" }
  | { type: "reset" };

function reducer(s: CheckState, a: Action): CheckState {
  switch (a.type) {
    case "start":
      return { ...initial, running: true, stage: "extract", request: a.request, text: a.request.text };
    case "fail":
      return { ...s, error: { code: a.code, message: a.message ?? "" } };
    case "end":
      return { ...s, running: false, stage: "done" };
    case "reset":
      return initial;
    case "event":
      return onEvent(s, a.event, a.data);
  }
}

function onEvent(s: CheckState, event: string, data: unknown): CheckState {
  switch (event) {
    case "status": {
      const d = data as { stage: string; truncated: boolean };
      return { ...s, truncated: d.truncated };
    }
    case "claims": {
      const d = data as { text: string; claims: Claim[]; citations: Citation[] };
      const checkable = d.claims.filter((c) => c.checkable).length;
      const perClaim = s.request?.mode === "deep" ? 4 : 2;
      return {
        ...s,
        stage: "sensors",
        text: d.text,
        claims: d.claims,
        citations: d.citations,
        sensorTotal: checkable * perClaim + 1,
      };
    }
    case "sensor": {
      const d = data as { claim_id: string; sensor: SensorName; result: unknown };
      return {
        ...s,
        sensors: { ...s.sensors, [d.claim_id]: { ...s.sensors[d.claim_id], [d.sensor]: d.result } },
        sensorDone: s.sensorDone + 1,
      };
    }
    case "citations":
      return { ...s, cits: data as CitationResult[], sensorDone: s.sensorDone + 1 };
    case "verdict": {
      const v = data as Verdict;
      return { ...s, verdicts: { ...s.verdicts, [v.claim_id]: v } };
    }
    case "error": {
      const d = data as { code: string; message: string };
      return { ...s, error: { code: d.code, message: d.message } };
    }
    case "done":
      return { ...s, done: data as DoneInfo };
  }
  return s;
}

/** Runs one check against /api/check and folds the SSE stream into state. */
export function useCheck() {
  const [state, dispatch] = useReducer(reducer, initial);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => () => abortRef.current?.abort(), []);

  const run = useCallback(async (request: CheckRequest) => {
    abortRef.current?.abort();
    const ctrl = new AbortController();
    abortRef.current = ctrl;
    dispatch({ type: "start", request });
    try {
      const res = await fetch("/api/check", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(request),
        signal: ctrl.signal,
      });
      if (!res.ok || !res.body) {
        const body = await res.json().catch(() => ({}));
        dispatch({ type: "fail", code: body.code ?? "backend_error" });
        return;
      }
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buf = "";
      for (;;) {
        const { value, done } = await reader.read();
        if (done) break;
        buf += decoder.decode(value, { stream: true }).replace(/\r\n/g, "\n");
        let i: number;
        while ((i = buf.indexOf("\n\n")) >= 0) {
          const block = buf.slice(0, i);
          buf = buf.slice(i + 2);
          const event = /^event: (.*)$/m.exec(block)?.[1];
          const data = /^data: (.*)$/m.exec(block)?.[1];
          if (event && data) dispatch({ type: "event", event, data: JSON.parse(data) });
        }
      }
    } catch (e) {
      if (!ctrl.signal.aborted) dispatch({ type: "fail", code: "network", message: String(e) });
    } finally {
      if (abortRef.current === ctrl) dispatch({ type: "end" });
    }
  }, []);

  const stop = useCallback(() => {
    abortRef.current?.abort();
    dispatch({ type: "end" });
  }, []);

  const reset = useCallback(() => {
    abortRef.current?.abort();
    abortRef.current = null;
    dispatch({ type: "reset" });
  }, []);

  return { state, run, stop, reset };
}
