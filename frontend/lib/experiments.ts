export interface ExperimentArtifact {
  path: string;
  size_bytes: number;
  sha256: string;
}

export interface ExperimentListItem {
  run_id: string;
  name: string;
  created_at: string;
  git_revision: string | null;
  git_dirty: boolean | null;
  input_count: number;
  output_count: number;
}

export interface ExperimentDetail {
  schema_version: number;
  run_id: string;
  name: string;
  created_at: string;
  command: string;
  git_revision: string | null;
  git_dirty: boolean | null;
  parameters: Record<string, unknown>;
  metrics: Record<string, unknown>;
  inputs: ExperimentArtifact[];
  outputs: ExperimentArtifact[];
}

const api = process.env.MARKETLAB_API_URL ?? "http://127.0.0.1:8000";

export async function getExperiments(): Promise<{ items: ExperimentListItem[]; connected: boolean }> {
  try {
    const response = await fetch(`${api}/api/v1/experiments`, { cache: "no-store" });
    if (!response.ok) return { items: [], connected: false };
    const data = (await response.json()) as { items: ExperimentListItem[] };
    return { items: data.items, connected: true };
  } catch {
    return { items: [], connected: false };
  }
}

export async function getExperiment(runId: string): Promise<{ data: ExperimentDetail | null; connected: boolean }> {
  try {
    const response = await fetch(`${api}/api/v1/experiments/${encodeURIComponent(runId)}`, { cache: "no-store" });
    if (!response.ok) return { data: null, connected: response.status !== 503 };
    return { data: (await response.json()) as ExperimentDetail, connected: true };
  } catch {
    return { data: null, connected: false };
  }
}
