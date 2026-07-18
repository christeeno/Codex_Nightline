export type ViewState = 'LANDING' | 'UPLOAD' | 'PROCESSING' | 'SUCCESS' | 'CONSOLE' | 'CITIZEN_DASHBOARD';

export interface Incident {
  id: string;
  trackingId: string;
  type: 'Traffic Violations' | 'Helmet Violations' | 'Triple Riding' | 'Potholes';
  title: string;
  time: string;
  date: string;
  severity: 'High' | 'Medium' | 'Low';
  confidence: number;
  licensePlate: string;
  location: string;
  status: 'Pending' | 'Verified' | 'Rejected';
  aiAnalysis: string;
  videoUrl: string;
  thumbnailUrl: string;
  evidenceUrl: string;
  rewardCr: number;
  timestampSeconds?: number;
  ocrConfidence?: number | null;
}

export interface SubmissionSummary {
  trackingId: string;
  submittedAt: string;
  incidentCount: number;
  rewardCredits: number;
  governmentResponse: string;
}

export interface DashboardStats {
  submitted: number;
  verified: number;
  pending: number;
  rejected: number;
  rewards: number;
  riskIndex: number;
  safetyScore: number;
  routesAnalyzed: number;
}
