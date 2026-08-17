import { getDashboard, label } from "../lib/dashboard";
import { Sidebar } from "../components/sidebar";

function formatDate(value: string): string {
  if (!value) return "Unknown date";
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(new Date(value));
}

function Empty({ children }: { children: string }) {
  return <p className="empty-state">{children}</p>;
}

export default async function DashboardPage() {
  const { data, connected } = await getDashboard();
  const maxFactor = Math.max(...data.factor_research.map((factor) => Math.abs(factor.value)), 0.01);

  return (
    <div className="shell">
      <Sidebar active="Overview" connected={connected} />

      <main>
        <header className="topbar">
          <div>
            <p className="eyebrow">Research workspace / Overview</p>
            <h1>Good morning, Harleen.</h1>
            <p className="lede">A disciplined view of what the evidence says—not what the market is shouting.</p>
          </div>
          <a className="primary-action" href="http://127.0.0.1:8000/docs">
            Open API <span>↗</span>
          </a>
        </header>

        {!connected && (
          <div className="connection-banner">
            Start FastAPI on port 8000 to load current research artifacts.
          </div>
        )}

        <section className="metric-grid" aria-label="Research highlights">
          <article className="metric-card dark-card">
            <p>Best OOS model</p>
            <strong>{data.best_oos_model ? label(data.best_oos_model) : "—"}</strong>
            <span>Purged walk-forward evaluation</span>
          </article>
          <article className="metric-card">
            <p>Best OOS Sharpe</p>
            <strong>{data.best_oos_sharpe?.toFixed(2) ?? "—"}</strong>
            <span>Risk-free adjusted · monthly</span>
          </article>
          <article className="metric-card">
            <p>Average robustness</p>
            <strong>{data.average_robustness_score?.toFixed(1) ?? "—"}<small>/100</small></strong>
            <span>Across canonical strategies</span>
          </article>
          <article className="metric-card accent-card">
            <p>Research scope</p>
            <strong>Daily US</strong>
            <span>Equities · long-only · EOD</span>
          </article>
        </section>

        <section className="dashboard-grid">
          <article className="panel factor-panel">
            <div className="panel-heading">
              <div>
                <p className="eyebrow">Signal diagnostics</p>
                <h2>Factor research</h2>
              </div>
              <span className="panel-note">Mean rank IC</span>
            </div>
            {data.factor_research.length ? (
              <div className="factor-list">
                {data.factor_research.map((factor) => (
                  <div className="factor-row" key={factor.name}>
                    <span>{label(factor.name)}</span>
                    <div className="factor-track">
                      <i
                        className={factor.value >= 0 ? "positive" : "negative"}
                        style={{ width: `${Math.abs(factor.value / maxFactor) * 100}%` }}
                      />
                    </div>
                    <strong>{factor.value >= 0 ? "+" : ""}{factor.value.toFixed(3)}</strong>
                  </div>
                ))}
              </div>
            ) : <Empty>No factor research has been generated yet.</Empty>}
          </article>

          <article className="panel experiment-panel">
            <div className="panel-heading">
              <div>
                <p className="eyebrow">Reproducibility</p>
                <h2>Recent experiments</h2>
              </div>
              <span className="count-pill">{data.recent_experiments.length}</span>
            </div>
            {data.recent_experiments.length ? (
              <div className="experiment-list">
                {data.recent_experiments.map((experiment) => (
                  <div className="experiment-row" key={experiment.experiment_id}>
                    <span className="run-icon">✓</span>
                    <div>
                      <strong>{label(experiment.name)}</strong>
                      <small>{formatDate(experiment.created_at)} · {experiment.experiment_id.slice(-10)}</small>
                    </div>
                    <span className="success-label">{experiment.status}</span>
                  </div>
                ))}
              </div>
            ) : <Empty>No registered experiments found.</Empty>}
          </article>

          <article className="panel report-panel">
            <div className="panel-heading">
              <div>
                <p className="eyebrow">Artifacts</p>
                <h2>Recent reports</h2>
              </div>
            </div>
            {data.recent_reports.length ? (
              <div className="report-list">
                {data.recent_reports.map((report) => (
                  <div className="report-row" key={report.path}>
                    <span className="file-type">{report.path.split(".").at(-1)?.toUpperCase()}</span>
                    <div>
                      <strong>{report.name}</strong>
                      <small>{report.path}</small>
                    </div>
                    <time>{formatDate(report.updated_at)}</time>
                  </div>
                ))}
              </div>
            ) : <Empty>No generated reports found.</Empty>}
          </article>

          <article className="panel workflow-panel">
            <p className="eyebrow">System discipline</p>
            <h2>Research pipeline</h2>
            <ol>
              <li className="done"><span>01</span> Point-in-time data</li>
              <li className="done"><span>02</span> Factor diagnostics</li>
              <li className="done"><span>03</span> Portfolio simulation</li>
              <li className="done"><span>04</span> Robustness validation</li>
              <li className="current"><span>05</span> Product layer</li>
            </ol>
          </article>
        </section>
      </main>
    </div>
  );
}
