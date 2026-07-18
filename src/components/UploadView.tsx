import React, { useState, useEffect } from 'react';
import { ViewState } from '../types';
import { UploadCloud, PlayCircle, X, BrainCircuit } from 'lucide-react';

interface UploadViewProps {
  setView: (view: ViewState) => void;
  setUploadedFile: (file: { name: string; size: string }) => void;
}

export default function UploadView({ setView, setUploadedFile }: UploadViewProps) {
  const [isDragActive, setIsDragActive] = useState(false);
  const [file, setFile] = useState<{ name: string; size: string } | null>(null);
  const [progress, setProgress] = useState(0);
  const [uploadSpeed, setUploadSpeed] = useState('0.0 MB/s');

  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (file && progress < 100) {
      interval = setInterval(() => {
        setProgress((prev) => {
          const next = prev + Math.floor(Math.random() * 15) + 5;
          const currentSpeed = (Math.random() * 0.8 + 0.8).toFixed(1);
          setUploadSpeed(`${currentSpeed} MB/s`);
          if (next >= 100) {
            clearInterval(interval);
            return 100;
          }
          return next;
        });
      }, 600);
    }
    return () => clearInterval(interval);
  }, [file, progress]);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setIsDragActive(true);
    } else if (e.type === 'dragleave') {
      setIsDragActive(false);
    }
  };

  const processFile = (fileName: string, fileSize: number) => {
    const formattedSize = (fileSize / (1024 * 1024)).toFixed(1) + ' MB';
    const newFile = { name: fileName, size: formattedSize };
    setFile(newFile);
    setProgress(0);
    setUploadedFile(newFile);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const droppedFile = e.dataTransfer.files[0];
      processFile(droppedFile.name, droppedFile.size);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0];
      processFile(selectedFile.name, selectedFile.size);
    }
  };

  const triggerUpload = () => {
    const randomNum = Math.floor(Math.random() * 9000) + 1000;
    processFile(`dashcam_${randomNum}.mp4`, 48024888); // ~45.8 MB
  };

  const cancelUpload = () => {
    setFile(null);
    setProgress(0);
  };

  return (
    <div className="pt-28 px-4 md:px-16 pb-20 max-w-7xl mx-auto flex flex-col items-center justify-center min-h-[calc(100vh-80px)]">
      <div className="w-full max-w-3xl flex flex-col gap-12">
        {/* Header Section */}
        <div className="text-center space-y-3">
          <h1 className="font-display text-3xl md:text-4xl font-bold text-blue-300 tracking-tight">
            Upload Dashcam Footage
          </h1>
          <p className="text-slate-400 font-sans text-sm md:text-base">
            Drag and drop your MP4, MOV, or AVI files here to begin AI analysis.
          </p>
        </div>

        {/* Drag & Drop Zone */}
        <div
          onDragEnter={handleDrag}
          onDragOver={handleDrag}
          onDragLeave={handleDrag}
          onDrop={handleDrop}
          onClick={triggerUpload}
          className={`glass-panel w-full rounded-2xl border-2 border-dashed flex flex-col items-center justify-center py-16 px-8 cursor-pointer transition-all duration-300 group ${
            isDragActive 
              ? 'border-blue-400 bg-blue-500/5 shadow-[0_0_30px_rgba(59,130,246,0.1)]' 
              : 'border-slate-800 hover:border-blue-500/50 hover:bg-slate-900/10'
          }`}
        >
          <div className="w-16 h-16 rounded-full bg-slate-800/80 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300">
            <UploadCloud className="text-blue-300" size={32} />
          </div>
          
          <h3 className="font-display text-lg md:text-xl font-bold text-slate-100 mb-1.5 text-center">
            Select a file or drag and drop
          </h3>
          <p className="font-display text-[10px] text-slate-400 uppercase tracking-widest mb-6">
            MP4, MOV, AVI UP TO 2GB
          </p>
          
          <button className="px-5 py-2.5 bg-slate-900 text-blue-300 border border-slate-700/80 rounded-lg font-medium text-xs hover:bg-slate-800 transition-colors pointer-events-none">
            Browse Files
          </button>
          
          <input 
            type="file" 
            className="hidden" 
            accept=".mp4,.mov,.avi" 
            onChange={handleFileChange} 
          />
        </div>

        {/* Upload Progress Card (Interactive State) */}
        {file && (
          <div className="glass-panel w-full rounded-2xl p-6 flex flex-col md:flex-row gap-6 items-start shadow-2xl border border-slate-800/40 relative overflow-hidden">
            <div className="absolute top-0 left-0 h-[2px] bg-blue-500 transition-all duration-300" style={{ width: `${progress}%` }}></div>
            
            {/* Thumbnail */}
            <div className="w-full md:w-48 h-32 rounded-xl overflow-hidden flex-shrink-0 relative bg-slate-900 border border-slate-800/40">
              <img 
                alt="Video thumbnail" 
                className="w-full h-full object-cover opacity-80" 
                src="https://lh3.googleusercontent.com/aida-public/AB6AXuABaV0vPFayoIT4mw_Nlo-bYGKmZnfv4W353e82aCfjCVgTLwOuyo_7HIxUm9j5spSEK6BvwXQJvNIN6w1x_ppeWKNZYmlnRW6bzx79spyVX8v_cDDiyajMOBu_svun8NamTins-TsGg7WGEfp228IexYC9Rh-L5kQnWAp5ZlQ3Ef1Ip7EPjdf46gzLcXPfhH3SQJ3maCcoxov7gqq1KyPN7TR5npOY0AxbHxDZ6BEtCE9tS9KnVwzKftHv2ceI9nv3YVv-P6__fFI" 
              />
              <div className="absolute inset-0 flex items-center justify-center bg-slate-950/40">
                <PlayCircle className="text-blue-300" size={32} />
              </div>
              <div className="absolute bottom-2 right-2 bg-slate-950/90 px-1.5 py-0.5 rounded text-[10px] font-mono text-slate-200 backdrop-blur-sm">
                02:45
              </div>
            </div>

            {/* Details & Progress */}
            <div className="flex-grow w-full flex flex-col justify-between h-32 py-1">
              <div className="flex justify-between items-start">
                <div>
                  <h4 className="text-slate-100 font-medium truncate max-w-[200px] md:max-w-[340px]">
                    {file.name}
                  </h4>
                  <p className="text-slate-400 text-xs mt-1">
                    {file.size} • {progress < 100 ? 'Uploading...' : 'Complete'}
                  </p>
                </div>
                <button 
                  onClick={cancelUpload}
                  className="text-slate-400 hover:text-red-400 transition-colors p-1.5 hover:bg-slate-800/50 rounded-full cursor-pointer"
                >
                  <X size={16} />
                </button>
              </div>

              <div className="space-y-2 w-full mt-auto">
                <div className="flex justify-between text-xs font-medium">
                  <span className="text-blue-300">{progress}%</span>
                  <span className="text-slate-400">{progress < 100 ? uploadSpeed : 'Done'}</span>
                </div>
                <div className="w-full bg-slate-900 rounded-full h-2 overflow-hidden border border-slate-800/40">
                  <div 
                    className="bg-blue-400 h-full rounded-full transition-all duration-300 progress-bar-stripes" 
                    style={{ width: `${progress}%` }}
                  ></div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Action Area */}
        <div className="flex justify-end pt-4">
          <button
            onClick={() => setView('PROCESSING')}
            disabled={!file || progress < 100}
            className={`px-8 py-3 rounded-xl font-display text-sm font-medium border flex items-center gap-2 transition-all duration-300 cursor-pointer ${
              file && progress === 100
                ? 'bg-blue-500 hover:bg-blue-400 text-white border-blue-400 hover:shadow-[0_0_20px_rgba(59,130,246,0.3)] hover:scale-[1.02]'
                : 'bg-slate-900 text-slate-500 border-slate-800/50 cursor-not-allowed opacity-55'
            }`}
          >
            <BrainCircuit size={16} />
            Analyze Footage
          </button>
        </div>
      </div>
    </div>
  );
}
