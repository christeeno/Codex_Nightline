import React from 'react';
import { ViewState } from '../types';
import { 
  LayoutDashboard, 
  Map, 
  FileCode, 
  AlertTriangle, 
  HelpCircle, 
  LogOut, 
  FileSpreadsheet, 
  ShieldCheck 
} from 'lucide-react';

interface SidebarProps {
  currentView: ViewState;
  setView: (view: ViewState) => void;
  onEmergencyTrigger?: () => void;
}

export default function Sidebar({ currentView, setView, onEmergencyTrigger }: SidebarProps) {
  return (
    <aside className="bg-slate-950/90 backdrop-blur-md border-r border-slate-800/40 w-64 shrink-0 flex flex-col h-screen py-8 px-4 z-50">
      {/* Brand Header */}
      <div className="mb-10 px-4">
        <button 
          onClick={() => setView('LANDING')}
          className="font-display text-2xl font-bold tracking-tighter text-blue-300 hover:opacity-95 text-left cursor-pointer"
        >
          PARA Console
        </button>
        <div className="flex items-center gap-2 mt-1.5 text-slate-500 text-xs">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
          <span>V3.2 Active</span>
        </div>
      </div>

      {/* Nav Section */}
      <nav className="flex-1 space-y-1">
        <button
          onClick={() => setView('CITIZEN_DASHBOARD')}
          className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all duration-200 cursor-pointer ${
            currentView === 'CITIZEN_DASHBOARD'
              ? 'bg-blue-500/10 text-blue-300 border-r-4 border-blue-400'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/40 hover:translate-x-1'
          }`}
        >
          <LayoutDashboard size={18} />
          <span>Overview</span>
        </button>

        <button
          onClick={() => setView('CITIZEN_DASHBOARD')}
          className="w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium text-slate-400 hover:text-slate-200 hover:bg-slate-900/40 hover:translate-x-1 transition-all duration-200 cursor-pointer text-left"
        >
          <Map size={18} />
          <span>Live Maps</span>
        </button>

        <button
          onClick={() => setView('CONSOLE')}
          className="w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium text-slate-400 hover:text-slate-200 hover:bg-slate-900/40 hover:translate-x-1 transition-all duration-200 cursor-pointer text-left"
        >
          <FileCode size={18} />
          <span>Evidence Log</span>
        </button>

        <button
          onClick={() => setView('CONSOLE')}
          className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all duration-200 cursor-pointer ${
            currentView === 'CONSOLE'
              ? 'bg-blue-500/10 text-blue-300 border-r-4 border-blue-400'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/40 hover:translate-x-1'
          }`}
        >
          <FileSpreadsheet size={18} />
          <span>Reports</span>
        </button>

        <button
          onClick={() => setView('CITIZEN_DASHBOARD')}
          className="w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium text-slate-400 hover:text-slate-200 hover:bg-slate-900/40 hover:translate-x-1 transition-all duration-200 cursor-pointer text-left"
        >
          <ShieldCheck size={18} />
          <span>Accountability</span>
        </button>
      </nav>

      {/* Footer CTA & Actions */}
      <div className="mt-auto px-2 space-y-4 border-t border-slate-800/40 pt-6">
        <button 
          onClick={onEmergencyTrigger}
          className="w-full py-3 px-4 bg-red-950/80 hover:bg-red-900/80 text-red-300 rounded-xl font-medium text-xs flex items-center justify-center gap-2 border border-red-900/40 transition-all duration-300 hover:shadow-[0_0_15px_rgba(239,68,68,0.15)] cursor-pointer"
        >
          <AlertTriangle size={14} className="animate-pulse" />
          Emergency Report
        </button>
        
        <div className="space-y-1">
          <button className="w-full flex items-center gap-3 px-4 py-2 text-slate-500 hover:text-slate-300 text-xs transition-colors cursor-pointer text-left">
            <HelpCircle size={16} />
            <span>Help</span>
          </button>
          <button 
            onClick={() => setView('LANDING')}
            className="w-full flex items-center gap-3 px-4 py-2 text-slate-500 hover:text-slate-300 text-xs transition-colors cursor-pointer text-left"
          >
            <LogOut size={16} />
            <span>Sign Out</span>
          </button>
        </div>
      </div>
    </aside>
  );
}
