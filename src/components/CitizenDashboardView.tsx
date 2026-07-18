import React, { useState } from 'react';
import { ViewState, DashboardStats } from '../types';
import { 
  Sparkles, 
  TrendingUp, 
  Award, 
  ShieldCheck, 
  ChevronRight, 
  Zap, 
  MapPin, 
  Lock,
  ArrowUpRight,
  ShieldAlert,
  Flame,
  CheckCircle,
  XCircle,
  Clock
} from 'lucide-react';

interface CitizenDashboardViewProps {
  setView: (view: ViewState) => void;
  stats: DashboardStats;
}

export default function CitizenDashboardView({ setView, stats }: CitizenDashboardViewProps) {
  const [isPro, setIsPro] = useState(false);
  const [activeTab, setActiveTab] = useState<'WEEK' | 'MONTH' | 'YEAR'>('MONTH');

  // SVG Area Chart points based on timeframe selection
  const getChartPoints = () => {
    if (activeTab === 'WEEK') {
      return {
        points: "0,140 100,110 200,90 300,50 400,20 500,45 600,10",
        fillPoints: "0,140 100,110 200,90 300,50 400,20 500,45 600,10 600,150 0,150",
        labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
      };
    }
    if (activeTab === 'YEAR') {
      return {
        points: "0,130 100,120 200,100 300,80 400,60 500,40 600,20",
        fillPoints: "0,130 100,120 200,100 300,80 400,60 500,40 600,20 600,150 0,150",
        labels: ['2021', '2022', '2023', '2024', '2025', '2026', 'Current']
      };
    }
    // Default: MONTH
    return {
      points: "0,120 100,95 200,110 300,60 400,45 500,30 600,15",
      fillPoints: "0,120 100,95 200,110 300,60 400,45 500,30 600,15 600,150 0,150",
      labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul']
    };
  };

  const chartData = getChartPoints();

  return (
    <div className="flex-grow overflow-y-auto h-screen pb-20 bg-slate-950">
      {/* Hero Welcome banner */}
      <section className="pt-24 px-8 pb-8 shrink-0 flex flex-col md:flex-row justify-between items-start md:items-center gap-6 border-b border-slate-900/40 bg-slate-950/20">
        <div>
          <div className="flex items-center gap-3.5">
            <div className="w-12 h-12 rounded-full overflow-hidden border-2 border-blue-400 shadow-[0_0_15px_rgba(59,130,246,0.3)]">
              <img 
                alt="Trooper Avatar" 
                className="w-full h-full object-cover" 
                src="https://lh3.googleusercontent.com/aida-public/AB6AXuCCwadGntoKIFFfNgq2WnLzfpj9sXzQnQ7YFGnPz_ZY9P9G1fqVg45a7sno1w37gb0SM2zFl2zlFvGvkweD65wjM0kwAa7yW3Tv3nRtBoc5ZpdWt0NOg50mKEUitAW6txGRVcF1EpZuMFjstf1W6sgwp-GoskYD-NDfaqCMGSz7_qZvSJba9mIMnybWLd900gmvCpsiWX5jM9JPgSXxWKe5GPlqFnO1JL1Y_O78xaQZp7dIPzPevfifSNmGcTDq7m63ZsZjAmne2OU" 
              />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="font-display text-2xl font-black text-slate-100 tracking-tight">
                  Welcome back, Trooper
                </h1>
                <span className="px-2 py-0.5 bg-blue-500/10 text-blue-300 rounded font-display text-[9px] font-bold uppercase tracking-wider">
                  Tier 3 Elite
                </span>
              </div>
              <p className="text-xs text-slate-400 font-sans mt-0.5">
                PRECINCT: 092-METRO • SECTOR: AP-NORTH
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button 
            onClick={() => setView('UPLOAD')}
            className="px-5 py-3 bg-blue-500 hover:bg-blue-400 text-white font-medium text-xs rounded-xl flex items-center gap-1.5 shadow-[0_0_20px_rgba(59,130,246,0.2)] transition-all duration-300 hover:scale-[1.02] cursor-pointer"
          >
            <Zap size={14} /> Analyze New Footage
          </button>
        </div>
      </section>

      <div className="p-8 max-w-7xl mx-auto space-y-8">
        {/* KPI Cards Row */}
        <section className="grid grid-cols-2 lg:grid-cols-5 gap-4">
          <div className="glass-panel rounded-2xl p-5 border border-slate-800/40 flex flex-col justify-between h-32 relative group overflow-hidden">
            <div className="absolute top-0 right-0 w-16 h-16 bg-blue-500/5 rounded-full blur-xl group-hover:bg-blue-500/10 transition-colors pointer-events-none"></div>
            <span className="text-[10px] text-slate-500 uppercase tracking-widest font-bold">
              Submitted
            </span>
            <div className="flex items-baseline justify-between mt-auto">
              <span className="font-display text-3xl font-black text-slate-100 tracking-tight">
                {stats.submitted}
              </span>
              <span className="text-[10px] text-blue-300 font-mono font-bold uppercase">Reports</span>
            </div>
          </div>

          <div className="glass-panel rounded-2xl p-5 border border-slate-800/40 flex flex-col justify-between h-32 relative group overflow-hidden">
            <div className="absolute top-0 right-0 w-16 h-16 bg-emerald-500/5 rounded-full blur-xl group-hover:bg-emerald-500/10 transition-colors pointer-events-none"></div>
            <span className="text-[10px] text-slate-500 uppercase tracking-widest font-bold">
              Verified
            </span>
            <div className="flex items-baseline justify-between mt-auto">
              <span className="font-display text-3xl font-black text-emerald-400 tracking-tight">
                {stats.verified}
              </span>
              <span className="text-[10px] text-emerald-400 font-mono font-bold uppercase">90.1% Ratio</span>
            </div>
          </div>

          <div className="glass-panel rounded-2xl p-5 border border-slate-800/40 flex flex-col justify-between h-32 relative group overflow-hidden">
            <div className="absolute top-0 right-0 w-16 h-16 bg-amber-500/5 rounded-full blur-xl group-hover:bg-amber-500/10 transition-colors pointer-events-none"></div>
            <span className="text-[10px] text-slate-500 uppercase tracking-widest font-bold">
              Pending
            </span>
            <div className="flex items-baseline justify-between mt-auto">
              <span className="font-display text-3xl font-black text-amber-400 tracking-tight">
                {stats.pending}
              </span>
              <span className="text-[10px] text-amber-400 font-mono font-bold uppercase">In Queue</span>
            </div>
          </div>

          <div className="glass-panel rounded-2xl p-5 border border-slate-800/40 flex flex-col justify-between h-32 relative group overflow-hidden">
            <div className="absolute top-0 right-0 w-16 h-16 bg-red-500/5 rounded-full blur-xl group-hover:bg-red-500/10 transition-colors pointer-events-none"></div>
            <span className="text-[10px] text-slate-500 uppercase tracking-widest font-bold">
              Rejected
            </span>
            <div className="flex items-baseline justify-between mt-auto">
              <span className="font-display text-3xl font-black text-slate-400 tracking-tight">
                {stats.rejected}
              </span>
              <span className="text-[10px] text-slate-500 font-mono font-bold uppercase">False Pos</span>
            </div>
          </div>

          <div className="col-span-2 lg:col-span-1 glass-panel rounded-2xl p-5 border border-emerald-500/20 flex flex-col justify-between h-32 relative group overflow-hidden">
            <div className="absolute -top-4 -right-4 w-20 h-20 bg-emerald-500/10 rounded-full blur-2xl pointer-events-none"></div>
            <span className="text-[10px] text-emerald-400 uppercase tracking-widest font-bold flex items-center gap-1.5">
              <Sparkles size={12} className="animate-pulse" /> Rewards Credits
            </span>
            <div className="flex items-baseline justify-between mt-auto">
              <span className="font-display text-3xl font-black text-emerald-300 tracking-tight">
                {stats.rewards.toLocaleString()}
              </span>
              <span className="text-xs text-slate-400 font-mono font-semibold">Cr</span>
            </div>
          </div>
        </section>

        {/* Bento Grid Analytics */}
        <section className="grid grid-cols-1 md:grid-cols-3 gap-6">
          
          {/* Box 1: Safety Score Circular Index */}
          <div className="glass-panel rounded-2xl p-6 border border-slate-800/40 flex flex-col justify-between relative overflow-hidden group min-h-[340px]">
            <div className="absolute top-0 right-0 w-24 h-24 bg-blue-500/5 rounded-full blur-2xl group-hover:bg-blue-500/10 transition-colors pointer-events-none"></div>
            
            <div className="flex justify-between items-start">
              <div>
                <h3 className="font-display text-base font-bold text-white mb-0.5">
                  Precinct Safety Score
                </h3>
                <p className="text-[11px] text-slate-500">Based on submitted dashboard footage</p>
              </div>
              <span className="text-xs bg-emerald-500/10 text-emerald-400 px-2 py-0.5 rounded font-bold">
                Excellent
              </span>
            </div>

            {/* Circular Gauge */}
            <div className="my-6 flex justify-center items-center relative h-36">
              <div className="absolute inset-0 rounded-full border border-slate-800/40 w-32 h-32 m-auto"></div>
              {/* Outer Gauge ring */}
              <svg className="w-32 h-32 m-auto transform -rotate-90 absolute inset-0" viewBox="0 0 100 100">
                <circle cx="50" cy="50" fill="none" r="42" stroke="rgba(30, 41, 59, 0.4)" strokeWidth="6"></circle>
                <circle cx="50" cy="50" fill="none" r="42" stroke="#10b981" strokeWidth="6" strokeDasharray="264" strokeDashoffset="16"></circle>
              </svg>
              
              <div className="flex flex-col items-center justify-center relative z-10">
                <span className="text-3xl font-black text-slate-100 font-display">94<span className="text-lg text-slate-500">%</span></span>
                <span className="text-[9px] text-slate-500 uppercase tracking-widest font-bold mt-1">Precinct Index</span>
              </div>
            </div>

            <div className="text-xs text-slate-400 flex items-center justify-between border-t border-slate-850/50 pt-4">
              <span className="flex items-center gap-1"><MapPin size={12} className="text-slate-500" /> Safe Segment:</span>
              <span className="font-mono text-slate-200 font-bold">Arterial Expressway</span>
            </div>
          </div>

          {/* Box 2: Violation Distribution custom CSS bars */}
          <div className="glass-panel rounded-2xl p-6 border border-slate-800/40 flex flex-col justify-between relative overflow-hidden group min-h-[340px]">
            <div>
              <h3 className="font-display text-base font-bold text-white mb-0.5">
                Violation Distribution
              </h3>
              <p className="text-[11px] text-slate-500">Breakdown of reported incident types</p>
            </div>

            <div className="space-y-4 my-4">
              {/* Item 1: Helmet */}
              <div className="space-y-1.5">
                <div className="flex justify-between items-center text-xs font-medium">
                  <span className="text-slate-300">Helmet Violations</span>
                  <span className="text-slate-400 font-mono">42%</span>
                </div>
                <div className="w-full bg-slate-900 rounded-full h-2 overflow-hidden border border-slate-800/40">
                  <div className="bg-blue-400 h-full rounded-full" style={{ width: '42%' }}></div>
                </div>
              </div>

              {/* Item 2: Crossing Divider */}
              <div className="space-y-1.5">
                <div className="flex justify-between items-center text-xs font-medium">
                  <span className="text-slate-300">Crossing Divider (Double Yellow)</span>
                  <span className="text-slate-400 font-mono">28%</span>
                </div>
                <div className="w-full bg-slate-900 rounded-full h-2 overflow-hidden border border-slate-800/40">
                  <div className="bg-teal-400 h-full rounded-full" style={{ width: '28%' }}></div>
                </div>
              </div>

              {/* Item 3: Triple Riding */}
              <div className="space-y-1.5">
                <div className="flex justify-between items-center text-xs font-medium">
                  <span className="text-slate-300">Triple Riding</span>
                  <span className="text-slate-400 font-mono">18%</span>
                </div>
                <div className="w-full bg-slate-900 rounded-full h-2 overflow-hidden border border-slate-800/40">
                  <div className="bg-amber-400 h-full rounded-full" style={{ width: '18%' }}></div>
                </div>
              </div>

              {/* Item 4: Potholes */}
              <div className="space-y-1.5">
                <div className="flex justify-between items-center text-xs font-medium">
                  <span className="text-slate-300">Pothole Mapping</span>
                  <span className="text-slate-400 font-mono">12%</span>
                </div>
                <div className="w-full bg-slate-900 rounded-full h-2 overflow-hidden border border-slate-800/40">
                  <div className="bg-red-400 h-full rounded-full" style={{ width: '12%' }}></div>
                </div>
              </div>
            </div>

            <p className="text-[10px] text-slate-500 leading-normal border-t border-slate-850/50 pt-4">
              AI accuracy parameters optimized for Helmet detection (94.1% true positive rating in current sector).
            </p>
          </div>

          {/* Box 3: Rewards Earning over time custom area chart */}
          <div className="glass-panel rounded-2xl p-6 border border-slate-800/40 flex flex-col justify-between relative overflow-hidden group min-h-[340px]">
            <div className="flex justify-between items-start">
              <div>
                <h3 className="font-display text-base font-bold text-white mb-0.5">
                  Rewards Over Time
                </h3>
                <p className="text-[11px] text-slate-500">Earnings curve for verified bounty logs</p>
              </div>

              <div className="flex bg-slate-900 p-0.5 rounded-lg border border-slate-800/50 text-[9px] font-bold">
                {['WEEK', 'MONTH', 'YEAR'].map((tab) => (
                  <button
                    key={tab}
                    onClick={() => setActiveTab(tab as 'WEEK' | 'MONTH' | 'YEAR')}
                    className={`px-2 py-1 rounded-md transition-all cursor-pointer ${
                      activeTab === tab ? 'bg-blue-500/25 text-blue-300' : 'text-slate-500 hover:text-slate-300'
                    }`}
                  >
                    {tab}
                  </button>
                ))}
              </div>
            </div>

            {/* SVG Area Line Chart */}
            <div className="h-36 w-full relative my-4">
              <svg className="w-full h-full" viewBox="0 0 600 150" preserveAspectRatio="none">
                <defs>
                  <linearGradient id="glow-grad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="rgba(59, 130, 246, 0.4)"></stop>
                    <stop offset="100%" stopColor="rgba(59, 130, 246, 0.0)"></stop>
                  </linearGradient>
                </defs>
                {/* Horizontal Guide Lines */}
                <line x1="0" y1="37.5" x2="600" y2="37.5" stroke="rgba(30, 41, 59, 0.2)" strokeWidth="1" />
                <line x1="0" y1="75" x2="600" y2="75" stroke="rgba(30, 41, 59, 0.2)" strokeWidth="1" />
                <line x1="0" y1="112.5" x2="600" y2="112.5" stroke="rgba(30, 41, 59, 0.2)" strokeWidth="1" />

                {/* Fill area */}
                <polygon points={chartData.fillPoints} fill="url(#glow-grad)" />
                {/* Line path */}
                <polyline points={chartData.points} fill="none" stroke="#4d8eff" strokeWidth="3.5" strokeLinecap="round" />
              </svg>

              {/* Chart labels overlay */}
              <div className="absolute bottom-0 left-0 right-0 flex justify-between px-1 text-[9px] font-mono font-medium text-slate-500">
                {chartData.labels.map((label, idx) => (
                  <span key={idx}>{label}</span>
                ))}
              </div>
            </div>

            <div className="flex justify-between items-center border-t border-slate-850/50 pt-4 text-xs font-semibold text-emerald-400">
              <span className="flex items-center gap-1"><TrendingUp size={14} /> Earning rate:</span>
              <span>+18.4% MoM</span>
            </div>
          </div>
        </section>

        {/* Contribution Funnel & Milestones & Upgrade */}
        <section className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Contribution Funnel */}
          <div className="glass-panel rounded-2xl p-6 border border-slate-800/40 space-y-6">
            <div>
              <h3 className="font-display text-base font-bold text-white mb-0.5">
                Contribution Funnel
              </h3>
              <p className="text-[11px] text-slate-500">Your flow of dashcam reports conversion</p>
            </div>

            <div className="space-y-4">
              {/* Phase 1 */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-lg bg-blue-500/10 flex items-center justify-center text-xs text-blue-300 font-bold border border-blue-500/20">
                    1
                  </div>
                  <div>
                    <h4 className="text-xs text-slate-200 font-semibold">Uploaded</h4>
                    <p className="text-[10px] text-slate-500">Raw videos submitted</p>
                  </div>
                </div>
                <div className="text-right font-mono text-xs">
                  <span className="text-slate-200 font-bold">185</span>
                  <span className="text-slate-500 ml-1.5 text-[10px]">100%</span>
                </div>
              </div>

              {/* Phase 2 */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-lg bg-teal-500/10 flex items-center justify-center text-xs text-teal-300 font-bold border border-teal-500/20">
                    2
                  </div>
                  <div>
                    <h4 className="text-xs text-slate-200 font-semibold">Analyzed</h4>
                    <p className="text-[10px] text-slate-500">Processed by AI pipeline</p>
                  </div>
                </div>
                <div className="text-right font-mono text-xs">
                  <span className="text-slate-200 font-bold">164</span>
                  <span className="text-slate-500 ml-1.5 text-[10px]">88.6%</span>
                </div>
              </div>

              {/* Phase 3 */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-lg bg-emerald-500/10 flex items-center justify-center text-xs text-emerald-300 font-bold border border-emerald-500/20">
                    3
                  </div>
                  <div>
                    <h4 className="text-xs text-slate-200 font-semibold">Verified</h4>
                    <p className="text-[10px] text-slate-500">Flagged incidents approved</p>
                  </div>
                </div>
                <div className="text-right font-mono text-xs">
                  <span className="text-slate-200 font-bold">128</span>
                  <span className="text-slate-500 ml-1.5 text-[10px]">69.1%</span>
                </div>
              </div>
            </div>
          </div>

          {/* Milestones */}
          <div className="glass-panel rounded-2xl p-6 border border-slate-800/40 space-y-6">
            <div>
              <h3 className="font-display text-base font-bold text-white mb-0.5">
                Milestone Progress
              </h3>
              <p className="text-[11px] text-slate-500">Achievements and sector prestige levels</p>
            </div>

            <div className="space-y-4">
              {/* Badge 1 */}
              <div className="flex gap-3 items-start">
                <div className="w-9 h-9 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-400 shrink-0">
                  <Award size={18} />
                </div>
                <div>
                  <h4 className="text-xs text-slate-200 font-bold">Veteran Reporter</h4>
                  <p className="text-[10px] text-slate-500">Completed 100 verified reports. Prestige Level +2.</p>
                </div>
              </div>

              {/* Badge 2 */}
              <div className="flex gap-3 items-start">
                <div className="w-9 h-9 rounded-xl bg-blue-500/10 border border-blue-500/30 flex items-center justify-center text-blue-300 shrink-0">
                  <Flame size={18} />
                </div>
                <div>
                  <h4 className="text-xs text-slate-200 font-bold">Pothole Hunter</h4>
                  <p className="text-[10px] text-slate-500">Map and log 25 verified road hazards.</p>
                </div>
              </div>

              {/* Badge 3 */}
              <div className="flex gap-3 items-start">
                <div className="w-9 h-9 rounded-xl bg-slate-800/60 border border-slate-700/40 flex items-center justify-center text-slate-400 shrink-0">
                  <Clock size={18} />
                </div>
                <div>
                  <h4 className="text-xs text-slate-400 font-bold">Night Watcher</h4>
                  <p className="text-[10px] text-slate-500">Analyze 10 footage logs recorded between 00:00 - 05:00.</p>
                </div>
              </div>
            </div>
          </div>

          {/* Upgrade to Pro Box */}
          <div className="glass-panel rounded-2xl p-6 border border-blue-500/20 relative overflow-hidden flex flex-col justify-between group min-h-[220px]">
            <div className="absolute -top-4 -right-4 w-32 h-32 bg-blue-500/10 rounded-full blur-2xl group-hover:bg-blue-500/20 transition-colors pointer-events-none"></div>
            
            <div className="space-y-3">
              <div className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md bg-blue-500/10 border border-blue-500/30 text-blue-300 text-[9px] font-bold uppercase tracking-wider">
                PARA PRO
              </div>
              <h3 className="font-display text-lg font-black text-white tracking-tight">
                Upgrade to PARA Pro
              </h3>
              <p className="text-slate-400 text-xs leading-relaxed">
                Unlock unlimited parallel uploads, higher AI frame scanning rates, and priority precinct verification queuing.
              </p>
            </div>

            <button 
              onClick={() => setIsPro(!isPro)}
              className={`w-full py-3 mt-4 rounded-xl text-xs font-bold transition-all duration-300 flex items-center justify-center gap-2 cursor-pointer border ${
                isPro 
                  ? 'bg-emerald-500/15 border-emerald-500/40 text-emerald-300' 
                  : 'bg-blue-500 hover:bg-blue-400 text-white border-blue-400 hover:shadow-[0_0_20px_rgba(59,130,246,0.25)] hover:scale-[1.02]'
              }`}
            >
              {isPro ? (
                <>
                  <ShieldCheck size={14} />
                  Pro Membership Active
                </>
              ) : (
                <>
                  Upgrade Now
                  <ArrowUpRight size={14} />
                </>
              )}
            </button>
          </div>
        </section>

        {/* Recent Activity Feed */}
        <section className="glass-panel rounded-2xl p-6 border border-slate-800/40 space-y-4">
          <div className="flex justify-between items-center">
            <div>
              <h3 className="font-display text-base font-bold text-white mb-0.5">
                Recent Verification Activity
              </h3>
              <p className="text-[11px] text-slate-500">Live logs from your contribution portal</p>
            </div>
            <button 
              onClick={() => setView('CONSOLE')}
              className="text-xs text-blue-300 hover:text-blue-400 flex items-center gap-1 cursor-pointer font-semibold"
            >
              Go to Console <ChevronRight size={14} />
            </button>
          </div>

          <div className="space-y-1">
            {/* Log 1 */}
            <div className="p-3.5 rounded-xl bg-slate-900/30 hover:bg-slate-900/60 border border-transparent hover:border-slate-850 flex items-center justify-between text-xs transition-all">
              <div className="flex items-center gap-3">
                <CheckCircle className="text-emerald-400" size={16} />
                <div>
                  <span className="text-slate-200 font-semibold">Incident #VIO-892-001 Approved</span>
                  <p className="text-[10px] text-slate-500 mt-0.5">Double Yellow Divider Crossing • Plate ABC-1234 • +120 Cr</p>
                </div>
              </div>
              <span className="font-mono text-[10px] text-slate-500">14:02:11</span>
            </div>

            {/* Log 2 */}
            <div className="p-3.5 rounded-xl bg-slate-900/30 hover:bg-slate-900/60 border border-transparent hover:border-slate-850 flex items-center justify-between text-xs transition-all">
              <div className="flex items-center gap-3">
                <CheckCircle className="text-emerald-400" size={16} />
                <div>
                  <span className="text-slate-200 font-semibold">Incident #VIO-892-002 Approved</span>
                  <p className="text-[10px] text-slate-500 mt-0.5">Helmet Violation • Plate XYZ-9876 • +150 Cr</p>
                </div>
              </div>
              <span className="font-mono text-[10px] text-slate-500">14:15:33</span>
            </div>

            {/* Log 3 */}
            <div className="p-3.5 rounded-xl bg-slate-900/30 hover:bg-slate-900/60 border border-transparent hover:border-slate-850 flex items-center justify-between text-xs transition-all">
              <div className="flex items-center gap-3">
                <TrendingUp className="text-blue-300" size={16} />
                <div>
                  <span className="text-slate-200 font-semibold">Dashcam Video uploaded</span>
                  <p className="text-[10px] text-slate-500 mt-0.5">dashcam_0842.mp4 (45.8 MB) analyzed successfully</p>
                </div>
              </div>
              <span className="font-mono text-[10px] text-slate-500">10:45 AM</span>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
