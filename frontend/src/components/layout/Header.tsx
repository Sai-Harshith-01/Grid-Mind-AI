import React from 'react';
import { RefreshCw, Clock, Building2, ChevronDown } from 'lucide-react';
import { FactoryListItem } from '../../types/api';

interface HeaderProps {
  title: string;
  subtitle: string;
  onRefresh: () => void;
  isLoading?: boolean;
  lastUpdated?: string;
  selectedFactoryId: string;
  onSelectFactory: (factoryId: string) => void;
  factories: FactoryListItem[];
}

export const Header: React.FC<HeaderProps> = ({
  title,
  subtitle,
  onRefresh,
  isLoading = false,
  lastUpdated,
  selectedFactoryId,
  onSelectFactory,
  factories,
}) => {
  return (
    <header className="bg-white border-b border-slate-200 px-6 lg:px-8 py-4 flex flex-col lg:flex-row lg:items-center justify-between gap-4 sticky top-0 z-20 shadow-xs">
      <div>
        <h1 className="text-xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
          {title}
        </h1>
        <p className="text-xs text-slate-500 mt-0.5">{subtitle}</p>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        {/* Factory Selector Dropdown */}
        <div className="relative flex items-center">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-teal-50 border border-teal-200 text-teal-900 shadow-xs hover:border-teal-300 transition-colors">
            <Building2 className="w-4 h-4 text-teal-600 shrink-0" />
            <div className="flex flex-col">
              <span className="text-[10px] uppercase font-bold tracking-wider text-teal-700 leading-none">
                Active Factory
              </span>
              <select
                value={selectedFactoryId}
                onChange={(e) => onSelectFactory(e.target.value)}
                disabled={isLoading}
                className="bg-transparent text-xs font-semibold text-slate-900 pr-5 focus:outline-hidden cursor-pointer appearance-none"
              >
                {factories.length > 0 ? (
                  factories.map((f) => (
                    <option key={f.factory_id} value={f.factory_id}>
                      {f.name} ({f.factory_id})
                    </option>
                  ))
                ) : (
                  <>
                    <option value="DEMO-FAC-001">PrecisionWorks Factory (DEMO-FAC-001)</option>
                    <option value="DEMO-FAC-002">FreshField Factory (DEMO-FAC-002)</option>
                    <option value="DEMO-FAC-003">WeaveWise Factory (DEMO-FAC-003)</option>
                  </>
                )}
              </select>
            </div>
            <ChevronDown className="w-3.5 h-3.5 text-teal-700 pointer-events-none absolute right-2.5 top-1/2 -translate-y-1/2" />
          </div>
        </div>

        {/* Time Horizon Indicator */}
        <div className="hidden sm:flex items-center gap-1.5 px-3 py-2 rounded-lg bg-slate-100 text-slate-600 text-xs font-mono border border-slate-200">
          <Clock className="w-3.5 h-3.5 text-slate-500" />
          <span>24-Hour Horizon</span>
        </div>

        {/* Refresh Action Button */}
        <button
          onClick={onRefresh}
          disabled={isLoading}
          className="flex items-center gap-2 px-3.5 py-2 rounded-lg bg-slate-900 text-white hover:bg-slate-800 disabled:opacity-50 text-xs font-medium transition-all shadow-sm active:scale-95"
          title="Refresh current factory telemetry and rerun optimisation"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
          <span>{isLoading ? 'Updating...' : 'Refresh'}</span>
        </button>

        {lastUpdated && (
          <span className="text-[11px] text-slate-400 hidden xl:inline">
            {lastUpdated}
          </span>
        )}
      </div>
    </header>
  );
};
