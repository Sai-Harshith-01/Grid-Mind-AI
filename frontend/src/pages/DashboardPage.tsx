import React from 'react';
import {
  Zap,
  TrendingDown,
  Layers,
  SunMedium,
  Gauge,
  IndianRupee,
  Factory,
  Cpu,
} from 'lucide-react';
import {
  FactoryProfileResponse,
  FactoryTimeSeriesResponse,
  EnergyMetricsSummaryResponse,
  OptimizationSummaryResponse,
  OptimizationRunResponse,
  DetectedAnomalyFinding,
  AnalyticalEnergyProfileResponse,
} from '../types/api';
import { KpiCard } from '../components/ui/KpiCard';
import { DemandTariffChart } from '../components/charts/DemandTariffChart';
import { ZoneDemandChart } from '../components/charts/ZoneDemandChart';
import { RenewableAvailabilityChart } from '../components/charts/RenewableAvailabilityChart';
import { HourlyCostComparisonChart } from '../components/charts/HourlyCostComparisonChart';
import { AnomalyAlertsSection } from '../components/dashboard/AnomalyAlertsSection';
import { VerifiedSavingsCalculator } from '../components/dashboard/VerifiedSavingsCalculator';
import {
  formatINR,
  formatKW,
  formatKWH,
  formatPercent,
} from '../utils/formatters';


interface DashboardPageProps {
  profile: FactoryProfileResponse | null;
  timeseries: FactoryTimeSeriesResponse | null;
  metrics: EnergyMetricsSummaryResponse | null;
  analyticalProfile: AnalyticalEnergyProfileResponse | null;
  optSummary: OptimizationSummaryResponse | null;
  optRun: OptimizationRunResponse | null;
  anomalies: DetectedAnomalyFinding[];
  onInvestigateAnomaly: (anomalyId: string) => void;
  onNavigateToSimulator: () => void;
}

export const DashboardPage: React.FC<DashboardPageProps> = ({
  profile,
  timeseries,
  metrics,
  analyticalProfile,
  optSummary,
  optRun,
  anomalies,
  onInvestigateAnomaly,
  onNavigateToSimulator,
}) => {
  const demandKwh = metrics?.demand_metrics.total_demand_kwh ?? null;
  const peakKw = metrics?.demand_metrics.peak_power_kw ?? null;
  const productionUnits = metrics?.demand_metrics.total_production_units ?? null;
  const intensity = metrics?.demand_metrics.overall_energy_intensity_kwh_per_unit ?? null;
  
  // Distinguish available renewable energy from allocated renewable energy
  const availRenewableKwh = metrics?.renewable_availability.total_renewable_available_kwh ?? null;
  const allocatedRenewableKwh = optSummary?.renewable_energy_allocated_kwh ?? null;
  const renewableSharePercent = optSummary?.renewable_allocation_percentage ?? null;

  // Financial values labelled as estimates
  const baselineCost = optSummary?.baseline_grid_only_cost_inr ?? null;
  const optimisedCost = optSummary?.optimised_supply_cost_inr ?? null;
  const estimatedSavings = optSummary?.estimated_savings_inr ?? null;
  const savingsPercent = optSummary?.estimated_savings_percentage ?? null;

  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto">
      {/* Synthetic Warning Banner */}
      <div className="bg-gradient-to-r from-amber-50 to-orange-50 border border-amber-200/80 rounded-xl p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-xs">
        <div className="flex items-center gap-2.5 text-amber-900 font-medium">
          <span className="w-2 h-2 rounded-full bg-amber-500 animate-pulse"></span>
          <span>
            <strong>Deterministic Prototype Simulation:</strong> Telemetry, weather availability, and machine power curves are synthetic MSME models for evaluation.
          </span>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <button
            onClick={onNavigateToSimulator}
            className="text-amber-800 hover:text-amber-950 font-semibold underline transition-colors"
          >
            Launch Simulator →
          </button>
          <span className="font-mono text-amber-700 bg-amber-100/70 px-2 py-0.5 rounded border border-amber-200/60">
            Fixed Seed #42
          </span>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard
          label="Total Factory Demand"
          value={formatKWH(demandKwh)}
          subtext={`Avg. Load: ${metrics?.demand_metrics.average_power_kw?.toFixed(1) || '—'} kW`}
          icon={Zap}
          accent="default"
        />

        <KpiCard
          label="Peak Demand Rate"
          value={formatKW(peakKw)}
          subtext={`Sanctioned Limit: ${profile?.grid.contract_demand_kw || 250} kW`}
          badge={
            peakKw && profile?.grid.contract_demand_kw
              ? `${((peakKw / profile.grid.contract_demand_kw) * 100).toFixed(0)}% Utilisation`
              : undefined
          }
          badgeColor="amber"
          icon={Gauge}
          accent="amber"
        />

        <KpiCard
          label="Energy Intensity"
          value={intensity !== null ? `${intensity.toFixed(2)} kWh/unit` : '—'}
          subtext={`Total Output: ${productionUnits?.toLocaleString('en-IN') || '—'} units`}
          icon={Factory}
          accent="blue"
        />

        <KpiCard
          label="Renewables Available"
          value={formatKWH(availRenewableKwh)}
          subtext={`Allocated by LP: ${formatKWH(allocatedRenewableKwh)}`}
          badge={renewableSharePercent !== null ? `${renewableSharePercent.toFixed(1)}% Demand` : undefined}
          badgeColor="teal"
          icon={SunMedium}
          accent="teal"
        />

        <KpiCard
          label="100% Grid Reference Baseline"
          value={formatINR(baselineCost)}
          subtext="Assuming zero renewable self-consumption"
          icon={IndianRupee}
          accent="default"
          isEstimate
        />

        <KpiCard
          label="Optimised Supply Cost"
          value={formatINR(optimisedCost)}
          subtext="HiGHS multi-source merit order dispatch"
          icon={Cpu}
          accent="emerald"
          badge="HiGHS LP"
          badgeColor="emerald"
          isEstimate
        />

        <KpiCard
          label="Modelled Daily Savings"
          value={formatINR(estimatedSavings)}
          subtext={savingsPercent !== null ? `${savingsPercent.toFixed(1)}% reduction vs baseline` : 'Scenario estimate'}
          icon={TrendingDown}
          accent="emerald"
          badge={savingsPercent !== null ? `-${savingsPercent.toFixed(0)}%` : undefined}
          badgeColor="emerald"
          isEstimate
        />

        <KpiCard
          label="Renewable Allocation Share"
          value={formatPercent(renewableSharePercent)}
          subtext={`Grid Share: ${optSummary?.grid_energy_share_percentage?.toFixed(1) || '—'}%`}
          icon={Layers}
          accent="teal"
          badge="Self-Consumption"
          badgeColor="teal"
        />
      </section>

      {/* Modelled Savings Calculator Section */}
      <section>
        <VerifiedSavingsCalculator
          baselineCost={baselineCost}
          optimisedCost={optimisedCost}
          dailySavings={estimatedSavings}
          savingsPercentage={savingsPercent}
          onNavigateToOptimizer={onNavigateToSimulator}
          factoryName={profile?.name}
          isScenarioActive={false}
          scenarioName="Standard Baseline"
          isCapacityFeasible={optSummary?.baseline_is_capacity_feasible ?? true}
        />
      </section>

      {/* Energy Consumption Charts Grid */}
      <section className="grid grid-cols-1 lg:grid-cols-2 gap-6">

        {analyticalProfile && (
          <DemandTariffChart data={analyticalProfile.hourly_profile} />
        )}

        {timeseries && (
          <ZoneDemandChart intervals={timeseries.intervals} />
        )}

        {analyticalProfile && (
          <RenewableAvailabilityChart data={analyticalProfile.hourly_profile} />
        )}

        {optRun && (
          <HourlyCostComparisonChart intervals={optRun.intervals} />
        )}
      </section>

      {/* Anomaly Alerts Section */}
      <section>
        <AnomalyAlertsSection
          findings={anomalies}
          onInvestigate={onInvestigateAnomaly}
        />
      </section>
    </div>
  );
};
