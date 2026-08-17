import { Sidebar } from "../../../components/sidebar";
import { getReportContent } from "../../../lib/reports";

export default async function ReportViewPage({ searchParams }: { searchParams: Promise<Record<string, string | string[] | undefined>> }) {
  const params = await searchParams;
  const path = typeof params.path === "string" ? params.path : "";
  const result = await getReportContent(path);
  return <div className="shell"><Sidebar active="Reports" connected={result.connected} /><main>
    <header className="topbar"><div><p className="eyebrow">Reports / Preview</p><h1>{result.data?.report.name ?? "Preview unavailable"}</h1><p className="lede">{result.data?.report.path ?? result.error}</p></div><a className="primary-action" href="/reports">All reports</a></header>
    {result.data && <article className="panel report-preview"><div className="panel-heading"><span className="file-type">{result.data.report.format.toUpperCase()}</span><span className="panel-note">Read-only artifact preview</span></div><pre>{result.data.content}</pre></article>}
  </main></div>;
}
