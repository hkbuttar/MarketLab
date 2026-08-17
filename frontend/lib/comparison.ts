import type { BacktestResult } from "./backtests";

export interface ComparedBacktest extends Omit<BacktestResult, "equity_curve"> {
  configuration: Record<string, unknown>;
}

export interface BacktestComparison {
  experiments: ComparedBacktest[];
  configuration_warnings: string[];
}

export async function getComparison(ids: string[]): Promise<{ data: BacktestComparison | null; connected: boolean; error: string | null }> {
  if (ids.length < 2) return { data: null, connected: true, error: null };
  const api = process.env.MARKETLAB_API_URL ?? "http://127.0.0.1:8000";
  const query = new URLSearchParams();
  ids.forEach((id) => query.append("experiment_id", id));
  try {
    const response = await fetch(`${api}/api/v1/compare/backtests?${query}`, { cache: "no-store" });
    if (!response.ok) {
      const body = await response.json();
      return { data: null, connected: true, error: body.detail ?? "Comparison unavailable" };
    }
    return { data: (await response.json()) as BacktestComparison, connected: true, error: null };
  } catch {
    return { data: null, connected: false, error: "Unable to reach the MarketLab API" };
  }
}
