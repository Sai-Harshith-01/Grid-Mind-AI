import React from 'react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from 'recharts';
import { TimeSeriesInterval } from '../../types/api';
import { formatHour } from '../../utils/formatters';

interface ZoneDemandChartProps {
  intervals: TimeSeriesInterval[];
}

export const ZoneDemandChart: React.FC<ZoneDemandChartProps> = ({ intervals }) => {
  const chartData = intervals.map((interval) => {
    const cncZone = interval.zones.find((z) => z.zone_id.includes('cnc'));
    const heatZone = interval.zones.find((z) => z.zone_id.includes('heat'));
    const assemblyZone = interval.zones.find((z) => z.zone_id.includes('assembly'));

    return {
      hour: formatHour(interval.interval_index),
      cncKw: cncZone?.power_kw || 0,
      heatKw: heatZone?.power_kw || 0,
      assemblyKw: assemblyZone?.power_kw || 0,
      totalKw: interval.total_factory_demand_kw,
    };
  });

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4">
        <div>
          <h3 className="text-base font-bold text-slate-900 tracking-tight">
            Demand Breakdown by Production Zone
          </h3>
          <p className="text-xs text-slate-500">
            Stacked active power draw (kW) across CNC Machining, Heat Treatment, and Assembly
          </p>
        </div>
        <div className="flex items-center gap-3 text-xs">
          <span className="flex items-center gap-1.5 text-slate-600">
            <span className="w-3 h-3 rounded bg-indigo-500 inline-block"></span>
            CNC & Machining
          </span>
          <span className="flex items-center gap-1.5 text-slate-600">
            <span className="w-3 h-3 rounded bg-amber-500 inline-block"></span>
            Heat Treatment
          </span>
          <span className="flex items-center gap-1.5 text-slate-600">
            <span className="w-3 h-3 rounded bg-teal-500 inline-block"></span>
            Assembly
          </span>
        </div>
      </div>

      <div className="h-72 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
            <XAxis dataKey="hour" tick={{ fontSize: 11, fill: '#64748b' }} tickLine={false} />
            <YAxis
              tick={{ fontSize: 11, fill: '#64748b' }}
              tickLine={false}
              axisLine={false}
              unit=" kW"
            />
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const p = payload[0].payload;
                  return (
                    <div className="bg-slate-900 text-white p-3 rounded-lg shadow-xl text-xs space-y-1.5 border border-slate-800">
                      <div className="font-bold text-slate-200 border-b border-slate-800 pb-1 flex justify-between gap-4">
                        <span>Hour {p.hour}</span>
                        <span className="font-mono text-teal-400">Total: {p.totalKw.toFixed(1)} kW</span>
                      </div>
                      <div className="flex justify-between gap-4 text-slate-300">
                        <span className="text-indigo-400">CNC Machining:</span>
                        <span className="font-mono">{p.cncKw.toFixed(1)} kW</span>
                      </div>
                      <div className="flex justify-between gap-4 text-slate-300">
                        <span className="text-amber-400">Heat Treatment:</span>
                        <span className="font-mono">{p.heatKw.toFixed(1)} kW</span>
                      </div>
                      <div className="flex justify-between gap-4 text-slate-300">
                        <span className="text-teal-400">Assembly:</span>
                        <span className="font-mono">{p.assemblyKw.toFixed(1)} kW</span>
                      </div>
                    </div>
                  );
                }
                return null;
              }}
            />
            <Area
              type="monotone"
              dataKey="cncKw"
              stackId="1"
              stroke="#6366f1"
              fill="#818cf8"
              fillOpacity={0.6}
            />
            <Area
              type="monotone"
              dataKey="heatKw"
              stackId="1"
              stroke="#d97706"
              fill="#fbbf24"
              fillOpacity={0.6}
            />
            <Area
              type="monotone"
              dataKey="assemblyKw"
              stackId="1"
              stroke="#0d9488"
              fill="#2dd4bf"
              fillOpacity={0.6}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
