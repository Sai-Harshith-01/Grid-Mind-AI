import React, { useState } from 'react';
import {
  Calculator,
  Calendar,
  AlertCircle,
  HelpCircle,
  ArrowRight,
  TrendingDown,
  RotateCcw,
} from 'lucide-react';
import { formatINR, formatLakhs, formatPercent } from '../../utils/formatters';

export interface VerifiedSavingsCalculatorProps {
  baselineCost: number | null | undefined;
  optimisedCost: number | null | undefined;
  dailySavings: number | null | undefined;
  savingsPercentage: number | null | undefined;
  onNavigateToOptimizer?: () => void;
  factoryName?: string;
  isScenarioActive?: boolean;
  scenarioName?: string;
  isCapacityFeasible?: boolean;
  onResetScenario?: () => void;
}

export const VerifiedSavingsCalculator: React.FC<VerifiedSavingsCalculatorProps> = ({
  baselineCost,
  optimisedCost,
  dailySavings,
  savingsPercentage,
  onNavigateToOptimizer,
  factoryName,
  isScenarioActive = false,
  scenarioName,
  isCapacityFeasible = true,
  onResetScenario,
}) => {
  const [operatingDays, setOperatingDays] = useState<number>(300);

  // If optimization hasn't run or data is missing
  if (
    baselineCost === null ||
    baselineCost === undefined ||
    optimisedCost === null ||
    optimisedCost === undefined
  ) {
    return (
      <div className="bg-white border border-slate-200 rounded-xl p-6 text-center space-y-3">
        <div className="w-10 h-10 rounded-full bg-slate-100 flex items-center justify-center mx-auto text-slate-500">
          <Calculator className="w-5 h-5" />
        </div>
        <h4 className="text-sm font-semibold text-slate-900">Modelled Electricity Savings Calculator</h4>
        <p className="text-xs text-slate-500 max-w-md mx-auto">
          Execute the HiGHS linear programming optimiser to calculate baseline vs. multi-source supply costs.
        </p>
        {onNavigateToOptimizer && (
          <button
            onClick={onNavigateToOptimizer}
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-teal-600 text-white text-xs font-medium hover:bg-teal-700 transition-colors shadow-xs"
          >
            <span>Run Optimisation to Calculate Savings</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        )}
      </div>
    );
  }

  // Calculate unrounded savings from exact backend figures
  const effectiveDailySavings = dailySavings ?? (baselineCost - optimisedCost);
  const isPositiveSavings = effectiveDailySavings >= 0;
  const effectiveSavingsPercentage =
    savingsPercentage ?? (baselineCost > 0 ? (effectiveDailySavings / baselineCost) * 100 : 0);
  const annualSavings = effectiveDailySavings * operatingDays;

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-xs space-y-5">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-100">
        <div className="flex items-center gap-2.5">
          <div className="w-9 h-9 rounded-lg bg-emerald-50 border border-emerald-200 flex items-center justify-center text-emerald-700">
            <TrendingDown className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base font-bold text-slate-900">
                Modelled Electricity Savings Calculator
              </h3>
              {isScenarioActive ? (
                <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-amber-100 text-amber-800 border border-amber-300">
                  {scenarioName || 'What-If Scenario Active'}
                </span>
              ) : (
                <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-teal-100 text-teal-800 border border-teal-200">
                  Standard Baseline
                </span>
              )}
            </div>
            <p className="text-xs text-slate-500">
              {factoryName
                ? `Derived from ${factoryName} 24-hour deterministic dispatch matrix`
                : 'Linear programming baseline vs. multi-source dispatch'}
            </p>
          </div>
        </div>

        {/* Operating Days Configurator */}
        <div className="flex items-center gap-2 bg-slate-50 border border-slate-200 px-3 py-1.5 rounded-lg text-xs self-start sm:self-auto">
          <Calendar className="w-3.5 h-3.5 text-slate-500" />
          <span className="text-slate-600 font-medium">Annual Horizon:</span>
          <select
            value={operatingDays}
            onChange={(e) => setOperatingDays(Number(e.target.value))}
            className="bg-white border border-slate-300 rounded px-2 py-0.5 text-xs font-semibold text-slate-800 focus:outline-hidden cursor-pointer"
          >
            <option value={250}>250 Days (Single Shift MSME)</option>
            <option value={300}>300 Days (Standard 6-Day MSME)</option>
            <option value={350}>350 Days (Continuous 24/7)</option>
            <option value={365}>365 Days (Full Year)</option>
          </select>
        </div>
      </div>

      {/* Scenario Awareness Callout */}
      {isScenarioActive && (
        <div className="p-3 bg-amber-50/80 border border-amber-200 text-amber-900 rounded-lg text-xs flex items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-amber-600 shrink-0" />
            <span>
              <strong>What-If Scenario Active:</strong> Both the baseline cost and optimised cost are recalculated for this scenario ({scenarioName || 'Adjusted Parameters'}).
            </span>
          </div>
          {onResetScenario && (
            <button
              onClick={onResetScenario}
              className="inline-flex items-center gap-1 px-2.5 py-1 text-xs rounded bg-white hover:bg-amber-100 text-amber-900 border border-amber-300 font-semibold shrink-0 transition-colors"
            >
              <RotateCcw className="w-3 h-3" />
              <span>Reset to Standard</span>
            </button>
          )}
        </div>
      )}

      {/* Numerical Metrics Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Baseline Cost */}
        <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-1">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-medium text-slate-500">
              {isCapacityFeasible ? 'Grid-Only Reference Baseline' : 'Unconstrained Grid Baseline'}
            </span>
            {!isCapacityFeasible && (
              <span className="text-[9px] font-bold px-1.5 py-0.5 rounded bg-rose-100 text-rose-800">
                Over Contract Cap
              </span>
            )}
          </div>
          <div className="text-xl font-bold text-slate-900">{formatINR(baselineCost)}</div>
          <p className="text-[10px] text-slate-400">
            {isScenarioActive
              ? '100% utility grid under active scenario tariffs'
              : '100% utility grid under standard multi-tier ToD tariffs'}
          </p>
        </div>

        {/* Optimised Supply Cost */}
        <div className="p-4 rounded-xl bg-teal-50/60 border border-teal-200 space-y-1">
          <span className="text-[11px] font-medium text-teal-800">Optimised Supply Cost</span>
          <div className="text-xl font-bold text-teal-900">{formatINR(optimisedCost)}</div>
          <p className="text-[10px] text-teal-700">Solar + Wind + Biomass + Grid LP dispatch</p>
        </div>

        {/* Daily Savings */}
        <div className={`p-4 rounded-xl border space-y-1 ${
          isPositiveSavings
            ? 'bg-emerald-50/80 border-emerald-200'
            : 'bg-amber-50 border-amber-200'
        }`}>
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-medium text-emerald-800">
              {isPositiveSavings ? 'Modelled Daily Savings' : 'Net Additional Daily Cost'}
            </span>
            <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
              isPositiveSavings ? 'bg-emerald-200 text-emerald-900' : 'bg-amber-200 text-amber-900'
            }`}>
              {isPositiveSavings ? `-${formatPercent(effectiveSavingsPercentage, 1)}` : `+${formatPercent(Math.abs(effectiveSavingsPercentage), 1)}`}
            </span>
          </div>
          <div className={`text-xl font-bold ${isPositiveSavings ? 'text-emerald-900' : 'text-amber-900'}`}>
            {formatINR(Math.abs(effectiveDailySavings))}
            <span className="text-xs font-normal text-slate-500 ml-1">/ day</span>
          </div>
          <p className="text-[10px] text-emerald-700">Daily cost delta from renewable self-consumption</p>
        </div>

        {/* Annualised Savings in Lakhs */}
        <div className={`p-4 rounded-xl border space-y-1 ${
          isPositiveSavings
            ? 'bg-emerald-600 text-white border-emerald-700 shadow-xs'
            : 'bg-slate-800 text-white border-slate-700'
        }`}>
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-medium text-emerald-100">Modelled Annual Savings</span>
            <span className="text-[9px] uppercase tracking-wider font-mono bg-emerald-700/80 px-1.5 py-0.5 rounded text-emerald-100">
              {operatingDays} Days
            </span>
          </div>
          <div className="text-xl font-bold tracking-tight">
            {formatLakhs(Math.abs(annualSavings))}
          </div>
          <div className="text-[10px] text-emerald-100 font-mono">
            {formatINR(Math.abs(annualSavings))} / year
          </div>
        </div>
      </div>

      {/* Assumptions & Disclaimers Footer */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 pt-3 border-t border-slate-100 text-[11px] text-slate-500">
        <div className="flex items-center gap-2">
          <HelpCircle className="w-3.5 h-3.5 text-slate-400 shrink-0" />
          <span>
            <strong>Calculation Basis:</strong> Daily Savings = Baseline Cost (₹{baselineCost?.toFixed(2)}) − Optimised Cost (₹{optimisedCost?.toFixed(2)}). Annualised savings assume {operatingDays} active operating days.
          </span>
        </div>
        {onNavigateToOptimizer && (
          <button
            onClick={onNavigateToOptimizer}
            className="text-teal-700 hover:text-teal-900 font-semibold flex items-center gap-1 shrink-0 transition-colors"
          >
            <span>View Full Dispatch Table</span>
            <ArrowRight className="w-3 h-3" />
          </button>
        )}
      </div>

      {/* Explicit Simulation Disclaimer */}
      <div className="px-3 py-2 rounded-lg bg-amber-50/60 border border-amber-200/60 text-[10px] text-amber-900 flex items-start gap-2">
        <AlertCircle className="w-3.5 h-3.5 text-amber-600 shrink-0 mt-0.5" />
        <span>
          <strong>Simulation Disclaimer:</strong> Modelled scenario projection based on synthetic MSME telemetry and scheduled Time-of-Day tariffs. Actual financial outcomes depend on real plant operating conditions, utility tariff structures, and equipment implementation. Zero-marginal-cost renewable assumptions exclude amortized capital and maintenance expenses.
        </span>
      </div>
    </div>
  );
};

