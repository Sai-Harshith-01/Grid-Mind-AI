import React from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from 'recharts';
import { IntervalSourceAllocation } from '../../types/api';
import { formatHour, formatINR } from '../../utils/formatters';

interface HourlyCostComparisonChartProps {
  intervals: IntervalSourceAllocation[];
}

export const HourlyCostComparisonChart: React.FC<HourlyCostComparisonChartProps> = ({
  intervals,
}) => {
  const chartData = intervals.map((interval) => ({
    hour: formatHour(interval.interval_index),
    baselineCost: interval.baseline_grid_cost_inr,
    optimisedCost: interval.interval_total_cost_inr,
    savings: interval.interval_savings_inr,
  }));

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4">
        <div>
          <h3 className="text-base font-bold text-slate-900 tracking-tight">
            Hourly Supply Cost: Baseline vs Optimised
          </h3>
          <p className="text-xs text-slate-500">
            Comparing 100% grid procurement against multi-source optimal dispatch (₹/hour)
          </p>
        </div>
        <div className="flex items-center gap-4 text-xs">
          <span className="flex items-center gap-1.5 text-slate-600">
            <span className="w-3 h-0.5 bg-rose-500 inline-block"></span>
            100% Grid Baseline
          </span>
          <span className="flex items-center gap-1.5 text-slate-600">
            <span className="w-3 h-0.5 bg-emerald-600 inline-block"></span>
            Optimised Dispatch
          </span>
        </div>
      </div>

      <div className="h-72 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
            <XAxis dataKey="hour" tick={{ fontSize: 11, fill: '#64748b' }} tickLine={false} />
            <YAxis
              tick={{ fontSize: 11, fill: '#64748b' }}
              tickLine={false}
              axisLine={false}
              unit=" ₹"
            />
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const p = payload[0].payload;
                  return (
                    <div className="bg-slate-900 text-white p-3 rounded-lg shadow-xl text-xs space-y-1.5 border border-slate-800">
                      <div className="font-bold text-slate-200 border-b border-slate-800 pb-1">
                        Hour {p.hour}
                      </div>
                      <div className="flex justify-between gap-4 text-rose-300">
                        <span>Grid Baseline:</span>
                        <span className="font-mono font-semibold">{formatINR(p.baselineCost)}</span>
                      </div>
                      <div className="flex justify-between gap-4 text-emerald-300">
                        <span>Optimised Cost:</span>
                        <span className="font-mono font-semibold">{formatINR(p.optimisedCost)}</span>
                      </div>
                      <div className="pt-1 border-t border-slate-800 flex justify-between gap-4 font-mono text-teal-300 font-bold">
                        <span>Hourly Savings:</span>
                        <span>{formatINR(p.savings)}</span>
                      </div>
                    </div>
                  );
                }
                return null;
              }}
            />
            <Line
              type="monotone"
              dataKey="baselineCost"
              stroke="#f43f5e"
              strokeWidth={2}
              strokeDasharray="4 4"
              dot={false}
            />
            <Line
              type="monotone"
              dataKey="optimisedCost"
              stroke="#059669"
              strokeWidth={2.5}
              dot={{ r: 3, fill: '#059669' }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
