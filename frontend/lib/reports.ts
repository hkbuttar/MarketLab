export interface ReportItem {
  name: string;
  path: string;
  category: string;
  format: string;
  size_bytes: number;
  updated_at: string;
}

export interface ReportContent {
  report: ReportItem;
  content: string;
}

const api = process.env.MARKETLAB_API_URL ?? "http://127.0.0.1:8000";

export async function getReports(): Promise<{ items: ReportItem[]; connected: boolean }> {
  try {
    const response = await fetch(`${api}/api/v1/reports`, { cache: "no-store" });
    if (!response.ok) return { items: [], connected: false };
    const data = (await response.json()) as { items: ReportItem[] };
    return { items: data.items, connected: true };
  } catch {
    return { items: [], connected: false };
  }
}

export async function getReportContent(path: string): Promise<{ data: ReportContent | null; connected: boolean; error: string | null }> {
  try {
    const response = await fetch(`${api}/api/v1/reports/content?path=${encodeURIComponent(path)}`, { cache: "no-store" });
    if (!response.ok) {
      const body = await response.json();
      return { data: null, connected: true, error: body.detail ?? "Preview unavailable" };
    }
    return { data: (await response.json()) as ReportContent, connected: true, error: null };
  } catch {
    return { data: null, connected: false, error: "Unable to reach the MarketLab API" };
  }
}
