import { Sidebar } from "../../components/sidebar";
import { getBacktests } from "../../lib/backtests";
import { label } from "../../lib/dashboard";

function date(value: string | null): string {
  return value ? new Intl.DateTimeFormat("en-US", { dateStyle: "medium" }).format(new Date(value)) : "Legacy run";
}

export default async function BacktestsPage() {
  const result = await getBacktests();
  return <div className="shell">
    <Sidebar active="Backtests" connected={result.connected} />
    <main>
      <header className="topbar"><div><p className="eyebrow">Research workspace / Backtests</p><h1>Experiment results</h1><p className="lede">Persisted runs, consistent analytics, and traceable artifacts.</p></div><a className="primary-action" href="/strategies">New backtest <span>→</span></a></header>
      {!result.connected && <div className="connection-banner">Start FastAPI on port 8000 to load experiments.</div>}
      <article className="panel backtest-catalog">
        <div className="panel-heading"><div><p className="eyebrow">Experiment registry</p><h2>Backtest runs</h2></div><span className="count-pill">{result.items.length}</span></div>
        {result.items.length ? <div className="backtest-list">{result.items.map((item) => <a className="backtest-row" href={`/backtests/${item.experiment_id}`} key={item.experiment_id}><span className={`run-icon ${item.status}`}>{item.status === "completed" ? "✓" : "·"}</span><div><strong>{item.strategy ? label(item.strategy) : "Unknown strategy"}</strong><small>{item.experiment_id}</small></div><time>{date(item.created_at)}</time><b className={`status-label ${item.status}`}>{item.status}</b></a>)}</div> : <p className="empty-state">No backtests have been submitted yet.</p>}
      </article>
    </main>
  </div>;
}
