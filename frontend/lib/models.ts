export interface MLFeatureImportance {
  name: string;
  permutation_importance: number;
  mean_absolute_shap: number;
  top_three_year_fraction: number;
}

export interface MLModelDiagnostics {
  name: string;
  months: number;
  mean_rank_ic: number;
  positive_ic_fraction: number;
  net_cagr: number;
  benchmark_cagr: number;
  oos_sharpe: number;
  maximum_drawdown: number;
  average_turnover: number;
  annualized_cost_drag: number;
  purging_delta_ic: number | null;
  top_features: MLFeatureImportance[];
}

export interface MLLabData {
  method: string;
  explainability_method: string;
  transaction_cost_bps: number;
  models: MLModelDiagnostics[];
}

export async function getModels(): Promise<{ data: MLLabData | null; connected: boolean }> {
  const api = process.env.MARKETLAB_API_URL ?? "http://127.0.0.1:8000";
  try {
    const response = await fetch(`${api}/api/v1/models`, { cache: "no-store" });
    if (!response.ok) return { data: null, connected: response.status !== 503 };
    return { data: (await response.json()) as MLLabData, connected: true };
  } catch {
    return { data: null, connected: false };
  }
}
