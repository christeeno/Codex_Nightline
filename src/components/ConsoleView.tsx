import React, { useEffect, useRef, useState } from 'react';
import { ViewState, Incident } from '../types';
import { 
  Check, 
  X, 
  ChevronRight, 
  Sparkles, 
  ShieldAlert, 
  Eye, 
  RotateCcw, 
  Cpu, 
  Search,
  Filter,
  CheckCircle2,
  XCircle,
  Clock
} from 'lucide-react';

interface ConsoleViewProps {
  setView: (view: ViewState) => void;
  incidents: Incident[];
  onReview: (incidentId: string, action: 'APPROVE' | 'REJECT') => Promise<void>;
  onSubmit: () => Promise<void>;
  canSubmit: boolean;
}

export default function ConsoleView({ setView, incidents, onReview, onSubmit, canSubmit }: ConsoleViewProps) {
  const [selectedId, setSelectedId] = useState<string>(incidents[0]?.id || '');
  const [filterType, setFilterType] = useState<string>('All');
  const [searchQuery, setSearchQuery] = useState('');
  const [toastMessage, setToastMessage] = useState<string | null>(null);
  const videoRef = useRef<HTMLVideoElement>(null);

  // Active Incident
  const activeIncident = incidents.find(inc => inc.id === selectedId) || incidents[0];

  // Counters
  const countPendingByType = (type: string) => {
    return incidents.filter(inc => inc.type === type && inc.status === 'Pending').length;
  };

  useEffect(() => {
    if (!incidents.find(item => item.id === selectedId)) setSelectedId(incidents[0]?.id || '');
  }, [incidents, selectedId]);

  useEffect(() => {
    const incident = incidents.find(item => item.id === selectedId);
    if (incident && videoRef.current && incident.timestampSeconds !== undefined) {
      videoRef.current.currentTime = incident.timestampSeconds;
    }
  }, [incidents, selectedId]);

  const handleAction = async (id: string, action: 'APPROVE' | 'REJECT') => {
    const inc = incidents.find(i => i.id === id);
    if (!inc) return;

    const isPending = inc.status === 'Pending';
    if (!isPending) {
      showToast(`Incident already processed as ${inc.status}`);
      return;
    }

    try {
      await onReview(id, action);
      showToast(action === 'APPROVE' ? `Citation approved! +${inc.rewardCr} Cr credited.` : 'Incident marked as false positive.');
    } catch (error) {
      showToast(error instanceof Error ? error.message : 'Unable to save the review.');
      return;
    }

    // Auto-select next pending incident
    const nextPending = incidents.find(item => item.id !== id && item.status === 'Pending');
    if (nextPending) {
      setTimeout(() => {
        setSelectedId(nextPending.id);
      }, 500);
    }
  };

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => {
      setToastMessage(null);
    }, 3500);
  };

  const filteredIncidents = incidents.filter(inc => {
    const matchesFilter = filterType === 'All' || inc.type === filterType;
    const matchesSearch = inc.title.toLowerCase().includes(searchQuery.toLowerCase()) || 
                          inc.licensePlate.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesFilter && matchesSearch;
  });

  return (
    <div className="flex-1 flex flex-col h-screen overflow-hidden bg-slate-950">
      {/* Toast Notification */}
      {toastMessage && (
        <div className="fixed top-24 right-6 z-50 bg-slate-900 border-2 border-blue-400/30 text-blue-300 py-3.5 px-6 rounded-2xl shadow-2xl backdrop-blur-xl flex items-center gap-3 animate-bounce">
          <Sparkles className="text-blue-300 animate-pulse" size={18} />
          <span className="text-sm font-semibold">{toastMessage}</span>
        </div>
      )}

      {/* Top Header Row of workspace */}
      <header className="h-20 shrink-0 border-b border-slate-900/50 flex justify-between items-center px-8 bg-slate-950/80 backdrop-blur-lg">
        <div className="flex items-center gap-4">
          <h1 className="font-display text-xl font-bold text-white tracking-tight">
            PARA Verification Console
          </h1>
          <div className="h-4 w-px bg-slate-800"></div>
          <p className="text-xs text-slate-400 font-medium font-sans">
            Batch #892 (dashcam_0842.mp4)
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => void onSubmit().catch(error => showToast(error instanceof Error ? error.message : 'Submission failed.'))}
            disabled={!canSubmit}
            className={`text-xs px-4 py-2.5 rounded-lg transition-all font-medium ${canSubmit ? 'bg-emerald-500 text-slate-950 hover:bg-emerald-400 cursor-pointer' : 'bg-slate-900 text-slate-600 border border-slate-800 cursor-not-allowed'}`}
          >
            Submit Verified Report
          </button>
          <button 
            onClick={() => setView('UPLOAD')}
            className="text-xs bg-slate-900 border border-slate-800 hover:border-slate-700 hover:bg-slate-800 px-4 py-2.5 rounded-lg text-slate-300 transition-all font-medium cursor-pointer"
          >
            Upload New Video
          </button>
        </div>
      </header>

      {/* Workspace Area: 3 Columns */}
      <div className="flex-1 flex overflow-hidden">
        
        {/* Left Column: Stats & Category List */}
        <div className="w-80 border-r border-slate-900/50 flex flex-col justify-between shrink-0 p-6 bg-slate-950/40">
          <div className="space-y-6">
            <div>
              <div className="inline-flex items-center gap-2 px-3 py-1 bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-[10px] font-bold rounded-full uppercase tracking-wider mb-3">
                <Check size={10} /> Analyzed Successfully
              </div>
              <h2 className="font-display text-2xl font-black text-slate-100 tracking-tight">
                Batch Summary
              </h2>
            </div>

            {/* Counters Grid */}
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-slate-900/50 rounded-xl p-4 border border-slate-800/40 flex flex-col justify-between">
                <span className="text-[10px] text-slate-500 uppercase tracking-widest font-semibold">
                  Crossing
                </span>
                <div className="flex items-baseline gap-1 mt-2">
                  <span className="text-2xl font-bold text-slate-200">
                    {countPendingByType('Traffic Violations')}
                  </span>
                  <span className="text-xs text-slate-500">pending</span>
                </div>
              </div>

              <div className="bg-slate-900/50 rounded-xl p-4 border border-slate-800/40 flex flex-col justify-between">
                <span className="text-[10px] text-slate-500 uppercase tracking-widest font-semibold">
                  Helmet
                </span>
                <div className="flex items-baseline gap-1 mt-2">
                  <span className="text-2xl font-bold text-slate-200">
                    {countPendingByType('Helmet Violations')}
                  </span>
                  <span className="text-xs text-slate-500">pending</span>
                </div>
              </div>

              <div className="bg-slate-900/50 rounded-xl p-4 border border-slate-800/40 flex flex-col justify-between">
                <span className="text-[10px] text-slate-500 uppercase tracking-widest font-semibold">
                  Triple Riding
                </span>
                <div className="flex items-baseline gap-1 mt-2">
                  <span className="text-2xl font-bold text-slate-200">
                    {countPendingByType('Triple Riding')}
                  </span>
                  <span className="text-xs text-slate-500">pending</span>
                </div>
              </div>

              <div className="bg-slate-900/50 rounded-xl p-4 border border-slate-800/40 flex flex-col justify-between">
                <span className="text-[10px] text-slate-500 uppercase tracking-widest font-semibold">
                  Potholes
                </span>
                <div className="flex items-baseline gap-1 mt-2">
                  <span className="text-2xl font-bold text-slate-200">
                    {countPendingByType('Potholes')}
                  </span>
                  <span className="text-xs text-slate-500">pending</span>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-blue-500/5 rounded-xl p-4 border border-blue-500/10 space-y-3">
            <div className="flex items-center gap-2 text-blue-300">
              <Cpu size={16} className="animate-spin" style={{ animationDuration: '6s' }} />
              <h4 className="font-display text-xs font-bold uppercase tracking-wider">
                Copilot Suggestions
              </h4>
            </div>
            <p className="text-slate-400 text-xs leading-relaxed">
              Models have flagged high-confidence license readings. Review each timeline entry to confirm correct plate numbers.
            </p>
          </div>
        </div>

        {/* Center Column: Scrollable Incident Timeline */}
        <div className="flex-1 flex flex-col overflow-hidden border-r border-slate-900/50 bg-slate-950/20">
          {/* Timeline Filter Header */}
          <div className="p-4 border-b border-slate-900/50 space-y-3 shrink-0">
            {/* Search Input */}
            <div className="relative">
              <Search className="absolute left-3.5 top-3 text-slate-500" size={16} />
              <input 
                type="text" 
                placeholder="Search by license plate or type..." 
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-slate-900/80 text-xs border border-slate-800/80 pl-10 pr-4 py-3 rounded-xl focus:border-blue-400 focus:outline-none transition-colors placeholder-slate-500 font-medium"
              />
            </div>

            {/* Filter Category Tabs */}
            <div className="flex gap-2 overflow-x-auto scrollbar-hide">
              {['All', 'Traffic Violations', 'Helmet Violations', 'Triple Riding', 'Potholes'].map((cat) => (
                <button
                  key={cat}
                  onClick={() => setFilterType(cat)}
                  className={`px-3.5 py-2 rounded-xl text-xs font-semibold whitespace-nowrap transition-all cursor-pointer ${
                    filterType === cat 
                      ? 'bg-blue-500/15 text-blue-300 border border-blue-500/40' 
                      : 'bg-slate-900/40 text-slate-500 border border-slate-850 hover:text-slate-300'
                  }`}
                >
                  {cat === 'Traffic Violations' ? 'Crossing Divider' : cat === 'Helmet Violations' ? 'Helmet' : cat}
                </button>
              ))}
            </div>
          </div>

          {/* Timeline Feed list */}
          <div className="flex-grow overflow-y-auto p-4 space-y-4">
            {filteredIncidents.length === 0 ? (
              <div className="text-center py-24 text-slate-500">
                <Filter size={32} className="mx-auto mb-3 opacity-30" />
                <p className="text-xs">No incidents match current filters.</p>
              </div>
            ) : (
              filteredIncidents.map((inc) => (
                <div
                  key={inc.id}
                  onClick={() => setSelectedId(inc.id)}
                  className={`p-4 rounded-2xl border transition-all duration-300 cursor-pointer relative flex flex-col gap-3 group ${
                    selectedId === inc.id
                      ? 'bg-blue-500/5 border-blue-500/40 shadow-[0_0_20px_rgba(59,130,246,0.05)]'
                      : 'bg-slate-900/40 border-slate-850 hover:bg-slate-900/80 hover:border-slate-800'
                  }`}
                >
                  <div className="flex justify-between items-start gap-4">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className={`w-2 h-2 rounded-full ${
                          inc.severity === 'High' ? 'bg-red-400' : inc.severity === 'Medium' ? 'bg-amber-400' : 'bg-blue-400'
                        }`}></span>
                        <h4 className="font-display font-bold text-sm text-slate-200 group-hover:text-blue-300 transition-colors">
                          {inc.title}
                        </h4>
                      </div>
                      <div className="flex gap-2.5 items-center mt-1 text-[10px] text-slate-500 font-medium font-mono uppercase tracking-wide">
                        <span>{inc.trackingId}</span>
                        <span>•</span>
                        <span>{inc.time}</span>
                      </div>
                    </div>

                    {/* Status Badge */}
                    <div>
                      {inc.status === 'Verified' ? (
                        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-[10px] font-bold">
                          <CheckCircle2 size={12} /> Verified
                        </span>
                      ) : inc.status === 'Rejected' ? (
                        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-red-500/10 border border-red-500/20 text-red-400 text-[10px] font-bold">
                          <XCircle size={12} /> Rejected
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400 text-[10px] font-bold">
                          <Clock size={12} /> Pending
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="flex justify-between items-center mt-1 border-t border-slate-850/50 pt-2 text-[11px] text-slate-400">
                    <span className="font-sans font-medium">Plate: <span className="font-mono text-slate-200 font-semibold">{inc.licensePlate}</span></span>
                    <span className="font-mono text-slate-500">Conf: <span className="text-blue-300 font-bold">{inc.confidence.toFixed(1)}%</span></span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Right Column: AI Evidence Detail Workbench */}
        {activeIncident && (
          <div className="w-1/2 shrink-0 flex flex-col overflow-y-auto p-6 bg-slate-950 space-y-6">
            
            {/* Camera View Player */}
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <h3 className="font-display text-sm font-bold text-slate-300 flex items-center gap-2">
                  <Eye size={16} /> Bounding Box Preview
                </h3>
                <span className="font-mono text-[10px] text-slate-500">Live Crop Coordinates</span>
              </div>
              
              <div className="w-full aspect-video rounded-2xl bg-slate-900 border border-slate-800/60 relative overflow-hidden flex items-center justify-center">
                <img 
                  alt="Incident detection frame" 
                  className="w-full h-full object-cover" 
                  src={activeIncident.evidenceUrl} 
                />
                <div className="absolute inset-0 bg-slate-950/20 pointer-events-none"></div>

                {/* Bounding Box Drawing */}
                <div className="absolute border-2 border-red-500 bg-red-500/10 animate-pulse rounded-lg flex flex-col p-1 font-mono text-[9px] text-white font-bold"
                  style={{
                    top: '25%',
                    left: '35%',
                    width: '35%',
                    height: '45%'
                  }}
                >
                  <span className="bg-red-500 px-1 py-0.5 self-start rounded text-[8px] leading-none mb-1">
                    {activeIncident.title.toUpperCase()}
                  </span>
                  <span>{activeIncident.confidence.toFixed(1)}% confidence</span>
                  <span>Plate: {activeIncident.licensePlate}</span>
                </div>
              </div>
              {activeIncident.videoUrl && (
                <div className="flex items-center gap-3">
                  <button
                    onClick={() => { const player = videoRef.current; if (player) { player.currentTime = activeIncident.timestampSeconds || 0; void player.play(); } }}
                    className="text-xs text-blue-300 border border-blue-500/30 hover:bg-blue-500/10 px-3 py-2 rounded-lg cursor-pointer"
                  >
                    Jump To Video • {activeIncident.time}
                  </button>
                  <video ref={videoRef} src={activeIncident.videoUrl} controls className="h-10 max-w-[60%] rounded border border-slate-800" />
                </div>
              )}
            </div>

            {/* Evidence details card */}
            <div className="grid grid-cols-2 gap-4">
              {/* Box 1: Bounding details */}
              <div className="bg-slate-900/40 rounded-xl p-4 border border-slate-800/40 flex flex-col gap-1.5 justify-between">
                <div>
                  <span className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold">
                    Confidence Matrix
                  </span>
                  <div className="font-mono text-2xl font-bold text-blue-300 mt-1 glow-text">
                    {activeIncident.confidence.toFixed(2)}%
                  </div>
                </div>
                <div className="w-full bg-slate-950 rounded-full h-1 overflow-hidden border border-slate-800/20">
                  <div className="bg-blue-400 h-full rounded-full" style={{ width: `${activeIncident.confidence}%` }}></div>
                </div>
              </div>

              {/* Box 2: Evidence Zoom (Plate Detail) */}
              <div className="bg-slate-900/40 rounded-xl p-4 border border-slate-800/40 flex flex-col gap-1.5 justify-between">
                <div>
                  <span className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold text-left">
                    License Plate Crop
                  </span>
                  <div className="font-mono text-2xl font-black tracking-widest text-slate-100 uppercase mt-1">
                    {activeIncident.licensePlate}
                  </div>
                </div>
                <div className="flex justify-between items-center border-t border-slate-800/40 pt-1.5 text-[10px] text-slate-500 font-mono">
                  <span>Detected: OCR_v2</span>
                  <span>CONF: High</span>
                </div>
              </div>
            </div>

            {/* Explanation / AI analysis block */}
            <div className="glass-panel rounded-xl p-5 border border-slate-800/40 space-y-3">
              <h4 className="font-display text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-2">
                <Cpu size={14} className="text-blue-300" /> Model Diagnostic Details
              </h4>
              <p className="font-sans text-slate-400 text-xs leading-relaxed">
                {activeIncident.aiAnalysis}
              </p>
            </div>

            {/* Final Action Row (Sticky at bottom) */}
            <div className="flex gap-4 pt-4 border-t border-slate-900/50 mt-auto">
              <button 
                onClick={() => handleAction(activeIncident.id, 'REJECT')}
                disabled={activeIncident.status !== 'Pending'}
                className={`flex-1 py-3 px-5 rounded-xl text-xs font-semibold flex items-center justify-center gap-2 border transition-all cursor-pointer ${
                  activeIncident.status === 'Pending'
                    ? 'bg-red-500/10 text-red-300 border-red-500/30 hover:bg-red-500/20'
                    : 'bg-slate-900 text-slate-600 border-slate-850 cursor-not-allowed opacity-55'
                }`}
              >
                <X size={14} />
                Reject False Positive
              </button>

              <button 
                onClick={() => handleAction(activeIncident.id, 'APPROVE')}
                disabled={activeIncident.status !== 'Pending'}
                className={`flex-1 py-3 px-5 rounded-xl text-xs font-semibold flex items-center justify-center gap-2 border transition-all cursor-pointer ${
                  activeIncident.status === 'Pending'
                    ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30 hover:bg-emerald-500/20 hover:shadow-[0_0_15px_rgba(16,185,129,0.1)]'
                    : 'bg-slate-900 text-slate-600 border-slate-850 cursor-not-allowed opacity-55'
                }`}
              >
                <Check size={14} />
                Approve & Generate Citation
              </button>
            </div>

          </div>
        )}

      </div>
    </div>
  );
}
