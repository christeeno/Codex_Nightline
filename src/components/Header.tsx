import React from 'react';
import { ViewState } from '../types';
import { Bell, Settings, Upload } from 'lucide-react';

interface HeaderProps {
  currentView: ViewState;
  setView: (view: ViewState) => void;
}

export default function Header({ currentView, setView }: HeaderProps) {
  return (
    <nav className="fixed top-0 w-full z-50 flex justify-between items-center px-6 md:px-16 h-20 bg-slate-950/80 backdrop-blur-xl border-b border-slate-800/50 shadow-sm transition-all duration-300">
      <div className="flex items-center gap-12">
        <button 
          onClick={() => setView('LANDING')} 
          className="font-display text-3xl font-bold tracking-tighter text-blue-300 cursor-pointer hover:opacity-90 transition-opacity"
        >
          PARA AI
        </button>
        <div className="hidden md:flex items-center gap-6 h-full text-sm">
          <button 
            onClick={() => setView('CITIZEN_DASHBOARD')}
            className={`font-medium transition-colors hover:text-blue-400 cursor-pointer ${
              currentView === 'CITIZEN_DASHBOARD' ? 'text-blue-300 border-b-2 border-blue-400 pb-1' : 'text-slate-400'
            }`}
          >
            Dashboard
          </button>
          <button 
            onClick={() => setView('CONSOLE')}
            className={`font-medium transition-colors hover:text-blue-400 cursor-pointer ${
              currentView === 'CONSOLE' ? 'text-blue-300 border-b-2 border-blue-400 pb-1' : 'text-slate-400'
            }`}
          >
            Incidents
          </button>
          <button 
            onClick={() => setView('CITIZEN_DASHBOARD')}
            className="text-slate-400 font-medium transition-colors hover:text-blue-400 cursor-pointer"
          >
            Analytics
          </button>
          <button 
            onClick={() => setView('LANDING')}
            className="text-slate-400 font-medium transition-colors hover:text-blue-400 cursor-pointer"
          >
            Fleet
          </button>
        </div>
      </div>
      
      <div className="flex items-center gap-6">
        <button 
          onClick={() => setView('UPLOAD')}
          className="hidden md:flex items-center gap-2 bg-blue-500/10 hover:bg-blue-500/20 text-blue-300 font-medium px-4 py-2 rounded-lg border border-blue-500/30 transition-all duration-300 hover:shadow-[0_0_15px_rgba(59,130,246,0.15)] cursor-pointer"
        >
          <Upload size={16} />
          Upload Footage
        </button>
        
        <div className="flex items-center gap-4">
          <button className="p-2 text-slate-400 hover:text-blue-300 hover:bg-slate-800/50 rounded-full transition-colors cursor-pointer relative">
            <Bell size={20} />
            <span className="absolute top-1.5 right-1.5 w-2.5 h-2.5 bg-emerald-500 rounded-full border-2 border-slate-950 animate-pulse"></span>
          </button>
          <button className="p-2 text-slate-400 hover:text-blue-300 hover:bg-slate-800/50 rounded-full transition-colors cursor-pointer">
            <Settings size={20} />
          </button>
          
          <div 
            onClick={() => setView('CITIZEN_DASHBOARD')}
            className="w-10 h-10 rounded-full overflow-hidden border-2 border-blue-400/50 cursor-pointer hover:border-blue-400 transition-colors"
          >
            <img 
              alt="User profile avatar" 
              className="w-full h-full object-cover" 
              src="https://lh3.googleusercontent.com/aida-public/AB6AXuCCwadGntoKIFFfNgq2WnLzfpj9sXzQnQ7YFGnPz_ZY9P9G1fqVg45a7sno1w37gb0SM2zFl2zlFvGvkweD65wjM0kwAa7yW3Tv3nRtBoc5ZpdWt0NOg50mKEUitAW6txGRVcF1EpZuMFjstf1W6sgwp-GoskYD-NDfaqCMGSz7_qZvSJba9mIMnybWLd900gmvCpsiWX5jM9JPgSXxWKe5GPlqFnO1JL1Y_O78xaQZp7dIPzPevfifSNmGcTDq7m63ZsZjAmne2OU"
            />
          </div>
        </div>
      </div>
    </nav>
  );
}
