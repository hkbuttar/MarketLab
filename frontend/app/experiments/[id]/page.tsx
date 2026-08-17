import { Sidebar } from "../../../components/sidebar";
import { label } from "../../../lib/dashboard";
import { getExperiment, type ExperimentArtifact } from "../../../lib/experiments";

function size(bytes: number): string { return bytes < 1024 * 1024 ? `${(bytes / 1024).toFixed(1)} KB` : `${(bytes / 1024 / 1024).toFixed(1)} MB`; }

function Artifacts({ title, items }: { title: string; items: ExperimentArtifact[] }) {
  return <article className="panel"><div className="panel-heading"><div><p className="eyebrow">Fingerprinted artifacts</p><h2>{title}</h2></div><span className="count-pill">{items.length}</span></div><div className="artifact-list">{items.map((item) => <div key={item.path}><span className="file-type">{item.path.split(".").at(-1)?.toUpperCase()}</span><div><strong>{item.path}</strong><small>SHA-256 · {item.sha256}</small></div><em>{size(item.size_bytes)}</em></div>)}</div></article>;
}

export default async function ExperimentPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const result = await getExperiment(id);
  const data = result.data;
  return <div className="shell"><Sidebar active="Experiments" connected={result.connected} /><main>
    <header className="topbar"><div><p className="eyebrow">Experiments / {id}</p><h1>{data ? label(data.name) : "Manifest unavailable"}</h1><p className="lede">{data?.created_at ?? "The requested experiment could not be loaded."}</p></div><a className="primary-action" href="/experiments">All experiments</a></header>
    {data && <>
      <section className="manifest-summary"><article><span>Schema</span><strong>v{data.schema_version}</strong></article><article><span>Git revision</span><strong>{data.git_revision?.slice(0, 10) ?? "—"}</strong></article><article><span>Source state</span><strong>{data.git_dirty ? "Dirty" : "Clean"}</strong></article><article><span>Artifacts</span><strong>{data.inputs.length + data.outputs.length}</strong></article></section>
      <article className="panel reproducibility-panel"><p className="eyebrow">Recorded command</p><code>{data.command}</code><p>Verify locally with <code>python scripts/reproduce_experiment.py {data.run_id} --verify-only</code></p></article>
      <section className="manifest-grid"><article className="panel"><p className="eyebrow">Configuration</p><h2>Parameters</h2><pre>{JSON.stringify(data.parameters, null, 2)}</pre></article><article className="panel"><p className="eyebrow">Recorded evidence</p><h2>Metrics</h2><pre>{JSON.stringify(data.metrics, null, 2)}</pre></article><Artifacts title="Inputs" items={data.inputs} /><Artifacts title="Outputs" items={data.outputs} /></section>
    </>}
  </main></div>;
}
