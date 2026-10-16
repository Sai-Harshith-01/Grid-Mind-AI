import React from 'react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from 'recharts';
import { IntervalSourceAllocation } from '../../types/api';
import { formatHour, formatINR } from '../../utils/formatters';

interface OptimizedDispatchChartProps {
  intervals: IntervalSourceAllocation[];
}

export const OptimizedDispatchChart: React.FC<OptimizedDispatchChartProps> = ({ intervals }) => {
  const chartData = intervals.map((interval) => ({
    hour: formatHour(interval.interval_index),
    solar: interval.solar_allocated_kwh,
    wind: interval.wind_allocated_kwh,
    biomass: interval.biomass_allocated_kwh,
    grid: interval.grid_allocated_kwh,
    demand: interval.factory_demand_kwh,
    cost: interval.interval_total_cost_inr,
    savings: interval.interval_savings_inr,
    tariff: interval.grid_tariff_inr_per_kwh,
  }));

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4">
        <div>
          <h3 className="text-base font-bold text-slate-900 tracking-tight">
            Hourly Multi-Source Dispatch Allocation (LP Solution)
          </h3>
          <p className="text-xs text-slate-500">
            Optimal merit-order mix: Solar & Wind (₹0) → Biomass (₹4.20) → ToD Grid (₹6.50–₹11.80)
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-3 text-xs">
          <span className="flex items-center gap-1.5 text-slate-600">
            <span className="w-3 h-3 rounded bg-amber-400 inline-block"></span>
            Solar
          </span>
          <span className="flex items-center gap-1.5 text-slate-600">
            <span className="w-3 h-3 rounded bg-cyan-400 inline-block"></span>
            Wind
          </span>
          <span className="flex items-center gap-1.5 text-slate-600">
            <span className="w-3 h-3 rounded bg-emerald-500 inline-block"></span>
            Biomass
          </span>
          <span className="flex items-center gap-1.5 text-slate-600">
            <span className="w-3 h-3 rounded bg-slate-500 inline-block"></span>
            Utility Grid
          </span>
        </div>
      </div>

      <div className="h-80 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
            <XAxis dataKey="hour" tick={{ fontSize: 11, fill: '#64748b' }} tickLine={false} />
            <YAxis
              tick={{ fontSize: 11, fill: '#64748b' }}
              tickLine={false}
              axisLine={false}
              unit=" kWh"
            />
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const p = payload[0].payload;
                  return (
                    <div className="bg-slate-900 text-white p-3.5 rounded-lg shadow-xl text-xs space-y-1.5 border border-slate-800 min-w-[200px]">
                      <div className="font-bold text-slate-200 border-b border-slate-800 pb-1 flex justify-between items-center">
                        <span>Hour {p.hour}</span>
                        <span className="font-mono text-teal-400">Demand: {p.demand.toFixed(1)} kWh</span>
                      </div>
                      <div className="space-y-1 pt-0.5">
                        <div className="flex justify-between gap-4 text-amber-300">
                          <span>Solar Dispatched:</span>
                          <span className="font-mono">{p.solar.toFixed(1)} kWh</span>
                        </div>
                        <div className="flex justify-between gap-4 text-cyan-300">
                          <span>Wind Dispatched:</span>
                          <span className="font-mono">{p.wind.toFixed(1)} kWh</span>
                        </div>
                        <div className="flex justify-between gap-4 text-emerald-300">
                          <span>Biomass Dispatched:</span>
                          <span className="font-mono">{p.biomass.toFixed(1)} kWh</span>
                        </div>
                        <div className="flex justify-between gap-4 text-slate-300">
                          <span>Grid Import:</span>
                          <span className="font-mono font-semibold">{p.grid.toFixed(1)} kWh</span>
                        </div>
                      </div>
                      <div className="pt-1.5 border-t border-slate-800 flex justify-between items-center font-mono">
                        <span className="text-slate-400">Interval Cost:</span>
                        <span className="text-white font-bold">{formatINR(p.cost)}</span>
                      </div>
                      <div className="flex justify-between items-center font-mono text-[11px]">
                        <span className="text-emerald-400">Est. Savings:</span>
                        <span className="text-emerald-400 font-semibold">{formatINR(p.savings)}</span>
                      </div>
                    </div>
                  );
                }
                return null;
              }}
            />
            <Bar dataKey="solar" stackId="a" fill="#f59e0b" />
            <Bar dataKey="wind" stackId="a" fill="#06b6d4" />
            <Bar dataKey="biomass" stackId="a" fill="#10b981" />
            <Bar dataKey="grid" stackId="a" fill="#64748b" radius={[3, 3, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
