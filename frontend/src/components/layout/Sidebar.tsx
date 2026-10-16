import React from 'react';
import {
  LayoutDashboard,
  BrainCircuit,
  Sliders,
  CheckCircle2,
  AlertTriangle,
  RotateCw,
  Factory,
  Zap,
} from 'lucide-react';
import { FactoryListItem, FactoryProfileResponse } from '../../types/api';

export type ActiveTab = 'dashboard' | 'investigator' | 'optimization';

interface SidebarProps {
  activeTab: ActiveTab;
  onSelectTab: (tab: ActiveTab) => void;
  factoryProfile: FactoryProfileResponse | null;
  isBackendHealthy: boolean;
  onRefreshHealth: () => void;
  selectedFactoryId: string;
  onSelectFactory: (factoryId: string) => void;
  factories: FactoryListItem[];
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  onSelectTab,
  factoryProfile,
  isBackendHealthy,
  onRefreshHealth,
  selectedFactoryId,
  onSelectFactory,
  factories,
}) => {
  return (
    <aside className="w-72 bg-slate-900 border-r border-slate-800 flex flex-col justify-between shrink-0 h-screen sticky top-0 text-slate-300">
      {/* Brand Header */}
      <div>
        <div className="h-16 px-6 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="h-9 w-9 rounded-lg bg-gradient-to-tr from-teal-500 to-emerald-400 flex items-center justify-center shadow-lg shadow-teal-900/30">
              <Zap className="w-5 h-5 text-slate-950 font-bold" />
            </div>
            <div>
              <span className="font-bold text-lg tracking-tight text-white">GridMind</span>
              <span className="text-teal-400 font-semibold text-lg ml-1">AI</span>
            </div>
          </div>
          <span className="px-2 py-0.5 rounded text-[10px] font-mono tracking-wide bg-teal-500/10 text-teal-300 border border-teal-500/20">
            MSME v1.0
          </span>
        </div>

        {/* Navigation Items */}
        <nav className="p-4 space-y-1.5">
          <button
            onClick={() => onSelectTab('dashboard')}
            className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-sm font-medium transition-colors ${
              activeTab === 'dashboard'
                ? 'bg-teal-500/10 text-teal-400 border border-teal-500/30'
                : 'hover:bg-slate-800/60 text-slate-400 hover:text-slate-200'
            }`}
          >
            <LayoutDashboard className="w-4 h-4 shrink-0" />
            <span>Factory Dashboard</span>
          </button>

          <button
            onClick={() => onSelectTab('investigator')}
            className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-sm font-medium transition-colors ${
              activeTab === 'investigator'
                ? 'bg-teal-500/10 text-teal-400 border border-teal-500/30'
                : 'hover:bg-slate-800/60 text-slate-400 hover:text-slate-200'
            }`}
          >
            <BrainCircuit className="w-4 h-4 shrink-0" />
            <div className="flex items-center justify-between w-full">
              <span>AI Energy Investigator</span>
              <span className="text-[10px] bg-slate-800 text-teal-300 px-1.5 py-0.5 rounded border border-slate-700">
                Gemini
              </span>
            </div>
          </button>

          <button
            onClick={() => onSelectTab('optimization')}
            className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-sm font-medium transition-colors ${
              activeTab === 'optimization'
                ? 'bg-teal-500/10 text-teal-400 border border-teal-500/30'
                : 'hover:bg-slate-800/60 text-slate-400 hover:text-slate-200'
            }`}
          >
            <Sliders className="w-4 h-4 shrink-0" />
            <div className="flex items-center justify-between w-full">
              <span>Renewable Simulator</span>
              <span className="text-[10px] bg-slate-800 text-emerald-300 px-1.5 py-0.5 rounded border border-slate-700">
                HiGHS LP
              </span>
            </div>
          </button>
        </nav>

        {/* Multi-Factory Quick Switcher Section */}
        <div className="px-4 py-2">
          <span className="text-[10px] uppercase font-bold tracking-wider text-slate-400 px-1">
            Demo MSME Profiles
          </span>
          <div className="mt-2 space-y-1">
            {(factories.length > 0
              ? factories
              : [
                  { factory_id: 'DEMO-FAC-001', name: 'PrecisionWorks Factory', sector: 'Precision CNC Machining' },
                  { factory_id: 'DEMO-FAC-002', name: 'FreshField Factory', sector: 'Food & Cold Storage' },
                  { factory_id: 'DEMO-FAC-003', name: 'WeaveWise Factory', sector: 'Textile Weaving' },
                ]
            ).map((f) => {
              const isSelected = f.factory_id === selectedFactoryId;
              return (
                <button
                  key={f.factory_id}
                  onClick={() => onSelectFactory(f.factory_id)}
                  className={`w-full text-left px-2.5 py-2 rounded-lg text-xs transition-all flex items-center justify-between ${
                    isSelected
                      ? 'bg-teal-950/80 text-teal-300 border border-teal-500/40 shadow-xs'
                      : 'text-slate-400 hover:bg-slate-800/50 hover:text-slate-200 border border-transparent'
                  }`}
                >
                  <div className="truncate">
                    <p className={`font-medium truncate ${isSelected ? 'text-teal-200' : 'text-slate-300'}`}>
                      {f.name}
                    </p>
                    <p className="text-[10px] text-slate-400 truncate">{f.sector}</p>
                  </div>
                  {isSelected && (
                    <span className="w-1.5 h-1.5 rounded-full bg-teal-400 shrink-0 ml-1.5"></span>
                  )}
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* Facility & System Footer */}
      <div className="p-4 border-t border-slate-800 space-y-3">
        {/* Active Facility Profile Card */}
        <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800 text-xs space-y-1.5">
          <div className="flex items-center gap-2 text-slate-200 font-medium">
            <Factory className="w-3.5 h-3.5 text-teal-400 shrink-0" />
            <span className="truncate">{factoryProfile?.name || 'PrecisionWorks Factory'}</span>
          </div>
          <p className="text-slate-400 text-[11px] truncate">
            {factoryProfile?.sector || 'Industrial Manufacturing'}
          </p>
          <div className="pt-1.5 border-t border-slate-800/60 flex items-center justify-between text-[11px] text-slate-400 font-mono">
            <span>Contract Grid:</span>
            <span className="text-slate-200 font-semibold">
              {factoryProfile?.grid.contract_demand_kw ? `${factoryProfile.grid.contract_demand_kw} kW` : '250 kW'}
            </span>
          </div>
        </div>

        {/* Synthetic Simulation Pill */}
        <div className="px-3 py-2 rounded bg-amber-500/10 border border-amber-500/20 text-amber-300 text-[11px] leading-tight">
          <strong>Deterministic Synthetic Model</strong>
          <p className="text-[10px] text-amber-400/90 mt-1">
            Fictional demonstration factories using synthetic data. Not actual customer facilities.
          </p>
        </div>

        {/* Live Backend Connection Indicator */}
        <div className="flex items-center justify-between pt-1 text-[11px]">
          <div className="flex items-center gap-2">
            {isBackendHealthy ? (
              <>
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                <span className="text-emerald-400">FastAPI Connected</span>
              </>
            ) : (
              <>
                <AlertTriangle className="w-3.5 h-3.5 text-rose-400" />
                <span className="text-rose-400">Offline / Connecting</span>
              </>
            )}
          </div>
          <button
            onClick={onRefreshHealth}
            className="text-slate-500 hover:text-slate-300 p-1 rounded transition-colors"
            title="Ping backend service"
          >
            <RotateCw className="w-3 h-3" />
          </button>
        </div>
      </div>
    </aside>
  );
};
