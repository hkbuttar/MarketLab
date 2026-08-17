import { Sidebar } from "../../components/sidebar";
import { ReportGenerator } from "../../components/report-generator";
import { getBacktests } from "../../lib/backtests";
import { label } from "../../lib/dashboard";
import { getReports, type ReportItem } from "../../lib/reports";

function size(bytes: number): string { return bytes < 1024 ? `${bytes} B` : bytes < 1024 * 1024 ? `${(bytes / 1024).toFixed(1)} KB` : `${(bytes / 1024 / 1024).toFixed(1)} MB`; }

export default async function ReportsPage() {
  const [reports, jobs] = await Promise.all([getReports(), getBacktests()]);
  const completed = jobs.items.filter((item) => item.status === "completed");
  const categories = reports.items.reduce((groups, item) => {
    (groups[item.category] ??= []).push(item);
    return groups;
  }, {} as Record<string, ReportItem[]>);
  return <div className="shell"><Sidebar active="Reports" connected={reports.connected && jobs.connected} /><main>
    <header className="topbar"><div><p className="eyebrow">Research workspace / Reports</p><h1>Evidence, packaged for review.</h1><p className="lede">Reproducible artifacts and structured studies without generated investment advice.</p></div></header>
    {completed.length > 0 && <ReportGenerator backtests={completed} />}
    <div className="report-catalog">{Object.entries(categories).map(([category, items]) => <article className="panel" key={category}><div className="panel-heading"><div><p className="eyebrow">Artifact collection</p><h2>{label(category)}</h2></div><span className="count-pill">{items.length}</span></div><div className="report-browser">{items.map((item) => <a href={`/reports/view?path=${encodeURIComponent(item.path)}`} key={item.path}><span className="file-type">{item.format.toUpperCase()}</span><div><strong>{item.name}</strong><small>{item.path}</small></div><em>{size(item.size_bytes)}</em></a>)}</div></article>)}</div>
    {!reports.items.length && <p className="empty-state">No report artifacts are available.</p>}
  </main></div>;
}
