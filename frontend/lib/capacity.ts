export interface CapacityCurvePoint {
  aum: number;
  maximum_participation: number;
  estimated_cost: number;
  estimated_cost_bps: number;
  feasible: boolean;
}

export interface StrategyCapacity {
  name: string;
  latest: { date: string; maximum_aum: number; binding_symbol: string };
  historical_minimum_aum: number;
  observations: number;
  curve: CapacityCurvePoint[];
}

export interface CapacityReport {
  generated_at: string;
  maximum_adv_participation: number;
  liquidation_days: number;
  strategies: StrategyCapacity[];
}

export async function getCapacity(): Promise<{ data: CapacityReport | null; connected: boolean }> {
  const api = process.env.MARKETLAB_API_URL ?? "http://127.0.0.1:8000";
  try {
    const response = await fetch(`${api}/api/v1/capacity`, { cache: "no-store" });
    if (!response.ok) return { data: null, connected: response.status !== 503 };
    return { data: (await response.json()) as CapacityReport, connected: true };
  } catch {
    return { data: null, connected: false };
  }
}
