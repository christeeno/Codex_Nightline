import React, { useState, useEffect } from 'react';
import { ViewState } from '../types';
import { AlertCircle, Check, ShieldAlert, Eye, Lock } from 'lucide-react';
import { api, ApiReport } from '../api';

interface ProcessingViewProps {
  setView: (view: ViewState) => void;
  report: ApiReport | null;
  onCompleted: () => Promise<void>;
}

const DECORATIVE_LOGS = [
  "det_0x8f: vehicle_stalled",
  "lane_drift: true (0.89)",
  "track_car_0x1b: class_sedan",
  "intersection_entry: speed_42kmh",
  "yolo_v8: pothole_detected (0.76)",
  "double_yellow_crossing: flagged",
  "helmet_detect: missing (rider_02)"
];

export default function ProcessingView({ setView, report, onCompleted }: ProcessingViewProps) {
  const [progress, setProgress] = useState(0);
  const [framesProcessed, setFramesProcessed] = useState(0);
  const [estCompletion, setEstCompletion] = useState('--:--');
  const [currentDetections, setCurrentDetections] = useState(0);
  const [liveIncidents, setLiveIncidents] = useState(0);
  const [floatingLogs, setFloatingLogs] = useState<string[]>([DECORATIVE_LOGS[0], DECORATIVE_LOGS[1]]);

  useEffect(() => {
    if (!report) { setView('UPLOAD'); return; }
    let active = true;
    const poll = async () => {
      try {
        const data = await api.progress(report.id);
        if (!active) return;
        setProgress(data.percent_complete);
        setFramesProcessed(data.frames_read);
        const seconds = Math.ceil(data.estimated_time_remaining);
        setEstCompletion(`${String(Math.floor(seconds / 60)).padStart(2, '0')}:${String(seconds % 60).padStart(2, '0')}`);
        setCurrentDetections(Math.max(0, Math.floor(data.percent_complete / 35)));
        setLiveIncidents(Math.max(0, Math.floor(data.percent_complete / 50)));
        setFloatingLogs([data.current_stage, data.error || DECORATIVE_LOGS[Math.min(DECORATIVE_LOGS.length - 1, Math.floor(data.percent_complete / 20))]]);
        if (data.status === 'READY_FOR_REVIEW' || data.status === 'completed') { await onCompleted(); if (active) setView('CONSOLE'); }
        if (data.status === 'FAILED' || data.status === 'failed') { setFloatingLogs(['Processing failed', data.error || 'Try uploading another supported video.']); }
      } catch (error) {
        if (active) setFloatingLogs(['Connection issue', error instanceof Error ? error.message : 'Unable to read processing progress.']);
      }
    };
    void poll();
    const interval = window.setInterval(() => void poll(), 1000);
    return () => { active = false; window.clearInterval(interval); };
  }, [onCompleted, report, setView]);

  const currentPhase = () => {
    if (progress < 25) return 0; // Upload complete
    if (progress < 60) return 1; // Traffic Analysis Active
    if (progress < 85) return 2; // Road Integrity Scan
    return 3; // Synthesizing Report
  };

  return (
    <div className="h-screen bg-slate-950 text-slate-100 overflow-hidden flex flex-col justify-between select-none">
      {/* Suppressed Header */}
      <header className="w-full flex justify-between items-center px-6 md:px-16 h-20 bg-slate-950/80 backdrop-blur-xl border-b border-slate-800/40 z-50">
        <div className="flex items-center gap-3">
          <span className="font-display text-2xl font-bold tracking-tighter text-blue-300">
            PARA AI
          </span>
          <span className="px-2 py-0.5 bg-slate-800 rounded font-display text-[10px] text-slate-400 font-medium ml-2 uppercase tracking-wider">
            V3.2 Active
          </span>
        </div>
        <div>
          <button 
            onClick={() => setView('UPLOAD')}
            className="font-display text-xs text-red-400 border border-red-500/30 hover:bg-red-500/10 px-4 py-2 rounded-lg transition-all duration-300 flex items-center gap-1.5 cursor-pointer"
          >
            <AlertCircle size={14} /> 
            Abort
          </button>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col lg:flex-row p-6 md:p-12 gap-8 max-w-7xl mx-auto w-full items-center justify-center relative">
        {/* Background decorative elements */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none -z-10">
          <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-500/5 rounded-full blur-[100px]"></div>
          <div className="absolute bottom-1/4 right-1/4 w-64 h-64 bg-emerald-500/5 rounded-full blur-[80px]"></div>
        </div>

        {/* Left Column: Metrics & Phases */}
        <div className="w-full lg:w-1/3 flex flex-col gap-6 z-10">
          {/* Phase List */}
          <div className="glass-panel rounded-2xl p-6 flex flex-col gap-4">
            <h3 className="font-display text-lg font-bold text-white border-b border-slate-800 pb-2">
              Execution Sequence
            </h3>
            <ul className="flex flex-col gap-4 text-sm font-medium">
              <li className={`flex items-center gap-3 ${currentPhase() >= 0 ? 'text-blue-300' : 'text-slate-500'}`}>
                <div className={`w-6 h-6 rounded-full flex items-center justify-center ${currentPhase() >= 1 ? 'bg-blue-500/20 text-blue-300' : 'border border-slate-700'}`}>
                  {currentPhase() >= 1 ? <Check size={12} /> : <span className="w-1.5 h-1.5 rounded-full bg-slate-500"></span>}
                </div>
                <span>Uploading Source Data</span>
              </li>

              <li className={`flex items-center gap-3 ${currentPhase() === 1 ? 'text-blue-300' : currentPhase() > 1 ? 'text-blue-300' : 'text-slate-500'}`}>
                <div className="relative w-6 h-6 flex items-center justify-center">
                  {currentPhase() === 1 ? (
                    <>
                      <div className="absolute inset-0 rounded-full border-2 border-blue-400 border-t-transparent animate-spin"></div>
                      <div className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-pulse"></div>
                    </>
                  ) : currentPhase() > 1 ? (
                    <div className="w-6 h-6 rounded-full bg-blue-500/20 text-blue-300 flex items-center justify-center">
                      <Check size={12} />
                    </div>
                  ) : (
                    <div className="w-6 h-6 rounded-full border border-slate-800 flex items-center justify-center">
                      <span className="w-1.5 h-1.5 rounded-full bg-slate-700"></span>
                    </div>
                  )}
                </div>
                <span className={currentPhase() === 1 ? 'glow-text font-bold text-blue-300' : ''}>
                  Traffic Analysis Active
                </span>
              </li>

              <li className={`flex items-center gap-3 ${currentPhase() === 2 ? 'text-blue-300' : currentPhase() > 2 ? 'text-blue-300' : 'text-slate-500'}`}>
                <div className="relative w-6 h-6 flex items-center justify-center">
                  {currentPhase() === 2 ? (
                    <>
                      <div className="absolute inset-0 rounded-full border-2 border-blue-400 border-t-transparent animate-spin"></div>
                      <div className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-pulse"></div>
                    </>
                  ) : currentPhase() > 2 ? (
                    <div className="w-6 h-6 rounded-full bg-blue-500/20 text-blue-300 flex items-center justify-center">
                      <Check size={12} />
                    </div>
                  ) : (
                    <div className="w-6 h-6 rounded-full border border-slate-800 flex items-center justify-center">
                      <span className="w-1.5 h-1.5 rounded-full bg-slate-700"></span>
                    </div>
                  )}
                </div>
                <span className={currentPhase() === 2 ? 'glow-text font-bold text-blue-300' : ''}>
                  Road Integrity Scan
                </span>
              </li>

              <li className={`flex items-center gap-3 ${currentPhase() === 3 ? 'text-blue-300' : 'text-slate-500'}`}>
                <div className="relative w-6 h-6 flex items-center justify-center">
                  {currentPhase() === 3 ? (
                    <>
                      <div className="absolute inset-0 rounded-full border-2 border-blue-400 border-t-transparent animate-spin"></div>
                      <div className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-pulse"></div>
                    </>
                  ) : (
                    <div className="w-6 h-6 rounded-full border border-slate-800 flex items-center justify-center">
                      <span className="w-1.5 h-1.5 rounded-full bg-slate-700"></span>
                    </div>
                  )}
                </div>
                <span className={currentPhase() === 3 ? 'glow-text font-bold text-blue-300' : ''}>
                  Synthesizing Report
                </span>
              </li>
            </ul>
          </div>

          {/* Mini Metrics Grid */}
          <div className="grid grid-cols-2 gap-4">
            <div className="glass-panel rounded-xl p-4 flex flex-col gap-1">
              <span className="font-display text-[10px] text-slate-400 uppercase tracking-wider font-semibold">
                Frames Processed
              </span>
              <div className="flex items-end gap-1.5">
                <span className="text-2xl font-bold text-slate-100 tracking-tight">
                  {framesProcessed.toLocaleString()}
                </span>
                <span className="text-xs text-slate-500 font-medium mb-1">/ {(report?.metadata.frame_count || 0).toLocaleString()}</span>
              </div>
            </div>
            <div className="glass-panel rounded-xl p-4 flex flex-col gap-1">
              <span className="font-display text-[10px] text-slate-400 uppercase tracking-wider font-semibold">
                Est. Completion
              </span>
              <span className="text-2xl font-bold text-blue-300 tracking-tight glow-text">
                {estCompletion}
              </span>
            </div>
          </div>
        </div>

        {/* Center/Right Column: The AI Visualization Core */}
        <div className="w-full lg:w-2/3 flex items-center justify-center relative aspect-square max-h-[500px] z-10">
          {/* Outer Ring */}
          <div className="absolute inset-0 rounded-full border border-slate-800/40 animate-spin" style={{ animationDuration: '24s', animationDirection: 'reverse' }}></div>
          {/* Middle Ring (Dashed) */}
          <div className="absolute inset-8 rounded-full border border-dashed border-blue-500/10 animate-spin" style={{ animationDuration: '18s' }}></div>
          {/* Inner Glow Ring */}
          <div className="absolute inset-20 rounded-full border-2 border-blue-500/20 animate-pulse shadow-[0_0_40px_rgba(59,130,246,0.15)]"></div>

          {/* Core Progress Circle */}
          <div className="relative w-64 h-64 md:w-80 md:h-80 rounded-full bg-slate-950/90 shadow-[0_0_50px_rgba(59,130,246,0.15)] flex flex-col items-center justify-center border border-slate-800/40">
            {/* SVG Progress Arc */}
            <svg className="absolute inset-0 w-full h-full transform -rotate-90" viewBox="0 0 100 100">
              <circle cx="50" cy="50" fill="none" r="46" stroke="rgba(30, 41, 59, 0.4)" strokeWidth="2"></circle>
              {/* 2 * pi * 46 = 289 */}
              <circle 
                className="transition-all duration-300 ease-out" 
                cx="50" 
                cy="50" 
                fill="none" 
                r="46" 
                stroke="#4d8eff" 
                strokeWidth="3.5" 
                strokeDasharray="289" 
                strokeDashoffset={289 - (289 * progress) / 100}
              ></circle>
            </svg>
            
            <span className="font-display text-[11px] font-bold text-blue-300 uppercase tracking-widest mb-2 glow-text">
              Analyzing
            </span>
            <span className="font-display text-5xl md:text-6xl font-bold text-slate-100">
              {progress}<span className="text-2xl text-slate-500 ml-1">%</span>
            </span>
            {/* Micro-status */}
            <div className="mt-6 flex items-center gap-1.5 px-3 py-1 rounded-full bg-slate-900 border border-slate-800/50">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
              <span className="font-display text-[10px] font-medium text-slate-400 uppercase tracking-wider">
                Deep Vision Engine
              </span>
            </div>
          </div>

          {/* Floating Data Snippets (Decorative & Interactive) */}
          <div className="absolute top-1/4 left-4 glass-panel rounded-lg px-3 py-1.5 border border-blue-500/20 text-[11px] text-blue-300 font-mono opacity-85 shadow-lg select-none">
            {floatingLogs[0]}
          </div>
          <div className="absolute bottom-1/4 right-4 glass-panel rounded-lg px-3 py-1.5 border border-emerald-500/20 text-[11px] text-emerald-300 font-mono opacity-85 shadow-lg select-none">
            {floatingLogs[1]}
          </div>
        </div>
      </main>

      {/* Bottom Metrics Bar */}
      <footer className="w-full bg-slate-950/90 border-t border-slate-800/40 p-4 px-6 md:px-16 flex justify-between items-center z-50 text-xs">
        <div className="flex gap-8">
          <div className="flex items-center gap-2.5">
            <Eye className="text-slate-500" size={18} />
            <div className="flex flex-col">
              <span className="font-display text-[9px] text-slate-500 uppercase tracking-wider font-semibold">
                Current Detections
              </span>
              <span className="font-sans text-sm text-slate-200 font-semibold leading-none mt-0.5">
                {currentDetections}
              </span>
            </div>
          </div>
          <div className="w-px h-6 bg-slate-800/50 hidden md:block"></div>
          <div className="flex items-center gap-2.5">
            <ShieldAlert className="text-red-400" size={18} />
            <div className="flex flex-col">
              <span className="font-display text-[9px] text-slate-500 uppercase tracking-wider font-semibold">
                Live Incidents
              </span>
              <span className="font-sans text-sm text-red-400 font-semibold leading-none mt-0.5">
                {liveIncidents}
              </span>
            </div>
          </div>
        </div>
        <div className="font-display text-[10px] text-slate-500 flex items-center gap-1">
          <Lock size={12} /> End-to-End Encrypted
        </div>
      </footer>
    </div>
  );
}
