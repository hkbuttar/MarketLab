export interface FactorSpec {
  name: string;
  weight: number;
  higher_is_better: boolean;
}

export interface StrategyDefinition {
  name: string;
  factors: FactorSpec[];
  selection_fraction: number;
  weighting: string;
  maximum_position: number;
  maximum_turnover: number;
  maximum_holdings: number | null;
  minimum_dollar_volume: number;
  cash_buffer: number;
  maximum_sector_weight: number | null;
  rebalance_frequency: string;
  signal_delay_sessions: number;
}

const executable = new Set(["momentum", "low_volatility", "quality_value_momentum"]);

export async function getStrategies(): Promise<{ items: StrategyDefinition[]; connected: boolean }> {
  const api = process.env.MARKETLAB_API_URL ?? "http://127.0.0.1:8000";
  try {
    const response = await fetch(`${api}/api/v1/strategies`, { cache: "no-store" });
    if (!response.ok) return { items: [], connected: false };
    const data = (await response.json()) as { items: StrategyDefinition[] };
    return { items: data.items.filter((item) => executable.has(item.name)), connected: true };
  } catch {
    return { items: [], connected: false };
  }
}
