import React from 'react';
import { LucideIcon } from 'lucide-react';

interface KpiCardProps {
  label: string;
  value: string;
  subtext?: string;
  icon: LucideIcon;
  badge?: string;
  badgeColor?: 'teal' | 'emerald' | 'amber' | 'blue' | 'rose' | 'slate';
  accent?: 'default' | 'teal' | 'emerald' | 'amber' | 'blue';
  isEstimate?: boolean;
}

export const KpiCard: React.FC<KpiCardProps> = ({
  label,
  value,
  subtext,
  icon: Icon,
  badge,
  badgeColor = 'slate',
  accent = 'default',
  isEstimate = false,
}) => {
  const getBadgeClass = () => {
    switch (badgeColor) {
      case 'teal':
        return 'bg-teal-50 text-teal-700 border-teal-200';
      case 'emerald':
        return 'bg-emerald-50 text-emerald-700 border-emerald-200';
      case 'amber':
        return 'bg-amber-50 text-amber-700 border-amber-200';
      case 'rose':
        return 'bg-rose-50 text-rose-700 border-rose-200';
      case 'blue':
        return 'bg-blue-50 text-blue-700 border-blue-200';
      case 'slate':
      default:
        return 'bg-slate-100 text-slate-700 border-slate-200';
    }
  };

  const getIconColor = () => {
    switch (accent) {
      case 'teal':
        return 'text-teal-600 bg-teal-50';
      case 'emerald':
        return 'text-emerald-600 bg-emerald-50';
      case 'amber':
        return 'text-amber-600 bg-amber-50';
      case 'blue':
        return 'text-blue-600 bg-blue-50';
      case 'default':
      default:
        return 'text-slate-700 bg-slate-100';
    }
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200/90 p-5 shadow-sm hover:shadow transition-shadow">
      <div className="flex items-center justify-between gap-3 mb-3">
        <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider flex items-center gap-1.5">
          {label}
          {isEstimate && (
            <span className="text-[10px] font-normal normal-case text-slate-400 bg-slate-100 px-1.5 py-0.2 rounded">
              est.
            </span>
          )}
        </span>
        <div className={`p-2 rounded-lg ${getIconColor()}`}>
          <Icon className="w-4 h-4" />
        </div>
      </div>

      <div className="flex items-baseline justify-between gap-2">
        <div className="text-2xl font-bold text-slate-900 tracking-tight font-mono">
          {value}
        </div>
        {badge && (
          <span
            className={`text-[11px] font-medium font-mono px-2 py-0.5 rounded-full border ${getBadgeClass()}`}
          >
            {badge}
          </span>
        )}
      </div>

      {subtext && <p className="text-xs text-slate-500 mt-2 truncate">{subtext}</p>}
    </div>
  );
};
