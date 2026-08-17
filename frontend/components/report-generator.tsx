"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import type { BacktestListItem } from "../lib/backtests";
import { label } from "../lib/dashboard";

export function ReportGenerator({ backtests }: { backtests: BacktestListItem[] }) {
  const [experiment, setExperiment] = useState(backtests[0]?.experiment_id ?? "");
  const [message, setMessage] = useState("");
  const [working, setWorking] = useState(false);
  const router = useRouter();
  const api = process.env.NEXT_PUBLIC_MARKETLAB_API_URL ?? "http://127.0.0.1:8000";

  async function generate() {
    setWorking(true);
    setMessage("");
    try {
      const response = await fetch(`${api}/api/v1/reports/backtests/${encodeURIComponent(experiment)}`, { method: "POST" });
      if (!response.ok) {
        const body = await response.json();
        throw new Error(body.detail ?? "Report generation failed");
      }
      setMessage("Markdown and HTML reports generated.");
      router.refresh();
    } catch (reason) {
      setMessage(reason instanceof Error ? reason.message : "Report generation failed");
    } finally {
      setWorking(false);
    }
  }

  return <article className="panel report-generator"><div><p className="eyebrow">Completed experiment</p><h2>Generate research report</h2></div><select value={experiment} onChange={(event) => setExperiment(event.target.value)}>{backtests.map((item) => <option value={item.experiment_id} key={item.experiment_id}>{item.strategy ? label(item.strategy) : item.experiment_id}</option>)}</select><button disabled={!experiment || working} onClick={generate} type="button">{working ? "Generating…" : "Generate"}</button>{message && <span>{message}</span>}</article>;
}
