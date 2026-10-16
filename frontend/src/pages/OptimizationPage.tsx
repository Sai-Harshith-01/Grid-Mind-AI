import React, { useState, useEffect } from 'react';
import {
  Sliders,
  TrendingDown,
  Zap,
  CheckCircle2,
  AlertTriangle,
  RotateCw,
  Gauge,
  IndianRupee,
  Fuel,
  Info,
  Sparkles,
  Undo2,
} from 'lucide-react';
import {
  FactoryProfileResponse,
  OptimizationSummaryResponse,
  OptimizationRunResponse,
} from '../types/api';
import { runOptimization } from '../api';
import { KpiCard } from '../components/ui/KpiCard';
import { OptimizedDispatchChart } from '../components/charts/OptimizedDispatchChart';
import { HourlyCostComparisonChart } from '../components/charts/HourlyCostComparisonChart';
import { VerifiedSavingsCalculator } from '../components/dashboard/VerifiedSavingsCalculator';
import {
  formatINR,
  formatKW,
  formatKWH,
  formatPercent,
} from '../utils/formatters';

interface OptimizationPageProps {
  profile: FactoryProfileResponse | null;
  optSummary: OptimizationSummaryResponse | null;
  optRun: OptimizationRunResponse | null;
  onRefreshOptimization: () => Promise<void>;
  selectedFactoryId?: string;
}

export const OptimizationPage: React.FC<OptimizationPageProps> = ({
  profile,
  optSummary,
  optRun,
  onRefreshOptimization,
  selectedFactoryId = 'DEMO-FAC-001',
}) => {
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [runMessage, setRunMessage] = useState<string | null>(null);

  // What-If Scenario State
  const [solarFactor, setSolarFactor] = useState<number>(100); // 0% to 200%
  const [tariffFactor, setTariffFactor] = useState<number>(100); // 50% to 200%
  const [customOptRun, setCustomOptRun] = useState<OptimizationRunResponse | null>(null);
  const [customOptSummary, setCustomOptSummary] = useState<OptimizationSummaryResponse | null>(null);
  const [isScenarioActive, setIsScenarioActive] = useState<boolean>(false);

  // Reset custom scenario when factory profile changes or selected factory changes
  useEffect(() => {
    setSolarFactor(100);
    setTariffFactor(100);
    setCustomOptRun(null);
    setCustomOptSummary(null);
    setIsScenarioActive(false);
  }, [profile?.factory_id, selectedFactoryId]);

  const activeOptRun = customOptRun || optRun;
  const activeOptSummary = customOptSummary || optSummary;

  const handleRunStandard = async () => {
    setIsRunning(true);
    setRunMessage(null);
    try {
      await onRefreshOptimization();
      setSolarFactor(100);
      setTariffFactor(100);
      setCustomOptRun(null);
      setCustomOptSummary(null);
      setIsScenarioActive(false);
      setRunMessage('HiGHS Linear Programming optimization re-solved under standard conditions.');
    } catch (err) {
      setRunMessage(err instanceof Error ? err.message : 'Optimization failed');
    } finally {
      setIsRunning(false);
    }
  };

  const handleSimulateScenario = async (solarPct = solarFactor, tariffPct = tariffFactor) => {
    setIsRunning(true);
    setRunMessage(null);
    try {
      const sMult = solarPct / 100;
      const tMult = tariffPct / 100;
      const runResult = await runOptimization(selectedFactoryId, {
        solarMultiplier: sMult,
        tariffMultiplier: tMult,
      });
      setCustomOptRun(runResult);
      setCustomOptSummary(runResult);
      setIsScenarioActive(sMult !== 1.0 || tMult !== 1.0);
      setRunMessage(
        `HiGHS Scenario solved: Solar at ${solarPct}%, Grid Tariffs at ${tariffPct}%. Estimated savings: ${formatINR(
          runResult.estimated_savings_inr
        )}/day.`
      );
    } catch (err) {
      setRunMessage(err instanceof Error ? err.message : 'Scenario simulation failed');
    } finally {
      setIsRunning(false);
    }
  };

  const handleApplyPreset = (solarPct: number, tariffPct: number) => {
    setSolarFactor(solarPct);
    setTariffFactor(tariffPct);
    handleSimulateScenario(solarPct, tariffPct);
  };

  const handleResetScenario = () => {
    setSolarFactor(100);
    setTariffFactor(100);
    setCustomOptRun(null);
    setCustomOptSummary(null);
    setIsScenarioActive(false);
    setRunMessage('Reset to standard operating conditions (100% solar, 100% grid tariff).');
  };

  const contractDemandKw = profile?.grid.contract_demand_kw || 250;
  const peakGridKw = activeOptSummary?.peak_grid_power_kw || 0;
  const headroomKw = contractDemandKw - peakGridKw;

  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto">
      {/* Simulator Control Header */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="p-1 rounded bg-teal-50 text-teal-700">
              <Sliders className="w-4 h-4 text-teal-600" />
            </span>
            <h2 className="text-lg font-bold text-slate-900 tracking-tight">
              Deterministic Renewable Dispatch Optimiser
            </h2>
            <span className="text-[11px] font-mono bg-emerald-50 text-emerald-700 px-2 py-0.5 rounded border border-emerald-200">
              SciPy HiGHS Solver
            </span>
            {isScenarioActive && (
              <span className="text-[11px] font-mono bg-amber-50 text-amber-700 px-2 py-0.5 rounded border border-amber-200 animate-pulse">
                What-If Scenario Active
              </span>
            )}
          </div>
          <p className="text-xs text-slate-500 max-w-2xl leading-relaxed">
            Minimises hourly energy procurement spend across Solar (₹0/kWh), Wind (₹0/kWh), Biomass (₹4.20/kWh), and Time-of-Day utility grid electricity (₹6.50–₹11.80/kWh), subject to equipment limits and daily fuel budgets.
          </p>
        </div>

        {/* Action Button: Run Standard Optimisation */}
        <button
          onClick={handleRunStandard}
          disabled={isRunning}
          className="flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg bg-teal-600 hover:bg-teal-700 text-white disabled:opacity-50 text-xs font-semibold shadow-sm transition-all active:scale-95 shrink-0"
        >
          <RotateCw className={`w-3.5 h-3.5 ${isRunning ? 'animate-spin' : ''}`} />
          <span>{isRunning ? 'Solving Linear Program...' : 'Re-Run Standard Dispatch'}</span>
        </button>
      </div>

      {runMessage && (
        <div className="p-3.5 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-xl text-xs flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
            <span>{runMessage}</span>
          </div>
          <button onClick={() => setRunMessage(null)} className="text-emerald-700 font-bold hover:underline">
            Dismiss
          </button>
        </div>
      )}

      {/* Interactive What-If Scenario Panel */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm space-y-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-3">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-amber-500" />
            <div>
              <h3 className="text-sm font-bold text-slate-900">
                Interactive What-If Scenario Simulator
              </h3>
              <p className="text-[11px] text-slate-500">
                Adjust factory operating bounds and re-solve the HiGHS linear program in real time.
              </p>
            </div>
          </div>
          {isScenarioActive && (
            <button
              onClick={handleResetScenario}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-medium transition-colors"
            >
              <Undo2 className="w-3.5 h-3.5" />
              <span>Reset to Defaults</span>
            </button>
          )}
        </div>

        {/* Sliders Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Solar Availability Slider */}
          <div className="space-y-2 p-4 rounded-lg bg-slate-50/70 border border-slate-200/80">
            <div className="flex items-center justify-between">
              <label className="text-xs font-semibold text-slate-800 flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-amber-400"></span>
                Solar Generation Availability
              </label>
              <div className="flex items-center gap-1.5">
                <span className="font-mono text-xs font-bold text-amber-700 bg-amber-50 px-2 py-0.5 rounded border border-amber-200">
                  {solarFactor}%
                </span>
                <span className="text-[10px] text-slate-400">
                  {solarFactor === 100
                    ? '(Normal)'
                    : solarFactor < 70
                    ? '(Monsoon/Overcast)'
                    : '(Expanded Solar)'}
                </span>
              </div>
            </div>
            <input
              type="range"
              min="0"
              max="200"
              step="10"
              value={solarFactor}
              onChange={(e) => setSolarFactor(Number(e.target.value))}
              className="w-full accent-amber-500 cursor-pointer h-1.5 bg-slate-200 rounded-lg appearance-none"
            />
            <div className="flex justify-between text-[10px] text-slate-400 font-mono">
              <span>0% (Heavy Rain / Night)</span>
              <span>100% (Baseline)</span>
              <span>200% (2x Array)</span>
            </div>
          </div>

          {/* Grid Tariff Slider */}
          <div className="space-y-2 p-4 rounded-lg bg-slate-50/70 border border-slate-200/80">
            <div className="flex items-center justify-between">
              <label className="text-xs font-semibold text-slate-800 flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-teal-500"></span>
                Grid Tariff Adjustment
              </label>
              <div className="flex items-center gap-1.5">
                <span className="font-mono text-xs font-bold text-teal-700 bg-teal-50 px-2 py-0.5 rounded border border-teal-200">
                  {tariffFactor}%
                </span>
                <span className="text-[10px] text-slate-400">
                  {tariffFactor === 100
                    ? '(Standard ToD)'
                    : tariffFactor > 115
                    ? '(Peak Surcharge)'
                    : '(Off-Peak Discount)'}
                </span>
              </div>
            </div>
            <input
              type="range"
              min="50"
              max="200"
              step="5"
              value={tariffFactor}
              onChange={(e) => setTariffFactor(Number(e.target.value))}
              className="w-full accent-teal-600 cursor-pointer h-1.5 bg-slate-200 rounded-lg appearance-none"
            />
            <div className="flex justify-between text-[10px] text-slate-400 font-mono">
              <span>50% (Subsidy)</span>
              <span>100% (Standard)</span>
              <span>200% (High Surcharge)</span>
            </div>
          </div>
        </div>

        {/* Preset Buttons & Simulate Trigger */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-2">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-[11px] font-medium text-slate-500 mr-1">Scenario Presets:</span>
            <button
              onClick={handleResetScenario}
              className={`px-2.5 py-1 text-[11px] rounded border transition-colors ${
                !isScenarioActive
                  ? 'bg-teal-50 text-teal-800 border-teal-300 font-semibold'
                  : 'bg-white hover:bg-slate-100 text-slate-700 border-slate-200'
              }`}
            >
              Standard (100% / 100%)
            </button>
            <button
              onClick={() => handleApplyPreset(40, 100)}
              className="px-2.5 py-1 text-[11px] rounded bg-white hover:bg-slate-100 text-slate-700 border border-slate-200 transition-colors"
            >
              Monsoon / Overcast (40% Solar)
            </button>
            <button
              onClick={() => handleApplyPreset(100, 125)}
              className="px-2.5 py-1 text-[11px] rounded bg-white hover:bg-slate-100 text-slate-700 border border-slate-200 transition-colors"
            >
              Summer Peak (+25% Tariff)
            </button>
            <button
              onClick={() => handleApplyPreset(150, 100)}
              className="px-2.5 py-1 text-[11px] rounded bg-white hover:bg-slate-100 text-slate-700 border border-slate-200 transition-colors"
            >
              Rooftop Expansion (150% Solar)
            </button>
          </div>

          <button
            onClick={() => handleSimulateScenario()}
            disabled={isRunning}
            className="inline-flex items-center justify-center gap-2 px-4 py-2 rounded-lg bg-slate-900 hover:bg-slate-800 text-white disabled:opacity-50 text-xs font-semibold shadow-xs transition-all shrink-0"
          >
            <RotateCw className={`w-3.5 h-3.5 ${isRunning ? 'animate-spin' : ''}`} />
            <span>{isRunning ? 'Solving Scenario...' : 'Simulate Scenario (HiGHS LP)'}</span>
          </button>
        </div>
      </div>

      {/* Solver Feasibility & Status Banner */}
      <div className="bg-slate-900 text-white rounded-xl p-4 shadow-sm border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
        <div className="flex items-center gap-2.5">
          {activeOptSummary?.is_feasible ? (
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
          ) : (
            <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
          )}
          <span>
            <strong>Solver Status:</strong> {activeOptSummary?.solver_status || 'HiGHS LP Solved Optimal'}
          </span>
          <span className="text-slate-400">|</span>
          <span className="text-slate-300">
            {activeOptSummary?.infeasible_intervals_count || 0} Infeasible Intervals
          </span>
        </div>
        <div className="flex items-center gap-3 font-mono text-[11px] text-slate-400">
          <span>Demand Served: {formatKWH(activeOptSummary?.total_demand_served_kwh)}</span>
          <span>•</span>
          <span className="text-teal-400 font-semibold">
            Renewable: {formatPercent(activeOptSummary?.renewable_allocation_percentage)}
          </span>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard
          label={isScenarioActive ? 'What-If Grid Baseline Cost' : '100% Grid Baseline Cost'}
          value={formatINR(activeOptSummary?.baseline_grid_only_cost_inr)}
          subtext={
            isScenarioActive
              ? `Recalculated under active scenario (${tariffFactor}% tariff)`
              : 'Reference cost if zero renewables self-consumed'
          }
          icon={IndianRupee}
          accent="default"
          badge={isScenarioActive ? `${tariffFactor}% Tariff` : undefined}
          badgeColor="amber"
          isEstimate
        />

        <KpiCard
          label={isScenarioActive ? 'What-If Optimised Cost' : 'Optimised Multi-Source Cost'}
          value={formatINR(activeOptSummary?.optimised_supply_cost_inr)}
          subtext={
            isScenarioActive
              ? `HiGHS mix with ${solarFactor}% solar & ${tariffFactor}% tariff`
              : 'Solar + Wind + Biomass + Grid optimal mix'
          }
          icon={Zap}
          accent="emerald"
          badge={isScenarioActive ? 'Scenario LP' : 'HiGHS LP'}
          badgeColor="emerald"
          isEstimate
        />

        <KpiCard
          label={isScenarioActive ? 'Scenario Daily Savings' : 'Estimated Daily Savings'}
          value={formatINR(activeOptSummary?.estimated_savings_inr)}
          subtext={`${formatPercent(activeOptSummary?.estimated_savings_percentage)} reduction against baseline`}
          icon={TrendingDown}
          accent="emerald"
          badge={
            activeOptSummary?.estimated_savings_percentage
              ? `-${activeOptSummary.estimated_savings_percentage.toFixed(0)}%`
              : undefined
          }
          badgeColor="emerald"
          isEstimate
        />

        <KpiCard
          label="Peak Grid Demand Draw"
          value={formatKW(peakGridKw)}
          subtext={`Headroom: ${formatKW(headroomKw)} under ${contractDemandKw} kW cap`}
          icon={Gauge}
          accent="amber"
          badge={
            activeOptSummary?.peak_grid_contract_utilisation_percent
              ? `${activeOptSummary.peak_grid_contract_utilisation_percent.toFixed(0)}% Cap`
              : undefined
          }
          badgeColor="amber"
        />
      </section>

      {/* Modelled Savings Calculator */}
      <section>
        <VerifiedSavingsCalculator
          baselineCost={activeOptSummary?.baseline_grid_only_cost_inr}
          optimisedCost={activeOptSummary?.optimised_supply_cost_inr}
          dailySavings={activeOptSummary?.estimated_savings_inr}
          savingsPercentage={activeOptSummary?.estimated_savings_percentage}
          factoryName={profile?.name}
          isScenarioActive={isScenarioActive}
          scenarioName={
            isScenarioActive
              ? `What-If: Solar ${solarFactor}%, Tariff ${tariffFactor}%`
              : 'Standard Baseline'
          }
          isCapacityFeasible={activeOptSummary?.baseline_is_capacity_feasible ?? true}
          onResetScenario={handleResetScenario}
        />
      </section>

      {/* Optimization Charts Grid */}
      <section className="space-y-6">
        {activeOptRun && (
          <OptimizedDispatchChart intervals={activeOptRun.intervals} />
        )}

        {activeOptRun && (
          <HourlyCostComparisonChart intervals={activeOptRun.intervals} />
        )}
      </section>

      {/* Operational Constraints & Asset Utilization Breakdown */}
      <section className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Grid Sanctioned Capacity Card */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-3">
          <div className="flex items-center justify-between pb-2 border-b border-slate-100">
            <span className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-1.5">
              <Gauge className="w-3.5 h-3.5 text-amber-500" />
              Grid Contract Demand
            </span>
            <span className="text-xs font-mono font-bold text-slate-900">
              {contractDemandKw} kW Limit
            </span>
          </div>

          <div className="space-y-2 text-xs">
            <div className="flex justify-between text-slate-600">
              <span>Peak Allocated Grid Power:</span>
              <span className="font-mono font-bold text-slate-900">{formatKW(peakGridKw)}</span>
            </div>
            <div className="flex justify-between text-slate-600">
              <span>Safety Headroom:</span>
              <span className="font-mono font-bold text-emerald-600">+{formatKW(headroomKw)}</span>
            </div>
            <div className="flex justify-between text-slate-600">
              <span>Capacity Utilisation:</span>
              <span className="font-mono font-bold text-amber-600">
                {formatPercent(activeOptSummary?.peak_grid_contract_utilisation_percent)}
              </span>
            </div>
          </div>

          <div className="pt-2 border-t border-slate-100 text-[11px] text-slate-500">
            Grid peak draw reduced from {contractDemandKw} kW down to {peakGridKw.toFixed(1)} kW, eliminating contract demand penalties.
          </div>
        </div>

        {/* Biomass Fuel Consumption & Stock */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-3">
          <div className="flex items-center justify-between pb-2 border-b border-slate-100">
            <span className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-1.5">
              <Fuel className="w-3.5 h-3.5 text-emerald-600" />
              Biomass Gasifier Fuel
            </span>
            <span className="text-xs font-mono font-bold text-emerald-700">
              {profile?.biomass.generator_capacity_kw || 50} kW / {profile?.biomass.stock_kg || 250} kg
            </span>
          </div>

          <div className="space-y-2 text-xs">
            <div className="flex justify-between text-slate-600">
              <span>Electricity Dispatched:</span>
              <span className="font-mono font-bold text-slate-900">
                {formatKWH(activeOptSummary?.biomass_energy_consumed_kwh)}
              </span>
            </div>
            <div className="flex justify-between text-slate-600">
              <span>Briquette Fuel Consumed:</span>
              <span className="font-mono font-bold text-slate-900">
                {activeOptSummary?.biomass_fuel_consumed_kg?.toFixed(1) || '0.0'} kg
              </span>
            </div>
            <div className="flex justify-between text-slate-600">
              <span>Remaining Fuel Stock:</span>
              <span className="font-mono font-bold text-slate-500">
                {activeOptSummary?.biomass_remaining_fuel_budget_kg?.toFixed(1) || '0.0'} kg
              </span>
            </div>
          </div>

          <div className="pt-2 border-t border-slate-100 text-[11px] text-slate-500">
            Biomass was dispatched to displace expensive grid electricity during evening peak tariff hours (₹11.80/kWh).
          </div>
        </div>

        {/* Merit Order Dispatch Architecture */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-3">
          <div className="flex items-center justify-between pb-2 border-b border-slate-100">
            <span className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-1.5">
              <Info className="w-3.5 h-3.5 text-teal-600" />
              Merit-Order Rules
            </span>
            <span className="text-xs font-mono font-bold text-teal-700">
              HiGHS LP
            </span>
          </div>

          <div className="space-y-1.5 text-xs text-slate-600">
            <div className="flex items-center gap-2">
              <span className="w-4 h-4 rounded-full bg-amber-100 text-amber-800 text-[10px] font-bold flex items-center justify-center">
                1
              </span>
              <span>Solar & Wind (₹0.00/kWh) — Zero marginal cost</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-4 h-4 rounded-full bg-emerald-100 text-emerald-800 text-[10px] font-bold flex items-center justify-center">
                2
              </span>
              <span>Biomass (₹{profile?.biomass.marginal_cost_inr_per_kwh?.toFixed(2) || '4.20'}/kWh) — Fuel constrained</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-4 h-4 rounded-full bg-slate-100 text-slate-800 text-[10px] font-bold flex items-center justify-center">
                3
              </span>
              <span>Utility Grid (₹6.50–₹11.80) — Remaining demand</span>
            </div>
          </div>

          <div className="pt-2 border-t border-slate-100 text-[11px] text-slate-400 italic">
            *All savings are scenario estimates derived from simulated dispatch models.
          </div>
        </div>
      </section>
    </div>
  );
};
