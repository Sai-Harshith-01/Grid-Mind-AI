import React from 'react';
import { HealthCheckState } from '../api/types';
import { API_BASE_URL } from '../api/client';
import { CheckCircle2, AlertCircle, RefreshCw, Server } from 'lucide-react';

interface HealthStatusBadgeProps {
  state: HealthCheckState;
  onRetry: () => void;
  isChecking: boolean;
}

export const HealthStatusBadge: React.FC<HealthStatusBadgeProps> = ({
  state,
  onRetry,
  isChecking,
}) => {
  return (
    <div className="w-full max-w-xl mx-auto rounded-xl border border-slate-800 bg-slate-900/80 p-5 shadow-2xl backdrop-blur-sm">
      <div className="flex items-center justify-between pb-3 border-b border-slate-800/80">
        <div className="flex items-center gap-2">
          <Server className="w-4 h-4 text-slate-400" />
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
            Backend Connectivity
          </span>
        </div>
        <button
          onClick={onRetry}
          disabled={isChecking}
          className="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium rounded-md bg-slate-800 hover:bg-slate-700 text-slate-300 disabled:opacity-50 transition-colors focus:outline-none focus:ring-2 focus:ring-emerald-500/50"
          title="Re-check backend health"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isChecking ? 'animate-spin' : ''}`} />
          {isChecking ? 'Checking...' : 'Check Status'}
        </button>
      </div>

      <div className="mt-4">
        {state.status === 'loading' && (
          <div className="flex items-center gap-3 p-3 rounded-lg bg-slate-800/50 border border-slate-700/50 text-slate-300">
            <RefreshCw className="w-5 h-5 text-emerald-400 animate-spin" />
            <div>
              <p className="text-sm font-medium">Connecting to Backend...</p>
              <p className="text-xs text-slate-400">Pinging {API_BASE_URL}/health</p>
            </div>
          </div>
        )}

        {state.status === 'online' && (
          <div className="rounded-lg bg-emerald-950/40 border border-emerald-500/30 p-3.5 text-emerald-200">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <span className="relative flex h-3 w-3">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
                </span>
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                <span className="text-sm font-semibold tracking-wide text-emerald-300">
                  System Online
                </span>
              </div>
              <span className="text-xs font-mono px-2 py-0.5 rounded bg-emerald-900/60 text-emerald-300 border border-emerald-700/40">
                v{state.data.version}
              </span>
            </div>

            <div className="mt-2.5 grid grid-cols-2 gap-2 text-xs text-emerald-300/80 pt-2 border-t border-emerald-800/30 font-mono">
              <div>
                <span className="text-slate-400 block">Service:</span>
                <span className="truncate">{state.data.service}</span>
              </div>
              <div>
                <span className="text-slate-400 block">Last Verified:</span>
                <span>{new Date(state.data.timestamp).toLocaleTimeString()}</span>
              </div>
            </div>
          </div>
        )}

        {state.status === 'offline' && (
          <div className="rounded-lg bg-rose-950/40 border border-rose-500/30 p-3.5 text-rose-200">
            <div className="flex items-start gap-2.5">
              <AlertCircle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
              <div className="flex-1">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-semibold text-rose-300">
                    System Offline
                  </span>
                  <span className="text-[11px] text-rose-400/80 font-mono">
                    {state.timestamp}
                  </span>
                </div>
                <p className="mt-1 text-xs text-rose-200/90 leading-relaxed">
                  {state.error}
                </p>
                <div className="mt-2.5 pt-2 border-t border-rose-800/30 text-xs text-slate-400">
                  <p>
                    Ensure the FastAPI server is running at{' '}
                    <code className="text-rose-300 bg-rose-950/80 px-1 py-0.5 rounded font-mono">
                      {API_BASE_URL}
                    </code>
                    . Start it with:
                  </p>
                  <pre className="mt-1.5 p-2 rounded bg-black/40 text-slate-300 font-mono text-[11px] overflow-x-auto">
                    uvicorn app.main:app --reload --port 8000
                  </pre>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="mt-3 flex items-center justify-between text-[11px] text-slate-500">
        <span>Target API Endpoint</span>
        <span className="font-mono text-slate-400">{API_BASE_URL}</span>
      </div>
    </div>
  );
};
