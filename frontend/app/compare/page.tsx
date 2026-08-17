import { Sidebar } from "../../components/sidebar";
import { getBacktests } from "../../lib/backtests";
import { getComparison } from "../../lib/comparison";
import { label } from "../../lib/dashboard";

function percent(value: number): string { return `${(value * 100).toFixed(1)}%`; }

export default async function ComparePage({ searchParams }: { searchParams: Promise<Record<string, string | string[] | undefined>> }) {
  const params = await searchParams;
  const selected = Array.isArray(params.experiment_id) ? params.experiment_id.slice(0, 5) : typeof params.experiment_id === "string" ? [params.experiment_id] : [];
  const [catalog, comparison] = await Promise.all([getBacktests(), getComparison(selected)]);
  const completed = catalog.items.filter((item) => item.status === "completed");
  const connected = catalog.connected && comparison.connected;

  return <div className="shell">
    <Sidebar active="Compare" connected={connected} />
    <main>
      <header className="topbar"><div><p className="eyebrow">Research workspace / Compare</p><h1>Put every result on equal footing.</h1><p className="lede">Select two to five completed experiments and inspect assumptions before outcomes.</p></div></header>
      <form className="panel comparison-selector" method="get">
        <div className="panel-heading"><div><p className="eyebrow">Selection</p><h2>Completed backtests</h2></div><span className="count-pill">{selected.length}/5</span></div>
        {completed.length ? <div className="comparison-options">{completed.map((item) => <label key={item.experiment_id}><input type="checkbox" name="experiment_id" value={item.experiment_id} defaultChecked={selected.includes(item.experiment_id)} /><span><strong>{item.strategy ? label(item.strategy) : "Unknown strategy"}</strong><small>{item.experiment_id}</small></span></label>)}</div> : <p className="empty-state">At least two completed backtests are required.</p>}
        <button className="run-backtest" type="submit">Compare selected runs</button>
      </form>
      {comparison.error && <div className="connection-banner">{comparison.error}</div>}
      {comparison.data && <>
        {comparison.data.configuration_warnings.length > 0 && <div className="comparison-warnings"><strong>Configuration differences</strong>{comparison.data.configuration_warnings.map((warning) => <span key={warning}>{warning}</span>)}</div>}
        <article className="panel comparison-table-wrap"><div className="panel-heading"><div><p className="eyebrow">Side-by-side evidence</p><h2>Performance and risk</h2></div></div><div className="comparison-table" style={{ gridTemplateColumns: `145px repeat(${comparison.data.experiments.length}, minmax(125px, 1fr))` }}><div className="comparison-cell heading">Metric</div>{comparison.data.experiments.map((item) => <div className="comparison-cell heading" key={item.experiment_id}><strong>{label(item.strategy)}</strong><small>{item.experiment_id.slice(0, 10)}</small></div>)}
          {[
            ["Net CAGR", (item: typeof comparison.data.experiments[number]) => percent(item.metrics.cagr)],
            ["Total return", (item: typeof comparison.data.experiments[number]) => percent(item.metrics.total_return)],
            ["SPY return", (item: typeof comparison.data.experiments[number]) => percent(item.metrics.benchmark_return)],
            ["Sharpe", (item: typeof comparison.data.experiments[number]) => item.metrics.sharpe.toFixed(2)],
            ["Volatility", (item: typeof comparison.data.experiments[number]) => percent(item.metrics.annualized_volatility)],
            ["Max drawdown", (item: typeof comparison.data.experiments[number]) => percent(item.metrics.maximum_drawdown)],
            ["Cost drag", (item: typeof comparison.data.experiments[number]) => percent(item.metrics.cost_drag)],
          ].flatMap(([name, formatter]) => [<div className="comparison-cell metric-name" key={`${name}-name`}>{name as string}</div>, ...comparison.data!.experiments.map((item) => <div className="comparison-cell metric-value" key={`${name}-${item.experiment_id}`}>{(formatter as (value: typeof item) => string)(item)}</div>)])}
        </div></article>
      </>}
    </main>
  </div>;
}
