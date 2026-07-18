import { useCallback, useEffect, useState } from 'react';
import { api, ApiIncident, ApiReport, DashboardResponse } from './api';
import { DashboardStats, Incident, SubmissionSummary, ViewState } from './types';
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import LandingView from './components/LandingView';
import UploadView from './components/UploadView';
import ProcessingView from './components/ProcessingView';
import SuccessView from './components/SuccessView';
import ConsoleView from './components/ConsoleView';
import CitizenDashboardView from './components/CitizenDashboardView';

const EMPTY_STATS: DashboardStats = { submitted: 0, verified: 0, pending: 0, rejected: 0, rewards: 0, riskIndex: 12, safetyScore: 94, routesAnalyzed: 0 };

const toIncident = (item: ApiIncident, report: ApiReport | null): Incident => ({
  id: item.id,
  trackingId: item.id.slice(0, 8).toUpperCase(),
  type: item.type === 'pothole' ? 'Potholes' : 'Helmet Violations',
  title: item.title,
  time: new Date(item.timestamp * 1000).toISOString().slice(14, 19),
  date: new Date().toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' }),
  severity: item.confidence >= 0.9 ? 'High' : 'Medium',
  confidence: item.confidence * 100,
  licensePlate: item.license_plate || '--',
  location: 'Dashcam route',
  status: item.status === 'approved' ? 'Verified' : item.status === 'rejected' ? 'Rejected' : 'Pending',
  aiAnalysis: item.details.source === 'demo_inference' ? 'Demo inference result awaiting human confirmation.' : 'AI evidence awaiting human confirmation.',
  videoUrl: api.mediaUrl(report?.video_url || null),
  thumbnailUrl: api.mediaUrl(item.evidence_url),
  evidenceUrl: api.mediaUrl(item.evidence_url),
  rewardCr: item.reward_credits,
  timestampSeconds: item.timestamp,
  ocrConfidence: item.ocr_confidence,
});

const toStats = (data: DashboardResponse): DashboardStats => ({
  submitted: data.submitted, verified: data.verified, pending: data.pending, rejected: data.rejected,
  rewards: data.rewards, riskIndex: data.risk_index, safetyScore: data.safety_score, routesAnalyzed: data.routes_analyzed,
});

export default function App() {
  const [view, setView] = useState<ViewState>('LANDING');
  const [report, setReport] = useState<ApiReport | null>(null);
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [stats, setStats] = useState<DashboardStats>(EMPTY_STATS);
  const [submission, setSubmission] = useState<SubmissionSummary | null>(null);

  const refreshDashboard = useCallback(async () => {
    try { setStats(toStats(await api.dashboard())); } catch { /* dashboard remains usable offline */ }
  }, []);
  useEffect(() => { void refreshDashboard(); }, [refreshDashboard]);

  const loadIncidents = useCallback(async () => {
    if (!report) return;
    const values = await api.incidents(report.id);
    setIncidents(values.map(item => toIncident(item, report)));
    await refreshDashboard();
  }, [report, refreshDashboard]);

  const handleUploaded = (nextReport: ApiReport) => {
    setReport(nextReport);
    setIncidents([]);
    setSubmission(null);
  };

  const handleReview = async (incidentId: string, action: 'APPROVE' | 'REJECT') => {
    if (!report) return;
    const updated = action === 'APPROVE' ? await api.approve(report.id, incidentId) : await api.reject(report.id, incidentId);
    setIncidents(current => current.map(item => item.id === incidentId ? toIncident(updated, report) : item));
    await refreshDashboard();
  };

  const handleSubmit = async () => {
    if (!report) return;
    const result = await api.submit(report.id);
    setSubmission({ trackingId: result.tracking_id, submittedAt: result.submitted_at, incidentCount: result.incident_count, rewardCredits: result.reward_credits, governmentResponse: result.government_response });
    await refreshDashboard();
    setView('SUCCESS');
  };

  const content = () => {
    switch (view) {
      case 'LANDING': return <LandingView setView={setView} />;
      case 'UPLOAD': return <UploadView setView={setView} onUploadComplete={handleUploaded} />;
      case 'PROCESSING': return <ProcessingView setView={setView} report={report} onCompleted={loadIncidents} />;
      case 'CONSOLE': return <ConsoleView setView={setView} incidents={incidents} onReview={handleReview} onSubmit={handleSubmit} canSubmit={incidents.some(item => item.status === 'Verified')} />;
      case 'SUCCESS': return <SuccessView setView={setView} fileName={report?.filename || 'dashcam footage'} submission={submission} />;
      case 'CITIZEN_DASHBOARD': return <CitizenDashboardView setView={setView} stats={stats} />;
      default: return <LandingView setView={setView} />;
    }
  };

  const hasSideBar = view === 'CONSOLE' || view === 'CITIZEN_DASHBOARD';
  const hasHeader = view === 'LANDING' || view === 'UPLOAD';
  if (hasSideBar) return <div className="flex h-screen overflow-hidden bg-slate-950 font-sans"><Sidebar currentView={view} setView={setView} onEmergencyTrigger={() => alert('Emergency SOS broadcast is a demo-only action.')} /><div className="flex-1 flex flex-col overflow-hidden relative">{content()}</div></div>;
  return <div className="min-h-screen bg-slate-950 relative overflow-x-hidden font-sans">{hasHeader && <Header currentView={view} setView={setView} />}<div className="w-full">{content()}</div></div>;
}
