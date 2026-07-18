import React, { useState } from 'react';
import { ViewState, Incident, DashboardStats } from './types';
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import LandingView from './components/LandingView';
import UploadView from './components/UploadView';
import ProcessingView from './components/ProcessingView';
import SuccessView from './components/SuccessView';
import ConsoleView from './components/ConsoleView';
import CitizenDashboardView from './components/CitizenDashboardView';

const INITIAL_INCIDENTS: Incident[] = [
  {
    id: 'inc_1',
    trackingId: 'VIO-892-001',
    type: 'Traffic Violations',
    title: 'Crossing Divider Line',
    time: '14:02:11',
    date: 'Jul 18, 2026',
    severity: 'High',
    confidence: 89.4,
    licensePlate: 'ABC-1234',
    location: 'Sector 4, Hwy Loop',
    status: 'Pending',
    aiAnalysis: 'Vehicle ABC-1234 was identified crossing a double yellow solid divider line at coordinates (45.829, -122.456). Threshold 0.85 exceeded.',
    videoUrl: '',
    thumbnailUrl: '',
    evidenceUrl: 'https://lh3.googleusercontent.com/aida-public/AB6AXuBWeJbUO1UKQwAriNl6y61IVwA2HMjj-fkOphOS0AzZIjJWF9o8tH9QZbiSGPyuNj3bjSzHksryKF9GvlUmKplWqFj3qtzDicPD9z_mI2t9swbysY9r7rUtte3ZPb4_vi8qB3ZdN3WTmGdoBh960wBXPbRjdkQWUTsKJ9Xn2ODx3-uV7JXr6omtaK684nSmwplX5To0qUYkuFnk-2A0yoAJrdyh2oWXNUZqnxh0suH_ntbQO4xF3dhPzyaOSk6C506XmGShGXbRoXI',
    rewardCr: 120
  },
  {
    id: 'inc_2',
    trackingId: 'VIO-892-002',
    type: 'Helmet Violations',
    title: 'Missing Helmet Detection',
    time: '14:15:33',
    date: 'Jul 18, 2026',
    severity: 'Medium',
    confidence: 94.1,
    licensePlate: 'XYZ-9876',
    location: 'Main Arterial, Sector 2',
    status: 'Pending',
    aiAnalysis: 'Rider and passenger on vehicle XYZ-9876 identified driving without protective safety helmet gear at coordinate (45.833, -122.461). Vision confidence 94.1%.',
    videoUrl: '',
    thumbnailUrl: '',
    evidenceUrl: 'https://lh3.googleusercontent.com/aida-public/AB6AXuBxDRKnvSOaLslHSMMmon49-s0gsWh2D_5PQ-NOUiSv-Q0y398B8ERU_SdyQosQZ4fIhcjsq90d5fjg5Ky9VmNhRS7OXhLB-9kI7Ey0WZG_uTGT5Jtsx-vcd4wefnDIV4x0loUTvebOV6lpdCQpUE7UQIWst848MNOIeIkCTr8Vl8FIBF72sLe3QLhuLo9-EWN8vNC50upkj4Lvj1_5PVEchUiZip4g6cMabb4uVcOXFC8mJhkxx5_LsFTwn-EKdlCOW9i0_GVNWkQ',
    rewardCr: 150
  },
  {
    id: 'inc_3',
    trackingId: 'VIO-892-003',
    type: 'Triple Riding',
    title: 'Triple Riding Infraction',
    time: '14:28:45',
    date: 'Jul 18, 2026',
    severity: 'High',
    confidence: 91.0,
    licensePlate: 'MNO-4567',
    location: 'Express Link Overpass',
    status: 'Pending',
    aiAnalysis: 'Motorcycle MNO-4567 carrying three active riders, exceeding the capacity regulations at coordinate (45.845, -122.472). Confidence score 91.0%.',
    videoUrl: '',
    thumbnailUrl: '',
    evidenceUrl: 'https://lh3.googleusercontent.com/aida-public/AB6AXuBxDRKnvSOaLslHSMMmon49-s0gsWh2D_5PQ-NOUiSv-Q0y398B8ERU_SdyQosQZ4fIhcjsq90d5fjg5Ky9VmNhRS7OXhLB-9kI7Ey0WZG_uTGT5Jtsx-vcd4wefnDIV4x0loUTvebOV6lpdCQpUE7UQIWst848MNOIeIkCTr8Vl8FIBF72sLe3QLhuLo9-EWN8vNC50upkj4Lvj1_5PVEchUiZip4g6cMabb4uVcOXFC8mJhkxx5_LsFTwn-EKdlCOW9i0_GVNWkQ',
    rewardCr: 180
  },
  {
    id: 'inc_4',
    trackingId: 'VIO-892-004',
    type: 'Potholes',
    title: 'Severe Asphalt Decay',
    time: '14:35:10',
    date: 'Jul 18, 2026',
    severity: 'Low',
    confidence: 82.5,
    licensePlate: '--',
    location: 'Arterial North, Junction 4',
    status: 'Pending',
    aiAnalysis: 'Severe physical asphalt decay of depth ~12cm logged at coordinates (45.855, -122.485). Suggested urgency level: Medium.',
    videoUrl: '',
    thumbnailUrl: '',
    evidenceUrl: 'https://lh3.googleusercontent.com/aida-public/AB6AXuBTpptbgcCUqtUvlYpyT7RybSuL7Dms6oonHPPABxfXS3uqDiruMPnVubBN1_B3XIdWtejEA4rTycrsH2FggT6rk0w0f88-RnCTn55HT2zpN9cQE-BrFJmy9Kc4HYSmp_lqwSpB4EL-YzVUEVaiZh_pUbSczNE93hgnb-xHtysGLDusuy310xU9NXr2T-Vq0M_o1lKSnZsI8ujXqDaIZmdXgNNgrKaxtkx31NdmfseH4TWbUF5tydTRk5GhGc8-1SnXtN37fFK2n7U',
    rewardCr: 80
  }
];

export default function App() {
  const [view, setView] = useState<ViewState>('LANDING');
  const [uploadedFile, setUploadedFile] = useState<{ name: string; size: string } | null>(null);
  
  // Real-time Dashboard Statistics
  const [stats, setStats] = useState<DashboardStats>({
    submitted: 185,
    verified: 128,
    pending: 4,
    rejected: 53,
    rewards: 12450,
    riskIndex: 12,
    safetyScore: 94,
    routesAnalyzed: 89
  });

  // Active Incidents state
  const [incidents, setIncidents] = useState<Incident[]>(INITIAL_INCIDENTS);

  const updateStatsOnAction = (type: 'APPROVE' | 'REJECT', points: number = 0) => {
    setStats(prev => {
      const nextPending = Math.max(0, prev.pending - 1);
      if (type === 'APPROVE') {
        return {
          ...prev,
          verified: prev.verified + 1,
          pending: nextPending,
          rewards: prev.rewards + points
        };
      } else {
        return {
          ...prev,
          rejected: prev.rejected + 1,
          pending: nextPending
        };
      }
    });
  };

  const handleEmergencyTrigger = () => {
    alert("Emergency SOS Broadcast Triggered: Broadcasting location coordinate logs & dashcam video streams to local transit authority dispatch team.");
  };

  // Conditional shell rendering
  const renderViewContent = () => {
    switch (view) {
      case 'LANDING':
        return <LandingView setView={setView} />;
      case 'UPLOAD':
        return (
          <UploadView 
            setView={setView} 
            setUploadedFile={(f) => {
              setUploadedFile(f);
              // Reset incident status to Pending for new reviews
              setIncidents(INITIAL_INCIDENTS);
              setStats(prev => ({ ...prev, pending: 4 }));
            }} 
          />
        );
      case 'PROCESSING':
        return <ProcessingView setView={setView} fileName={uploadedFile?.name || 'dashcam_0842.mp4'} />;
      case 'SUCCESS':
        return <SuccessView setView={setView} fileName={uploadedFile?.name || 'dashcam_0842.mp4'} />;
      case 'CONSOLE':
        return (
          <ConsoleView 
            setView={setView} 
            incidents={incidents} 
            setIncidents={setIncidents} 
            updateStats={updateStatsOnAction} 
          />
        );
      case 'CITIZEN_DASHBOARD':
        return <CitizenDashboardView setView={setView} stats={stats} />;
      default:
        return <LandingView setView={setView} />;
    }
  };

  // Determine which layout to show
  const hasSideBar = view === 'CONSOLE' || view === 'CITIZEN_DASHBOARD';
  const hasHeader = view === 'LANDING' || view === 'UPLOAD';

  if (hasSideBar) {
    return (
      <div className="flex h-screen overflow-hidden bg-slate-950 font-sans">
        <Sidebar currentView={view} setView={setView} onEmergencyTrigger={handleEmergencyTrigger} />
        <div className="flex-1 flex flex-col overflow-hidden relative">
          {renderViewContent()}
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 relative overflow-x-hidden font-sans">
      {hasHeader && <Header currentView={view} setView={setView} />}
      <div className="w-full">
        {renderViewContent()}
      </div>
    </div>
  );
}
