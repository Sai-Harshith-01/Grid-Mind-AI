import React from 'react';
import { AlertCircle, ArrowRight, BrainCircuit } from 'lucide-react';
import { DetectedAnomalyFinding } from '../../types/api';
import {
  formatCategoryName,
  formatTime,
  getSeverityBadgeClass,
} from '../../utils/formatters';

interface AnomalyAlertsSectionProps {
  findings: DetectedAnomalyFinding[];
  onInvestigate: (findingId: string) => void;
}

export const AnomalyAlertsSection: React.FC<AnomalyAlertsSectionProps> = ({
  findings,
  onInvestigate,
}) => {
  // Sort findings by severity priority: critical > high > medium > low
  const severityRank: Record<string, number> = {
    critical: 4,
    high: 3,
    medium: 2,
    low: 1,
  };

  const sortedFindings = [...findings].sort(
    (a, b) => (severityRank[b.severity] || 0) - (severityRank[a.severity] || 0)
  );

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4 pb-3 border-b border-slate-100">
        <div>
          <h3 className="text-base font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-rose-500" />
            Detected Operational Anomalies ({findings.length})
          </h3>
          <p className="text-xs text-slate-500">
            Algorithmic rule violations requiring plant operator review or AI root-cause investigation
          </p>
        </div>
        <span className="text-xs font-mono text-slate-500">
          Ranked by Severity
        </span>
      </div>

      <div className="divide-y divide-slate-100 overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead>
            <tr className="text-slate-400 font-semibold border-b border-slate-100 pb-2">
              <th className="py-2.5 px-3">Severity</th>
              <th className="py-2.5 px-3">Category</th>
              <th className="py-2.5 px-3">Affected Zone / Machine</th>
              <th className="py-2.5 px-3">Time</th>
              <th className="py-2.5 px-3 font-mono">Observed vs Threshold</th>
              <th className="py-2.5 px-3 font-mono">Deviation</th>
              <th className="py-2.5 px-3 text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {sortedFindings.map((finding) => (
              <tr
                key={finding.finding_id}
                className="hover:bg-slate-50/80 transition-colors group"
              >
                <td className="py-3 px-3">
                  <span
                    className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${getSeverityBadgeClass(
                      finding.severity
                    )}`}
                  >
                    {finding.severity}
                  </span>
                </td>
                <td className="py-3 px-3 font-medium text-slate-800">
                  {formatCategoryName(finding.category)}
                  <p className="text-[11px] text-slate-400 font-normal truncate max-w-xs">
                    {finding.title}
                  </p>
                </td>
                <td className="py-3 px-3 text-slate-600">
                  {finding.affected_zone_name || 'Plant-wide'}
                  {finding.affected_machine_name && (
                    <span className="block text-[11px] text-slate-400 truncate">
                      {finding.affected_machine_name}
                    </span>
                  )}
                </td>
                <td className="py-3 px-3 font-mono text-slate-600">
                  {formatTime(finding.timestamp)}
                </td>
                <td className="py-3 px-3 font-mono text-slate-700">
                  <span className="font-bold text-slate-900">
                    {finding.evidence.observed_value.toFixed(1)} {finding.evidence.unit}
                  </span>{' '}
                  <span className="text-slate-400 text-[11px]">
                    / {finding.evidence.baseline_threshold.toFixed(1)}
                  </span>
                </td>
                <td className="py-3 px-3 font-mono font-semibold text-rose-600">
                  +{finding.evidence.deviation_percent.toFixed(0)}%
                </td>
                <td className="py-3 px-3 text-right">
                  <button
                    onClick={() => onInvestigate(finding.finding_id)}
                    className="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-teal-50 text-teal-700 hover:bg-teal-100 border border-teal-200 text-xs font-medium transition-colors active:scale-95"
                  >
                    <BrainCircuit className="w-3.5 h-3.5 text-teal-600" />
                    <span>Investigate</span>
                    <ArrowRight className="w-3 h-3 text-teal-500 opacity-60 group-hover:translate-x-0.5 transition-transform" />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
