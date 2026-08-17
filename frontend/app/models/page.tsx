import { Sidebar } from "../../components/sidebar";
import { label } from "../../lib/dashboard";
import { getModels } from "../../lib/models";

function percent(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}

export default async function ModelsPage() {
  const result = await getModels();
  const models = result.data?.models ?? [];
  const best = models.length ? [...models].sort((a, b) => b.oos_sharpe - a.oos_sharpe)[0] : null;

  return (
    <div className="shell">
      <Sidebar active="ML Lab" connected={result.connected} />
      <main>
        <header className="topbar">
          <div><p className="eyebrow">Research workspace / ML Lab</p><h1>Complexity must earn its place.</h1><p className="lede">Purged walk-forward evidence, implementation drag, and feature stability.</p></div>
          {result.data && <span className="assumption-pill">{result.data.transaction_cost_bps.toFixed(0)} bps costs</span>}
        </header>

        {!result.data ? <div className="connection-banner">ML evaluation artifacts or the API are unavailable.</div> : <>
          <section className="ml-summary">
            <article className="metric-card dark-card"><p>Best OOS model</p><strong>{best ? label(best.name) : "—"}</strong><span>Ranked by net out-of-sample Sharpe</span></article>
            <article className="metric-card"><p>Best OOS Sharpe</p><strong>{best?.oos_sharpe.toFixed(2) ?? "—"}</strong><span>{best?.months ?? 0} monthly test observations</span></article>
            <article className="metric-card"><p>Benchmark CAGR</p><strong>{best ? percent(best.benchmark_cagr) : "—"}</strong><span>SPY over the shared OOS window</span></article>
          </section>

          <div className="model-list">
            {models.map((model) => {
              const featureMaximum = Math.max(...model.top_features.map((feature) => Math.abs(feature.permutation_importance)), 0.001);
              return <article className="panel model-card" key={model.name}>
                <div className="panel-heading"><div><p className="eyebrow">Purged walk-forward</p><h2>{label(model.name)}</h2></div><span className="count-pill">{model.months} months</span></div>
                <div className="model-metrics">
                  <div><span>Net CAGR</span><strong>{percent(model.net_cagr)}</strong></div>
                  <div><span>OOS Sharpe</span><strong>{model.oos_sharpe.toFixed(2)}</strong></div>
                  <div><span>Rank IC</span><strong>{model.mean_rank_ic.toFixed(3)}</strong></div>
                  <div><span>Positive IC</span><strong>{percent(model.positive_ic_fraction)}</strong></div>
                  <div><span>Max drawdown</span><strong>{percent(model.maximum_drawdown)}</strong></div>
                  <div><span>Turnover</span><strong>{percent(model.average_turnover)}</strong></div>
                </div>
                <div className="model-detail-grid">
                  <div><p className="eyebrow">Explainability</p><h3>Stable feature leaders</h3><div className="importance-list">{model.top_features.map((feature) => <div key={feature.name}><span>{label(feature.name)}</span><i><b style={{ width: `${Math.max(0, feature.permutation_importance) / featureMaximum * 100}%` }} /></i><strong>{feature.permutation_importance.toFixed(3)}</strong></div>)}</div></div>
                  <div className="validation-note"><p className="eyebrow">Validation discipline</p><h3>Leakage controls</h3><dl><div><dt>Purging effect on IC</dt><dd>{model.purging_delta_ic === null ? "—" : `${model.purging_delta_ic >= 0 ? "+" : ""}${model.purging_delta_ic.toFixed(4)}`}</dd></div><div><dt>Annual cost drag</dt><dd>{percent(model.annualized_cost_drag)}</dd></div><div><dt>Active CAGR</dt><dd>{percent(model.net_cagr - model.benchmark_cagr)}</dd></div></dl></div>
                </div>
              </article>;
            })}
          </div>
          <p className="method-note ml-method">{result.data.method}. Explainability: {result.data.explainability_method}.</p>
        </>}
      </main>
    </div>
  );
}
