// During local development Vite proxies this path to the FastAPI backend,
// keeping browser requests same-origin and avoiding CORS requirements.
const API_BASE = import.meta.env.VITE_API_URL || '/api';

export interface ApiReport {
  id: string;
  filename: string;
  video_url: string | null;
  status: string;
  metadata: { duration: number | null; frame_count: number | null; fps: number | null };
}

export interface ApiIncident {
  id: string;
  type: string;
  title: string;
  timestamp: number;
  confidence: number;
  license_plate: string | null;
  ocr_confidence: number | null;
  evidence_url: string | null;
  status: string;
  reward_credits: number;
  details: Record<string, unknown>;
}

export interface Progress {
  frames_read: number;
  frames_remaining: number;
  current_timestamp: number;
  video_duration: number;
  percent_complete: number;
  estimated_time_remaining: number;
  current_stage: string;
  status: string;
  error: string | null;
}

export interface DashboardResponse {
  submitted: number; verified: number; pending: number; rejected: number; rewards: number;
  risk_index: number; safety_score: number; routes_analyzed: number;
}

export interface Submission {
  tracking_id: string;
  submitted_at: string;
  incident_count: number;
  reward_credits: number;
  government_response: string;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, init);
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || body.errors?.[0] || `Request failed (${response.status}).`);
  }
  const body = await response.json() as T | { data: T };
  return typeof body === 'object' && body !== null && 'data' in body ? body.data : body as T;
}

export const api = {
  upload: (file: File) => {
    const data = new FormData();
    data.append('video', file);
    return request<ApiReport>('/upload', { method: 'POST', body: data });
  },
  analyze: (id: string) => request(`/analyze/${id}`, { method: 'POST' }),
  progress: (id: string) => request<Progress>(`/reports/${id}/progress`),
  incidents: (id: string) => request<ApiIncident[]>(`/reports/${id}/incidents`),
  approve: (reportId: string, incidentId: string) => request<ApiIncident>(`/reports/${reportId}/incidents/${incidentId}/approve`, { method: 'POST' }),
  reject: (reportId: string, incidentId: string) => request<ApiIncident>(`/reports/${reportId}/incidents/${incidentId}/reject`, { method: 'POST' }),
  submit: (id: string) => request<Submission>(`/reports/${id}/submit`, { method: 'POST' }),
  dashboard: () => request<DashboardResponse>('/dashboard'),
  mediaUrl: (path: string | null) => path ? `${API_BASE}${path}` : '',
};
