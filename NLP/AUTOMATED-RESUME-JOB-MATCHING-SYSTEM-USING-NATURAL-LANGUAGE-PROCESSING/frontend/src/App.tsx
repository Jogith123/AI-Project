import { useState, useRef } from 'react';
import {
  Upload, FileText, AlertCircle, Loader2, Download,
  ThumbsUp, ThumbsDown, Sparkles, ChevronRight,
  Briefcase, X, Zap, BarChart3
} from 'lucide-react';
import axios from 'axios';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

interface MatchResult {
  candidate_name: string;
  match_score: number;
  extracted_skills: string[];
  feedback?: 'up' | 'down';
}

function App() {
  const [files, setFiles] = useState<File[]>([]);
  const [jobDescription, setJobDescription] = useState('');
  const [results, setResults] = useState<MatchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) setFiles(Array.from(e.target.files));
  };
  const removeFile = (idx: number) => setFiles(files.filter((_, i) => i !== idx));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (files.length === 0 || !jobDescription) {
      setError('Please provide both resumes and a job description.');
      return;
    }
    setError(null);
    setLoading(true);
    const formData = new FormData();
    formData.append('job_description', jobDescription);
    files.forEach(file => formData.append('files', file));
    try {
      const res = await axios.post<MatchResult[]>('http://localhost:8000/match', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setResults(res.data);
    } catch {
      setError('Failed to process resumes. Ensure the backend AI engine is running.');
    } finally {
      setLoading(false);
    }
  };

  const handleExportCSV = () => {
    if (results.length === 0) return;
    const headers = ['Candidate Name', 'Match Score (%)', 'Extracted Skills', 'Feedback'];
    const rows = results.map(r => [
      `"${r.candidate_name.replace(/"/g, '""')}"`, r.match_score,
      `"${r.extracted_skills.join(', ')}"`, r.feedback || 'None'
    ]);
    const csv = [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = 'matched_candidates.csv';
    document.body.appendChild(a); a.click(); document.body.removeChild(a);
  };

  const handleFeedback = (index: number, type: 'up' | 'down') => {
    setResults(prev => prev.map((r, i) =>
      i === index ? { ...r, feedback: r.feedback === type ? undefined : type } : r
    ));
  };

  const getScoreColor = (score: number) => {
    if (score >= 75) return 'text-emerald-400';
    if (score >= 50) return 'text-amber-400';
    return 'text-red-400';
  };

  const getScoreBg = (score: number) => {
    if (score >= 75) return 'bg-emerald-500/10 border-emerald-500/20';
    if (score >= 50) return 'bg-amber-500/10 border-amber-500/20';
    return 'bg-red-500/10 border-red-500/20';
  };

  const avgScore = results.length > 0
    ? (results.reduce((sum, r) => sum + r.match_score, 0) / results.length).toFixed(1) : '0';
  const topScore = results.length > 0 ? results[0]?.match_score : 0;

  return (
    <div className="h-screen flex flex-col bg-background text-gray-200 overflow-hidden">

      {/* Header */}
      <header className="shrink-0 glass-panel border-b border-white/5 z-50">
        <div className="w-full px-6 h-14 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-emerald-400 to-emerald-600 flex items-center justify-center shadow-lg shadow-emerald-500/20">
              <Sparkles className="w-4 h-4 text-white" />
            </div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-bold tracking-tight text-white">
                Neural<span className="text-emerald-400">Match</span>
              </h1>
              <span className="text-[10px] font-mono font-semibold px-1.5 py-0.5 rounded-md bg-emerald-950 text-emerald-400 border border-emerald-900/50">v2.0</span>
            </div>
          </div>

          {results.length > 0 && (
            <div className="hidden md:flex items-center gap-6 text-xs animate-fade-in">
              <div className="flex items-center gap-2 text-gray-400">
                <BarChart3 className="w-3.5 h-3.5 text-amber-400" />
                <span className="font-mono font-semibold text-white">{avgScore}%</span>
                <span>Avg Score</span>
              </div>
              <div className="w-px h-4 bg-white/10" />
              <div className="flex items-center gap-2 text-gray-400">
                <Zap className="w-3.5 h-3.5 text-emerald-400" />
                <span className="font-mono font-semibold text-white">{topScore}%</span>
                <span>Top Match</span>
              </div>
            </div>
          )}
        </div>
      </header>

      {/* Main Layout */}
      <div className="flex-1 flex min-h-0 overflow-hidden">

        {/* Left Sidebar */}
        <aside className="w-[380px] xl:w-[420px] shrink-0 border-r border-white/5 flex flex-col bg-[#0d0d0f]/80 overflow-hidden">
          <div className="px-5 pt-5 pb-4 border-b border-white/5">
            <h2 className="text-sm font-semibold text-white tracking-wide flex items-center gap-2">
              <Zap className="w-4 h-4 text-emerald-400" /> Configure Analysis
            </h2>
            <p className="text-xs text-gray-500 mt-1">Set up your job profile and upload resumes</p>
          </div>
          <form onSubmit={handleSubmit} className="flex-1 flex flex-col min-h-0 overflow-hidden">
            <div className="flex-1 overflow-y-auto px-5 py-4 space-y-5">
              <div className="space-y-2">
                <label className="text-xs font-semibold tracking-wider text-gray-400 uppercase flex items-center gap-1.5">
                  <Briefcase className="w-3.5 h-3.5 text-emerald-400" /> Job Description
                </label>
                <textarea
                  value={jobDescription} onChange={(e) => setJobDescription(e.target.value)}
                  placeholder="Paste the job description, requirements, and responsibilities..."
                  className="w-full h-[180px] xl:h-[220px] bg-white/[0.03] border border-white/8 rounded-xl p-4 text-sm text-gray-200 placeholder-gray-600 focus:ring-1 focus:ring-emerald-500/40 focus:border-emerald-500/40 outline-none transition-all resize-none leading-relaxed"
                />
              </div>
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <label className="text-xs font-semibold tracking-wider text-gray-400 uppercase flex items-center gap-1.5">
                    <FileText className="w-3.5 h-3.5 text-emerald-400" /> Resumes
                  </label>
                  <span className="text-[10px] text-gray-500 font-mono">{files.length} file{files.length !== 1 ? 's' : ''}</span>
                </div>
                <div onClick={() => fileInputRef.current?.click()}
                  className="flex flex-col items-center justify-center h-28 border border-dashed border-white/10 rounded-xl cursor-pointer bg-white/[0.02] hover:bg-white/[0.04] hover:border-emerald-500/30 transition-all duration-300 group">
                  <div className="w-10 h-10 rounded-full bg-white/5 flex items-center justify-center mb-2 group-hover:scale-105 transition-transform">
                    <Upload className="w-4 h-4 text-emerald-400" />
                  </div>
                  <p className="text-xs text-gray-400"><span className="text-emerald-400 font-semibold">Browse files</span> or drag & drop</p>
                  <p className="text-[10px] text-gray-600 mt-0.5">PDF, DOCX, TXT</p>
                  <input ref={fileInputRef} multiple type="file" className="hidden" accept=".pdf,.doc,.docx,.txt" onChange={handleFileChange} />
                </div>
                {files.length > 0 && (
                  <div className="space-y-1.5 max-h-[120px] overflow-y-auto pr-1">
                    {files.map((f, i) => (
                      <div key={i} className="flex items-center gap-2 text-xs text-gray-300 bg-white/[0.03] rounded-lg p-2.5 px-3 border border-white/5 animate-fade-in group">
                        <div className="w-0.5 h-4 bg-emerald-500/60 rounded-full shrink-0" />
                        <FileText className="w-3.5 h-3.5 text-emerald-400/70 shrink-0" />
                        <span className="truncate flex-1 font-medium">{f.name}</span>
                        <span className="text-[10px] text-gray-500 font-mono shrink-0">{(f.size / 1024).toFixed(0)}KB</span>
                        <button type="button" onClick={(e) => { e.stopPropagation(); removeFile(i); }}
                          className="text-gray-500 hover:text-red-400 transition-colors p-0.5 rounded hover:bg-red-400/10 shrink-0">
                          <X className="w-3 h-3" />
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
            <div className="shrink-0 px-5 py-4 border-t border-white/5 bg-[#0d0d0f]/90">
              <button type="submit" disabled={loading || files.length === 0 || !jobDescription}
                className="w-full flex items-center justify-center gap-2 bg-gradient-to-r from-emerald-600 to-emerald-500 hover:from-emerald-500 hover:to-emerald-400 text-white font-semibold py-3 px-5 rounded-xl transition-all duration-300 disabled:opacity-40 disabled:cursor-not-allowed shadow-lg shadow-emerald-500/15 hover:shadow-emerald-500/25 text-sm group">
                {loading ? (<><Loader2 className="w-4 h-4 animate-spin" /><span>Processing Embeddings...</span></>)
                  : (<><span>Analyze Candidates</span><ChevronRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" /></>)}
              </button>
              {error && (
                <div className="mt-3 flex items-center gap-2 text-red-400 bg-red-950/30 p-3 rounded-lg border border-red-900/40 text-xs animate-fade-in">
                  <AlertCircle className="w-4 h-4 shrink-0" /><p>{error}</p>
                </div>
              )}
            </div>
          </form>
        </aside>

        {/* Right Panel */}
        <main className="flex-1 flex flex-col min-h-0 overflow-hidden">
          <div className="shrink-0 px-6 py-4 border-b border-white/5 flex items-center justify-between bg-[#0b0b0d]/60">
            <div>
              <h2 className="text-sm font-semibold text-white tracking-wide flex items-center gap-2">
                Intelligence Feed
                {results.length > 0 && (
                  <span className="bg-emerald-950 text-emerald-400 text-[10px] font-mono font-semibold px-2 py-0.5 rounded-md border border-emerald-900/50">
                    {results.length} ranked
                  </span>
                )}
              </h2>
              <p className="text-xs text-gray-500 mt-0.5">Semantic AI ranking with confidence scoring</p>
            </div>
            {results.length > 0 && (
              <button onClick={handleExportCSV}
                className="flex items-center gap-1.5 text-xs font-semibold text-gray-300 bg-white/5 px-3 py-2 rounded-lg hover:bg-white/8 transition-all border border-white/8 hover:border-white/12">
                <Download className="w-3.5 h-3.5 text-emerald-400" /> Export CSV
              </button>
            )}
          </div>
          <div className="flex-1 overflow-y-auto">
            {results.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-gray-500 gap-5 px-6">
                <div className="relative">
                  <div className="absolute inset-0 bg-emerald-500/10 blur-3xl rounded-full scale-150" />
                  <div className="w-20 h-20 rounded-2xl glass-card flex items-center justify-center relative border border-white/8">
                    <Sparkles className="w-8 h-8 text-emerald-700/40" />
                  </div>
                </div>
                <div className="text-center">
                  <p className="text-base font-medium text-gray-300">Awaiting Analysis</p>
                  <p className="text-xs mt-1.5 max-w-[260px] mx-auto leading-relaxed text-gray-500">
                    Configure job requirements and upload candidate resumes to generate AI-powered match scores.
                  </p>
                </div>
              </div>
            ) : (
              <div className="p-6 space-y-3">
                {results.map((r, i) => (
                  <div key={i} className="group glass-card rounded-xl overflow-hidden transition-all duration-300 hover:shadow-[0_4px_24px_rgba(0,0,0,0.4)] animate-slide-up"
                    style={{ animationDelay: `${i * 80}ms` }}>
                    {i === 0 && <div className="h-0.5 bg-gradient-to-r from-emerald-500 via-emerald-400 to-transparent" />}
                    <div className="p-5">
                      <div className="flex items-center justify-between mb-4">
                        <div className="flex items-center gap-3">
                          <div className={cn("w-10 h-10 rounded-xl font-bold flex items-center justify-center text-sm border shrink-0",
                            i === 0 ? "bg-gradient-to-br from-emerald-500 to-emerald-700 text-white border-emerald-400/30 shadow-lg shadow-emerald-500/20"
                              : i < 3 ? "bg-white/5 text-emerald-400 border-emerald-900/30"
                                : "bg-white/[0.03] text-gray-400 border-white/5")}>#{i + 1}</div>
                          <div>
                            <h3 className="text-sm font-semibold text-white">{r.candidate_name}</h3>
                            <p className="text-[10px] text-gray-500 font-mono tracking-wider mt-0.5">RESUME ANALYSIS</p>
                          </div>
                        </div>
                        <div className={cn("flex items-center gap-2 px-3 py-1.5 rounded-lg border", getScoreBg(r.match_score))}>
                          <span className={cn("text-xl font-black font-mono tracking-tight", getScoreColor(r.match_score))}>{r.match_score}</span>
                          <div className="flex flex-col">
                            <span className={cn("text-[10px] font-bold", getScoreColor(r.match_score))}>%</span>
                            <span className="text-[8px] text-gray-500 font-semibold tracking-wider uppercase">MATCH</span>
                          </div>
                        </div>
                      </div>
                      <div className="flex items-start gap-4">
                        <div className="flex-1 min-w-0">
                          <p className="text-[10px] font-semibold tracking-widest text-gray-500 mb-2 uppercase">Technical Skills</p>
                          <div className="flex flex-wrap gap-1.5">
                            {r.extracted_skills.length > 0 ? r.extracted_skills.map((skill, idx) => (
                              <span key={idx} className="bg-white/[0.04] border border-white/6 text-gray-300 text-[11px] font-medium px-2.5 py-1 rounded-md">{skill}</span>
                            )) : <span className="text-xs text-gray-500 italic">No technical skills identified</span>}
                          </div>
                        </div>
                        <div className="flex items-center gap-1.5 shrink-0 pt-5">
                          <button onClick={() => handleFeedback(i, 'up')} className={cn("p-2 rounded-lg transition-all duration-200",
                            r.feedback === 'up' ? "bg-emerald-500/15 text-emerald-400 border border-emerald-500/25"
                              : "bg-white/[0.03] text-gray-500 border border-white/5 hover:text-emerald-400 hover:bg-emerald-500/10")} title="Good match">
                            <ThumbsUp className="w-3.5 h-3.5" />
                          </button>
                          <button onClick={() => handleFeedback(i, 'down')} className={cn("p-2 rounded-lg transition-all duration-200",
                            r.feedback === 'down' ? "bg-red-500/15 text-red-400 border border-red-500/25"
                              : "bg-white/[0.03] text-gray-500 border border-white/5 hover:text-red-400 hover:bg-red-500/10")} title="Poor match">
                            <ThumbsDown className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}

export default App;
