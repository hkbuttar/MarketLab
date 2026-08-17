import { Sidebar } from "../../components/sidebar";
import { label } from "../../lib/dashboard";
import { getExperiments } from "../../lib/experiments";

function date(value: string): string { return new Intl.DateTimeFormat("en-US", { dateStyle: "medium", timeStyle: "short" }).format(new Date(value)); }

export default async function ExperimentsPage() {
  const result = await getExperiments();
  return <div className="shell"><Sidebar active="Experiments" connected={result.connected} /><main>
    <header className="topbar"><div><p className="eyebrow">Research workspace / Experiments</p><h1>Every result has a provenance trail.</h1><p className="lede">Immutable manifests connect code, parameters, data fingerprints, and outputs.</p></div></header>
    {!result.connected && <div className="connection-banner">Start FastAPI on port 8000 to load experiment manifests.</div>}
    <article className="panel experiment-catalog"><div className="panel-heading"><div><p className="eyebrow">Reproducibility registry</p><h2>Recorded experiments</h2></div><span className="count-pill">{result.items.length}</span></div>
      {result.items.length ? <div className="manifest-list">{result.items.map((item) => <a href={`/experiments/${item.run_id}`} key={item.run_id}><span className="run-icon">✓</span><div><strong>{label(item.name)}</strong><small>{item.run_id}</small></div><time>{date(item.created_at)}</time><span className={item.git_dirty ? "git-state dirty" : "git-state clean"}>{item.git_dirty ? "Dirty tree" : "Clean tree"}</span><em>{item.input_count} in · {item.output_count} out</em></a>)}</div> : <p className="empty-state">No immutable experiment manifests found.</p>}
    </article>
  </main></div>;
}
