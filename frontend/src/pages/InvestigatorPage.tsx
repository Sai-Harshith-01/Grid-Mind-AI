import React, { useState } from 'react';
import {
  BrainCircuit,
  AlertTriangle,
  CheckCircle2,
  Filter,
  Printer,
  Sparkles,
  HelpCircle,
  FileText,
  IndianRupee,
  ChevronRight,
  Loader2,
} from 'lucide-react';
import {
  DetectedAnomalyFinding,
  InvestigationResponse,
  InvestigationStatusResponse,
  InvestigationReportResponse,
} from '../types/api';
import {
  investigateAnomaly,
  generateInvestigationReport,
} from '../api';
import {
  formatINR,
  formatTime,
  getSeverityBadgeClass,
} from '../utils/formatters';

interface InvestigatorPageProps {
  anomalies: DetectedAnomalyFinding[];
  selectedAnomalyId: string | null;
  onSelectAnomaly: (anomalyId: string) => void;
  investigationStatus: InvestigationStatusResponse | null;
  selectedFactoryId?: string;
  onNavigateToOptimizer?: () => void;
}

export const InvestigatorPage: React.FC<InvestigatorPageProps> = ({
  anomalies,
  selectedAnomalyId,
  onSelectAnomaly,
  investigationStatus,
  selectedFactoryId = 'DEMO-FAC-001',
  onNavigateToOptimizer,
}) => {
  const [severityFilter, setSeverityFilter] = useState<string>('all');
  const [categoryFilter, setCategoryFilter] = useState<string>('all');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [investigationResult, setInvestigationResult] = useState<InvestigationResponse | null>(null);
  const [investigationError, setInvestigationError] = useState<string | null>(null);

  // Full Batch Report State
  const [isReportLoading, setIsReportLoading] = useState<boolean>(false);
  const [batchReport, setBatchReport] = useState<InvestigationReportResponse | null>(null);
  const [reportError, setReportError] = useState<string | null>(null);
  const [showReportModal, setShowReportModal] = useState<boolean>(false);

  // Filter findings
  const filteredFindings = anomalies.filter((finding) => {
    if (severityFilter !== 'all' && finding.severity !== severityFilter) return false;
    if (categoryFilter !== 'all' && finding.category !== categoryFilter) return false;
    return true;
  });

  // Current active finding
  const activeFinding =
    anomalies.find((f) => f.finding_id === selectedAnomalyId) || filteredFindings[0] || null;

  const handleRunInvestigation = async () => {
    if (!activeFinding) return;

    setIsLoading(true);
    setInvestigationError(null);
    setInvestigationResult(null);

    try {
      const result = await investigateAnomaly(activeFinding.finding_id, selectedFactoryId);
      setInvestigationResult(result);
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Investigation failed';
      setInvestigationError(msg);
    } finally {
      setIsLoading(false);
    }
  };

  const handleGenerateReport = async () => {
    setIsReportLoading(true);
    setReportError(null);
    try {
      const report = await generateInvestigationReport({ max_findings: 5 }, selectedFactoryId);
      setBatchReport(report);
      setShowReportModal(true);
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to generate report';
      setReportError(msg);
    } finally {
      setIsReportLoading(false);
    }
  };


  return (
    <div className="p-8 space-y-6 max-w-7xl mx-auto">
      {/* Gemini AI Status Header Banner */}
      <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-lg bg-teal-50 text-teal-700 border border-teal-200">
            <BrainCircuit className="w-5 h-5 text-teal-600" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-sm font-bold text-slate-900">
                Google Gemini AI Energy Investigator
              </h2>
              {investigationStatus?.is_available ? (
                <span className="flex items-center gap-1 text-[11px] font-mono text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                  <CheckCircle2 className="w-3 h-3 text-emerald-500" />
                  Ready ({investigationStatus.model_name})
                </span>
              ) : (
                <span className="flex items-center gap-1 text-[11px] font-mono text-amber-700 bg-amber-50 px-2 py-0.5 rounded-full border border-amber-200">
                  <AlertTriangle className="w-3 h-3 text-amber-500" />
                  Key Not Configured
                </span>
              )}
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              {investigationStatus?.status_message ||
                'Rule-based analytical evidence is fully available. Add GEMINI_API_KEY in backend/.env to unlock generative root-cause audits.'}
            </p>
          </div>
        </div>

        {/* Action: Generate Full Plant Diagnostic Report */}
        <button
          onClick={handleGenerateReport}
          disabled={isReportLoading || !investigationStatus?.is_available}
          className="flex items-center justify-center gap-2 px-4 py-2 rounded-lg bg-teal-600 hover:bg-teal-700 text-white disabled:opacity-50 text-xs font-semibold shadow-sm transition-all active:scale-95 shrink-0"
        >
          {isReportLoading ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Synthesizing Report...</span>
            </>
          ) : (
            <>
              <FileText className="w-4 h-4" />
              <span>Generate Executive Report</span>
            </>
          )}
        </button>
      </div>

      {reportError && (
        <div className="p-4 bg-rose-50 border border-rose-200 text-rose-800 rounded-xl text-xs flex items-center justify-between">
          <span>{reportError}</span>
          <button onClick={() => setReportError(null)} className="text-rose-600 font-bold ml-4">
            Dismiss
          </button>
        </div>
      )}

      {/* Main Two-Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: Filterable Anomaly Selector (4 cols) */}
        <div className="lg:col-span-4 bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden flex flex-col">
          <div className="p-4 border-b border-slate-100 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-1.5">
                <Filter className="w-3.5 h-3.5 text-slate-500" />
                Detected Findings ({filteredFindings.length})
              </span>
            </div>

            {/* Filter Controls */}
            <div className="grid grid-cols-2 gap-2 text-xs">
              <select
                value={severityFilter}
                onChange={(e) => setSeverityFilter(e.target.value)}
                className="bg-slate-50 border border-slate-200 text-slate-700 text-xs rounded-lg px-2 py-1.5 focus:outline-none focus:ring-1 focus:ring-teal-500"
              >
                <option value="all">All Severities</option>
                <option value="critical">Critical</option>
                <option value="high">High</option>
                <option value="medium">Medium</option>
                <option value="low">Low</option>
              </select>

              <select
                value={categoryFilter}
                onChange={(e) => setCategoryFilter(e.target.value)}
                className="bg-slate-50 border border-slate-200 text-slate-700 text-xs rounded-lg px-2 py-1.5 focus:outline-none focus:ring-1 focus:ring-teal-500"
              >
                <option value="all">All Categories</option>
                <option value="idle_machine_waste">Idle Waste</option>
                <option value="unexpected_consumption_spike">Spike</option>
                <option value="high_demand_period">Peak Risk</option>
              </select>
            </div>
          </div>

          {/* Finding Cards List */}
          <div className="divide-y divide-slate-100 max-h-[600px] overflow-y-auto">
            {filteredFindings.map((finding) => {
              const isSelected = activeFinding?.finding_id === finding.finding_id;
              return (
                <button
                  key={finding.finding_id}
                  onClick={() => {
                    onSelectAnomaly(finding.finding_id);
                    setInvestigationResult(null);
                    setInvestigationError(null);
                  }}
                  className={`w-full text-left p-4 transition-colors flex items-start justify-between gap-3 ${
                    isSelected ? 'bg-teal-50/70 border-l-4 border-teal-500' : 'hover:bg-slate-50'
                  }`}
                >
                  <div className="space-y-1.5 min-w-0">
                    <div className="flex items-center gap-2">
                      <span
                        className={`px-1.5 py-0.5 rounded text-[9px] font-bold uppercase tracking-wider ${getSeverityBadgeClass(
                          finding.severity
                        )}`}
                      >
                        {finding.severity}
                      </span>
                      <span className="text-[11px] font-mono text-slate-400">
                        {formatTime(finding.timestamp)}
                      </span>
                    </div>

                    <div className="text-xs font-semibold text-slate-800 truncate">
                      {finding.title}
                    </div>

                    <div className="text-[11px] text-slate-500 flex items-center gap-2 font-mono">
                      <span>Dev: +{finding.evidence.deviation_percent.toFixed(0)}%</span>
                      <span>•</span>
                      <span>{finding.affected_zone_name || 'Plant'}</span>
                    </div>
                  </div>

                  <ChevronRight
                    className={`w-4 h-4 shrink-0 transition-transform ${
                      isSelected ? 'text-teal-600 translate-x-0.5' : 'text-slate-300'
                    }`}
                  />
                </button>
              );
            })}
          </div>
        </div>

        {/* Right Column: Grounded Evidence & Gemini Investigation (8 cols) */}
        <div className="lg:col-span-8 space-y-6">
          {activeFinding ? (
            <>
              {/* Evidence Panel (Deterministic Facts) */}
              <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm space-y-5">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-100">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs font-mono text-slate-400">
                        {activeFinding.finding_id}
                      </span>
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${getSeverityBadgeClass(
                          activeFinding.severity
                        )}`}
                      >
                        {activeFinding.severity}
                      </span>
                    </div>
                    <h3 className="text-lg font-bold text-slate-900 tracking-tight">
                      {activeFinding.title}
                    </h3>
                  </div>

                  {/* Trigger Gemini Investigation Button */}
                  <button
                    onClick={handleRunInvestigation}
                    disabled={isLoading}
                    className="flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg bg-teal-600 hover:bg-teal-700 text-white disabled:opacity-50 text-xs font-semibold shadow-sm transition-all active:scale-95 shrink-0"
                  >
                    {isLoading ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        <span>Investigating with Gemini...</span>
                      </>
                    ) : (
                      <>
                        <Sparkles className="w-4 h-4 text-teal-200" />
                        <span>Investigate with Gemini</span>
                      </>
                    )}
                  </button>
                </div>

                {/* Evidence Metrics Grid */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                  <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
                    <span className="text-[11px] text-slate-500 block">Observed Value</span>
                    <span className="text-base font-bold font-mono text-slate-900">
                      {activeFinding.evidence.observed_value.toFixed(1)} {activeFinding.evidence.unit}
                    </span>
                  </div>

                  <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
                    <span className="text-[11px] text-slate-500 block">Expected Baseline</span>
                    <span className="text-base font-bold font-mono text-slate-700">
                      {activeFinding.evidence.baseline_threshold.toFixed(1)} {activeFinding.evidence.unit}
                    </span>
                  </div>

                  <div className="p-3 bg-rose-50/60 rounded-lg border border-rose-100">
                    <span className="text-[11px] text-rose-600 block">Calculated Deviation</span>
                    <span className="text-base font-bold font-mono text-rose-700">
                      +{activeFinding.evidence.deviation_percent.toFixed(1)}%
                    </span>
                  </div>

                  <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
                    <span className="text-[11px] text-slate-500 block">Interval Tariff</span>
                    <span className="text-base font-bold font-mono text-slate-900">
                      ₹{activeFinding.evidence.grid_tariff_inr_per_kwh?.toFixed(2) || '—'} / kWh
                    </span>
                  </div>
                </div>

                {/* Detection Rule Context */}
                <div className="p-3.5 bg-slate-50 rounded-lg border border-slate-100 text-xs space-y-1.5">
                  <div className="font-semibold text-slate-700 flex items-center justify-between">
                    <span>Detection Rule: {activeFinding.detection_rule_id}</span>
                    <span className="font-mono text-[10px] text-slate-400">Deterministic Heuristic</span>
                  </div>
                  <p className="text-slate-600 leading-relaxed">
                    {activeFinding.detection_rule_description}
                  </p>
                </div>

                {/* Initial Diagnostic Notes */}
                <div className="text-xs text-slate-500 flex items-start gap-2 bg-amber-50/50 p-3 rounded-lg border border-amber-100">
                  <HelpCircle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                  <div>
                    <span className="font-semibold text-amber-900">
                      Initial Engineering Diagnostic Hypothesis:
                    </span>
                    <p className="text-amber-800 mt-0.5 leading-relaxed">
                      {activeFinding.physical_hypothesis_notes}
                    </p>
                  </div>
                </div>
              </div>

              {/* Error Message Display */}
              {investigationError && (
                <div className="p-5 bg-rose-50 border border-rose-200 rounded-xl text-xs space-y-2">
                  <div className="flex items-center gap-2 text-rose-900 font-bold">
                    <AlertTriangle className="w-4 h-4 text-rose-600" />
                    <span>Gemini Investigation Unavailable</span>
                  </div>
                  <p className="text-rose-700 leading-relaxed">{investigationError}</p>
                  <p className="text-[11px] text-rose-600 pt-1 border-t border-rose-200/60 font-mono">
                    To enable live Gemini root-cause generation, ensure GEMINI_API_KEY is configured in backend/.env.
                  </p>
                </div>
              )}

              {/* Gemini AI Structured Response */}
              {investigationResult && (
                <div className="bg-white rounded-xl border border-teal-200 p-6 shadow-sm space-y-6 animate-fadeIn">
                  {/* AI Metadata & Executive Summary */}
                  <div className="pb-4 border-b border-slate-100 space-y-2">
                    <div className="flex items-center justify-between text-xs">
                      <span className="flex items-center gap-1.5 font-bold text-teal-700 uppercase tracking-wider">
                        <Sparkles className="w-4 h-4 text-teal-600" />
                        Gemini AI Diagnostic Report
                      </span>
                      <span className="font-mono text-slate-400 text-[11px]">
                        Model: {investigationResult.ai_metadata.model_name} (
                        {investigationResult.ai_metadata.latency_ms}ms)
                      </span>
                    </div>
                    <p className="text-sm text-slate-800 leading-relaxed font-medium bg-teal-50/60 p-3.5 rounded-lg border border-teal-100">
                      {investigationResult.summary}
                    </p>
                  </div>

                  {/* Factual Observations */}
                  <div className="space-y-2">
                    <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                      Factual Telemetry Observations
                    </h4>
                    <ul className="list-disc pl-5 text-xs text-slate-600 space-y-1">
                      {investigationResult.observations.map((obs, i) => (
                        <li key={i}>{obs}</li>
                      ))}
                    </ul>
                  </div>

                  {/* Possible Causes (Hypotheses) */}
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                        Suspected Causes (Unconfirmed Hypotheses)
                      </h4>
                      <span className="text-[10px] text-amber-700 bg-amber-50 px-2 py-0.5 rounded border border-amber-200 font-medium">
                        Verification Required
                      </span>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      {investigationResult.possible_causes.map((cause, i) => (
                        <div
                          key={i}
                          className="p-3.5 rounded-lg border border-slate-200 bg-slate-50/60 text-xs space-y-1.5"
                        >
                          <div className="flex items-center justify-between">
                            <span className="font-bold text-slate-800">Hypothesis {i + 1}</span>
                            <span className="text-[10px] font-mono font-semibold text-slate-500 bg-slate-200/60 px-1.5 py-0.5 rounded">
                              Likelihood: {cause.likelihood}
                            </span>
                          </div>
                          <p className="text-slate-700 font-medium">{cause.hypothesis}</p>
                          <p className="text-[11px] text-slate-500">
                            <strong>Evidence:</strong> {cause.supporting_evidence}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Prioritised Recommended Actions */}
                  <div className="space-y-3">
                    <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                      Prioritised Operator Recommendations
                    </h4>

                    <div className="space-y-3">
                      {investigationResult.recommended_actions.map((rec, i) => (
                        <div
                          key={i}
                          className="p-4 rounded-xl border border-slate-200 bg-white shadow-sm space-y-2.5 text-xs"
                        >
                          <div className="flex items-center justify-between gap-2">
                            <div className="flex items-center gap-2">
                              <span
                                className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${getSeverityBadgeClass(
                                  rec.priority
                                )}`}
                              >
                                {rec.priority}
                              </span>
                              <span className="font-bold text-slate-900 text-sm">
                                {rec.action}
                              </span>
                            </div>
                          </div>

                          <p className="text-slate-600 leading-relaxed">{rec.rationale}</p>

                          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-2 border-t border-slate-100 text-[11px]">
                            <div className="text-slate-600">
                              <strong className="text-teal-700">Expected Benefit:</strong>{' '}
                              {rec.expected_operational_benefit}
                            </div>
                            <div className="text-slate-600">
                              <strong className="text-rose-700">Safety Precautions:</strong>{' '}
                              {rec.safety_considerations}
                            </div>
                          </div>

                          <div className="pt-2 border-t border-slate-100 text-[11px] text-slate-500 font-mono">
                            <strong>Verification Step:</strong> {rec.verification_step}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Backend Calculated Financial Impact */}
                  <div className="p-4 bg-slate-900 text-white rounded-xl space-y-2 text-xs border border-slate-800">
                    <div className="flex items-center justify-between text-slate-300 font-semibold border-b border-slate-800 pb-1.5">
                      <span className="flex items-center gap-1.5">
                        <IndianRupee className="w-3.5 h-3.5 text-teal-400" />
                        Authoritative Backend Financial Impact
                      </span>
                      <span className="text-[10px] font-mono text-slate-400">
                        Derived from LP Optimiser
                      </span>
                    </div>
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-1">
                      <div>
                        <span className="text-slate-400 text-[10px] block">Excess Energy</span>
                        <span className="font-mono text-sm font-bold text-amber-300">
                          {investigationResult.financial_impact.detected_excess_energy_kwh?.toFixed(1) || '0.0'} kWh
                        </span>
                      </div>
                      <div>
                        <span className="text-slate-400 text-[10px] block">Interval Grid Cost</span>
                        <span className="font-mono text-sm font-bold text-white">
                          {formatINR(investigationResult.financial_impact.excess_energy_grid_cost_inr)}
                        </span>
                      </div>
                      <div>
                        <span className="text-slate-400 text-[10px] block">Daily Plant Spend</span>
                        <span className="font-mono text-sm font-bold text-slate-300">
                          {formatINR(investigationResult.financial_impact.optimised_scenario_cost_inr)}
                        </span>
                      </div>
                      <div>
                        <span className="text-slate-400 text-[10px] block">Daily LP Savings</span>
                        <span className="font-mono text-sm font-bold text-emerald-400">
                          {formatINR(investigationResult.financial_impact.estimated_daily_savings_inr)}
                        </span>
                      </div>
                    </div>
                    <p className="text-[11px] text-slate-400 pt-2 border-t border-slate-800/80 italic">
                      {investigationResult.financial_impact.financial_caveats}
                    </p>
                  </div>

                  {/* Step 4 Demo Action: Navigate to Optimiser */}
                  {onNavigateToOptimizer && (
                    <div className="p-4 bg-teal-50 border border-teal-200 rounded-xl flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
                      <div className="space-y-0.5">
                        <span className="font-bold text-teal-900 flex items-center gap-1.5 text-xs">
                          <Sparkles className="w-4 h-4 text-teal-600 shrink-0" />
                          Demo Step 4: Multi-Source Dispatch Optimisation
                        </span>
                        <p className="text-teal-700 text-[11px]">
                          Root causes isolated and mitigations identified. Run the HiGHS LP solver to calculate optimal solar, wind, biomass, and grid allocations.
                        </p>
                      </div>
                      <button
                        onClick={onNavigateToOptimizer}
                        className="px-4 py-2.5 rounded-lg bg-teal-600 hover:bg-teal-700 text-white font-semibold text-xs transition-colors shrink-0 flex items-center gap-1.5 shadow-sm"
                      >
                        <span>Optimise This Factory</span>
                        <ChevronRight className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  )}
                </div>
              )}
            </>
          ) : (
            <div className="bg-white rounded-xl border border-slate-200 p-12 text-center text-slate-400 text-sm">
              No anomalies found matching current filters.
            </div>
          )}
        </div>
      </div>

      {/* Batch Executive Report Modal */}
      {showReportModal && batchReport && (
        <div className="fixed inset-0 bg-slate-950/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-3xl w-full max-h-[85vh] overflow-y-auto shadow-2xl border border-slate-200 p-6 space-y-6">
            <div className="flex items-center justify-between pb-4 border-b border-slate-100">
              <div className="flex items-center gap-2.5">
                <FileText className="w-5 h-5 text-teal-600" />
                <h3 className="text-lg font-bold text-slate-900 tracking-tight">
                  Plant-Wide Energy Diagnostic Audit Report
                </h3>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => window.print()}
                  className="p-2 text-slate-500 hover:text-slate-800 rounded-lg hover:bg-slate-100 transition-colors"
                  title="Print Report"
                >
                  <Printer className="w-4 h-4" />
                </button>
                <button
                  onClick={() => setShowReportModal(false)}
                  className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-100 text-slate-700 hover:bg-slate-200"
                >
                  Close
                </button>
              </div>
            </div>

            <div className="p-4 bg-teal-50/70 border border-teal-100 rounded-xl text-xs text-slate-700 leading-relaxed">
              <strong className="text-teal-900 block mb-1">Executive Risk Synthesis:</strong>
              {batchReport.overall_risk_summary}
            </div>

            <div className="space-y-3">
              <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                Consolidated Priority Action Plan
              </h4>
              <div className="space-y-2.5">
                {batchReport.prioritized_actions.map((act, i) => (
                  <div
                    key={i}
                    className="p-3.5 rounded-lg border border-slate-200 bg-slate-50/60 text-xs space-y-1.5"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-slate-900">{act.action}</span>
                      <span
                        className={`px-1.5 py-0.5 rounded text-[10px] font-bold uppercase ${getSeverityBadgeClass(
                          act.priority
                        )}`}
                      >
                        {act.priority}
                      </span>
                    </div>
                    <p className="text-slate-600">{act.rationale}</p>
                    <p className="text-[11px] text-teal-700 font-mono">
                      Expected Benefit: {act.expected_operational_benefit}
                    </p>
                  </div>
                ))}
              </div>
            </div>

            <div className="pt-3 border-t border-slate-100 text-[11px] text-slate-400 flex items-center justify-between font-mono">
              <span>Report ID: {batchReport.report_id}</span>
              <span>Generated: {new Date(batchReport.generated_at).toLocaleString()}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
