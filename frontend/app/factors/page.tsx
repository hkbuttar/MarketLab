import { Sidebar } from "../../components/sidebar";
import { getFactorLab, label, type DatedValue } from "../../lib/factors";

function LineChart({ values }: { values: DatedValue[] }) {
  if (values.length < 2) return <p className="empty-state">Not enough IC history.</p>;
  const width = 760, height = 220, pad = 18;
  const maximum = Math.max(...values.map((item) => Math.abs(item.value)), 0.01);
  const points = values.map((item, index) => {
    const x = pad + (index / (values.length - 1)) * (width - pad * 2);
    const y = height / 2 - (item.value / maximum) * (height / 2 - pad);
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  }).join(" ");
  return (
    <svg className="ic-chart" viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Information coefficient history">
      <line x1="0" y1={height / 2} x2={width} y2={height / 2} className="zero-line" />
      <polyline points={points} className="ic-line" />
    </svg>
  );
}

function percentage(value: number | null): string {
  return value === null ? "—" : `${(value * 100).toFixed(1)}%`;
}

export default async function FactorLabPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const params = await searchParams;
  const factor = typeof params.factor === "string" ? params.factor : "momentum_12_1";
  const startDate = typeof params.start === "string" ? params.start : "2015-01-01";
  const endDate = typeof params.end === "string" ? params.end : "2026-06-30";
  const result = await getFactorLab(factor, startDate, endDate);
  const data = result.data;

  return (
    <div className="shell">
      <Sidebar active="Factor Lab" connected={result.connected} />
      <main>
        <header className="topbar factor-header">
          <div><p className="eyebrow">Research workspace / Factor Lab</p><h1>Interrogate the signal.</h1><p className="lede">Evidence across time, portfolios, turnover, and unintended exposures.</p></div>
        </header>

        <form className="factor-controls" method="get">
          <label>Factor<select name="factor" defaultValue={data?.factor ?? factor}>{result.factors.map((item) => <option value={item} key={item}>{label(item)}</option>)}</select></label>
          <label>Start date<input type="date" name="start" defaultValue={startDate} /></label>
          <label>End date<input type="date" name="end" defaultValue={endDate} /></label>
          <label>Universe<select disabled><option>Investable US equities</option></select></label>
          <label>Forward horizon<select disabled><option>21 sessions</option></select></label>
          <button type="submit">Run analysis</button>
        </form>

        {result.error && <div className="connection-banner">{result.error}</div>}
        {data && <>
          <section className="factor-metrics">
            <article><span>Mean rank IC</span><strong>{data.mean_ic >= 0 ? "+" : ""}{data.mean_ic.toFixed(3)}</strong><small>{data.observations} monthly observations</small></article>
            <article><span>Positive IC rate</span><strong>{percentage(data.positive_ic_rate)}</strong><small>Months above zero</small></article>
            <article><span>Top-quintile turnover</span><strong>{percentage(data.mean_turnover)}</strong><small>Mean one-way turnover</small></article>
            <article><span>Research window</span><strong>{data.start_date.slice(0, 4)}–{data.end_date.slice(0, 4)}</strong><small>21-session forward return</small></article>
          </section>

          <section className="factor-lab-grid">
            <article className="panel ic-panel"><div className="panel-heading"><div><p className="eyebrow">Persistence</p><h2>IC history</h2></div><span className="panel-note">Monthly Spearman rank IC</span></div><LineChart values={data.ic_history} /></article>
            <article className="panel quantile-panel"><div className="panel-heading"><div><p className="eyebrow">Monotonicity</p><h2>Quantile returns</h2></div></div><div className="vertical-bars">{data.quantile_returns.map((item) => <div key={item.name}><strong>{percentage(item.value)}</strong><i className={item.value >= 0 ? "up" : "down"} style={{ height: `${Math.max(8, Math.abs(item.value) * 1300)}px` }} /><span>{item.name}</span></div>)}</div></article>
            <article className="panel"><div className="panel-heading"><div><p className="eyebrow">Redundancy</p><h2>Factor correlations</h2></div></div><div className="correlation-list">{data.correlations.map((item) => <div key={item.name}><span>{label(item.name)}</span><i><b style={{ width: `${Math.abs(item.value) * 100}%` }} /></i><strong>{item.value.toFixed(2)}</strong></div>)}</div></article>
            <article className="panel sector-panel"><div className="panel-heading"><div><p className="eyebrow">Concentration</p><h2>Top-quintile sectors</h2></div></div><div className="sector-list">{data.sector_exposure.slice(0, 8).map((item) => <div key={item.name}><span>{label(item.name)}</span><strong>{percentage(item.value)}</strong></div>)}</div><p className="method-note">{data.sector_classification_note}</p></article>
          </section>
        </>}
      </main>
    </div>
  );
}
