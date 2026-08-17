export interface DashboardMetric {
  name: string;
  value: number;
}

export interface RecentExperiment {
  experiment_id: string;
  name: string;
  created_at: string;
  status: string;
}

export interface RecentReport {
  name: string;
  path: string;
  updated_at: string;
}

export interface DashboardSummary {
  best_oos_model: string | null;
  best_oos_sharpe: number | null;
  average_robustness_score: number | null;
  factor_research: DashboardMetric[];
  recent_experiments: RecentExperiment[];
  recent_reports: RecentReport[];
}

const emptyDashboard: DashboardSummary = {
  best_oos_model: null,
  best_oos_sharpe: null,
  average_robustness_score: null,
  factor_research: [],
  recent_experiments: [],
  recent_reports: [],
};

export async function getDashboard(): Promise<{
  data: DashboardSummary;
  connected: boolean;
}> {
  const apiUrl = process.env.MARKETLAB_API_URL ?? "http://127.0.0.1:8000";
  try {
    const response = await fetch(`${apiUrl}/api/v1/dashboard`, {
      cache: "no-store",
    });
    if (!response.ok) {
      return { data: emptyDashboard, connected: false };
    }
    return { data: (await response.json()) as DashboardSummary, connected: true };
  } catch {
    return { data: emptyDashboard, connected: false };
  }
}

export function label(value: string): string {
  return value.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}
