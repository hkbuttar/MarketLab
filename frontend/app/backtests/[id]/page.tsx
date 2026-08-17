import { Sidebar } from "../../../components/sidebar";
import { getBacktestResult, type EquityPoint } from "../../../lib/backtests";
import { label } from "../../../lib/dashboard";

function percent(value: number): string { return `${(value * 100).toFixed(1)}%`; }
function money(value: number): string { return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", notation: "compact", maximumFractionDigits: 1 }).format(value); }

function EquityChart({ values }: { values: EquityPoint[] }) {
  if (values.length < 2) return <p className="empty-state">Not enough observations.</p>;
  const width = 900, height = 280, pad = 16;
  const all = values.flatMap((point) => [point.net_nav, point.benchmark_nav]);
  const minimum = Math.min(...all), maximum = Math.max(...all), range = Math.max(maximum - minimum, 1);
  const points = (field: "net_nav" | "benchmark_nav") => values.map((point, index) => `${pad + index / (values.length - 1) * (width - pad * 2)},${height - pad - (point[field] - minimum) / range * (height - pad * 2)}`).join(" ");
  return <svg className="equity-chart" viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Strategy and benchmark equity curve"><polyline className="benchmark-line" points={points("benchmark_nav")} /><polyline className="strategy-line" points={points("net_nav")} /></svg>;
}

export default async function BacktestResultPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const result = await getBacktestResult(id);
  const data = result.data;
  return <div className="shell">
    <Sidebar active="Backtests" connected={result.connected} />
    <main>
      <header className="topbar"><div><p className="eyebrow">Backtests / {id}</p><h1>{data ? label(data.strategy) : "Result unavailable"}</h1><p className="lede">{data ? `${data.start_date} through ${data.end_date}` : result.error}</p></div><a className="primary-action" href="/backtests">All runs</a></header>
      {data && <>
        <section className="result-metrics">
          <article><span>Net CAGR</span><strong>{percent(data.metrics.cagr)}</strong></article><article><span>Sharpe</span><strong>{data.metrics.sharpe.toFixed(2)}</strong></article><article><span>Maximum drawdown</span><strong>{percent(data.metrics.maximum_drawdown)}</strong></article><article><span>Volatility</span><strong>{percent(data.metrics.annualized_volatility)}</strong></article><article><span>Total costs</span><strong>{money(data.metrics.total_costs)}</strong></article>
        </section>
        <article className="panel result-chart"><div className="panel-heading"><div><p className="eyebrow">Performance</p><h2>Net equity curve</h2></div><div className="chart-legend"><span className="strategy-key">Strategy</span><span className="benchmark-key">SPY</span></div></div><EquityChart values={data.equity_curve} /></article>
        <section className="result-detail-grid"><article className="panel"><p className="eyebrow">Return comparison</p><h2>Outcome</h2><dl className="result-dl"><div><dt>Total return</dt><dd>{percent(data.metrics.total_return)}</dd></div><div><dt>SPY return</dt><dd>{percent(data.metrics.benchmark_return)}</dd></div><div><dt>Active return</dt><dd>{percent(data.metrics.total_return - data.metrics.benchmark_return)}</dd></div></dl></article><article className="panel"><p className="eyebrow">Implementation</p><h2>Trading drag</h2><dl className="result-dl"><div><dt>Gross-to-net drag</dt><dd>{percent(data.metrics.cost_drag)}</dd></div><div><dt>Cumulative costs</dt><dd>{money(data.metrics.total_costs)}</dd></div><div><dt>Daily observations</dt><dd>{data.metrics.observations}</dd></div></dl></article></section>
      </>}
    </main>
  </div>;
}
