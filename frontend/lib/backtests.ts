export interface BacktestListItem {
  experiment_id: string;
  status: "queued" | "running" | "completed" | "failed";
  strategy: string | null;
  created_at: string | null;
}

export interface EquityPoint {
  date: string;
  net_nav: number;
  gross_nav: number;
  benchmark_nav: number;
}

export interface BacktestResult {
  experiment_id: string;
  strategy: string;
  start_date: string;
  end_date: string;
  metrics: {
    total_return: number;
    benchmark_return: number;
    cagr: number;
    annualized_volatility: number;
    sharpe: number;
    maximum_drawdown: number;
    total_costs: number;
    cost_drag: number;
    observations: number;
  };
  equity_curve: EquityPoint[];
}

const api = process.env.MARKETLAB_API_URL ?? "http://127.0.0.1:8000";

export async function getBacktests(): Promise<{ items: BacktestListItem[]; connected: boolean }> {
  try {
    const response = await fetch(`${api}/api/v1/backtests`, { cache: "no-store" });
    if (!response.ok) return { items: [], connected: false };
    const data = (await response.json()) as { items: BacktestListItem[] };
    return { items: data.items, connected: true };
  } catch {
    return { items: [], connected: false };
  }
}

export async function getBacktestResult(id: string): Promise<{ data: BacktestResult | null; connected: boolean; error: string | null }> {
  try {
    const response = await fetch(`${api}/api/v1/backtests/${encodeURIComponent(id)}/results`, { cache: "no-store" });
    if (!response.ok) {
      const body = await response.json();
      return { data: null, connected: response.status !== 503, error: body.detail ?? "Result unavailable" };
    }
    return { data: (await response.json()) as BacktestResult, connected: true, error: null };
  } catch {
    return { data: null, connected: false, error: "Unable to reach the MarketLab API" };
  }
}
