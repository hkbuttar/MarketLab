"use client";

import { FormEvent, useState } from "react";

import type { StrategyDefinition } from "../lib/strategies";
import { label } from "../lib/dashboard";

interface JobState {
  experiment_id: string;
  status: "queued" | "running" | "completed" | "failed";
  summary?: Record<string, unknown> | null;
  error?: string | null;
}

export function StrategyBuilder({ strategies }: { strategies: StrategyDefinition[] }) {
  const [selected, setSelected] = useState(strategies[0]?.name ?? "");
  const [job, setJob] = useState<JobState | null>(null);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const strategy = strategies.find((item) => item.name === selected);
  const api = process.env.NEXT_PUBLIC_MARKETLAB_API_URL ?? "http://127.0.0.1:8000";

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setError("");
    setJob(null);
    const form = new FormData(event.currentTarget);
    const payload = {
      strategy: form.get("strategy"),
      start_date: form.get("start_date"),
      end_date: form.get("end_date"),
      capital: Number(form.get("capital")),
      rebalance: "monthly",
      weighting: "equal",
      cost_bps: Number(form.get("cost_bps")),
    };
    try {
      const response = await fetch(`${api}/api/v1/backtests`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!response.ok) {
        const body = await response.json();
        throw new Error(body.detail?.[0]?.msg ?? body.detail ?? "Backtest was rejected");
      }
      const accepted = (await response.json()) as JobState;
      setJob(accepted);
      poll(accepted.experiment_id);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to reach the API");
    } finally {
      setSubmitting(false);
    }
  }

  async function poll(experimentId: string) {
    for (let attempt = 0; attempt < 120; attempt += 1) {
      await new Promise((resolve) => setTimeout(resolve, 1000));
      try {
        const response = await fetch(`${api}/api/v1/backtests/${experimentId}`);
        if (!response.ok) return;
        const status = (await response.json()) as JobState;
        setJob(status);
        if (status.status === "completed" || status.status === "failed") return;
      } catch {
        return;
      }
    }
  }

  return (
    <>
      <form className="builder-grid" onSubmit={submit}>
        <article className="panel builder-form">
          <div className="panel-heading"><div><p className="eyebrow">Configuration</p><h2>Backtest definition</h2></div></div>
          <div className="builder-fields">
            <label>Strategy<select name="strategy" value={selected} onChange={(event) => setSelected(event.target.value)}>{strategies.map((item) => <option key={item.name} value={item.name}>{label(item.name)}</option>)}</select></label>
            <div className="field-pair"><label>Start date<input name="start_date" type="date" defaultValue="2015-01-01" required /></label><label>End date<input name="end_date" type="date" defaultValue="2025-12-31" required /></label></div>
            <label>Starting capital<input name="capital" type="number" min="1000" max="1000000000" step="1000" defaultValue="1000000" required /></label>
            <label>Transaction cost assumption<div className="input-suffix"><input name="cost_bps" type="number" min="0" max="100" step="0.5" defaultValue="10" required /><span>bps</span></div></label>
          </div>
          <button className="run-backtest" disabled={submitting || !selected} type="submit">{submitting ? "Submitting…" : "Run backtest"}</button>
          {error && <p className="builder-error">{error}</p>}
        </article>

        <article className="panel builder-spec">
          <div className="panel-heading"><div><p className="eyebrow">Engine-owned settings</p><h2>Portfolio specification</h2></div></div>
          {strategy && <dl>
            <div><dt>Signals</dt><dd>{strategy.factors.map((factor) => label(factor.name)).join(" + ")}</dd></div>
            <div><dt>Selection</dt><dd>Top {(strategy.selection_fraction * 100).toFixed(0)}%</dd></div>
            <div><dt>Weighting</dt><dd>{label(strategy.weighting)}</dd></div>
            <div><dt>Max position</dt><dd>{(strategy.maximum_position * 100).toFixed(0)}%</dd></div>
            <div><dt>Max turnover</dt><dd>{(strategy.maximum_turnover * 100).toFixed(0)}%</dd></div>
            <div><dt>Rebalance</dt><dd>{label(strategy.rebalance_frequency)}</dd></div>
            <div><dt>Signal delay</dt><dd>{strategy.signal_delay_sessions} session</dd></div>
          </dl>}
          <p className="method-note">These settings describe the persisted canonical portfolio targets. Change them in the quantitative strategy configuration, then rebuild targets before running a custom specification.</p>
        </article>
      </form>

      {job && <article className={`panel job-panel ${job.status}`}>
        <div><p className="eyebrow">Experiment {job.experiment_id}</p><h2>{label(job.status)}</h2></div>
        <span>{job.status === "completed" ? "Backtest artifact and summary are ready." : job.error ?? "The research engine is processing this run."}</span>
      </article>}
    </>
  );
}
