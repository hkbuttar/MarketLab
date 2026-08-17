import { label } from "./dashboard";

export interface NamedValue { name: string; value: number }
export interface DatedValue { date: string; value: number }

export interface FactorLabResult {
  factor: string;
  universe: string;
  forward_horizon: number;
  start_date: string;
  end_date: string;
  observations: number;
  mean_ic: number;
  positive_ic_rate: number;
  mean_turnover: number | null;
  ic_history: DatedValue[];
  quantile_returns: NamedValue[];
  correlations: NamedValue[];
  sector_exposure: NamedValue[];
  sector_classification_note: string;
}

export async function getFactorLab(
  factor: string,
  startDate: string,
  endDate: string,
): Promise<{ data: FactorLabResult | null; factors: string[]; connected: boolean; error?: string }> {
  const api = process.env.MARKETLAB_API_URL ?? "http://127.0.0.1:8000";
  try {
    const catalogResponse = await fetch(`${api}/api/v1/factors`, { cache: "no-store" });
    if (!catalogResponse.ok) throw new Error("Factor catalog is unavailable");
    const catalog = (await catalogResponse.json()) as { items: string[] };
    const selected = catalog.items.includes(factor) ? factor : catalog.items[0];
    if (!selected) return { data: null, factors: [], connected: true };
    const query = new URLSearchParams({
      start_date: startDate,
      end_date: endDate,
      universe: "investable_us_equities",
      forward_horizon: "21",
    });
    const response = await fetch(`${api}/api/v1/factors/${selected}?${query}`, { cache: "no-store" });
    if (!response.ok) {
      const value = (await response.json()) as { detail?: string };
      return { data: null, factors: catalog.items, connected: true, error: value.detail ?? "No matching research" };
    }
    return { data: (await response.json()) as FactorLabResult, factors: catalog.items, connected: true };
  } catch {
    return { data: null, factors: [], connected: false, error: "Start FastAPI to load factor research." };
  }
}

export { label };
