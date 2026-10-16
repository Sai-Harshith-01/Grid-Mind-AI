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
import { HourlyAnalyticalProfileItem } from '../../types/api';
import { formatHour } from '../../utils/formatters';

interface RenewableAvailabilityChartProps {
  data: HourlyAnalyticalProfileItem[];
}

export const RenewableAvailabilityChart: React.FC<RenewableAvailabilityChartProps> = ({
  data,
}) => {
  const chartData = data.map((item) => ({
    hour: formatHour(item.interval_index),
    solarKwh: item.solar_available_kwh,
    windKwh: item.wind_available_kwh,
    biomassKwh: item.biomass_available_kwh,
    totalRenewableKwh: item.total_renewable_available_kwh,
  }));

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4">
        <div>
          <h3 className="text-base font-bold text-slate-900 tracking-tight">
            Renewable Generation Potential (Availability)
          </h3>
          <p className="text-xs text-slate-500">
            Simulated generation availability by source before dispatch allocation (kWh/hour)
          </p>
        </div>
        <div className="flex items-center gap-3 text-xs">
          <span className="flex items-center gap-1.5 text-slate-600">
            <span className="w-3 h-3 rounded bg-amber-400 inline-block"></span>
            Solar PV
          </span>
          <span className="flex items-center gap-1.5 text-slate-600">
            <span className="w-3 h-3 rounded bg-cyan-400 inline-block"></span>
            Wind Turbine
          </span>
          <span className="flex items-center gap-1.5 text-slate-600">
            <span className="w-3 h-3 rounded bg-emerald-500 inline-block"></span>
            Biomass Gasifier
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
              unit=" kWh"
            />
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const p = payload[0].payload;
                  return (
                    <div className="bg-slate-900 text-white p-3 rounded-lg shadow-xl text-xs space-y-1.5 border border-slate-800">
                      <div className="font-bold text-slate-200 border-b border-slate-800 pb-1 flex justify-between gap-4">
                        <span>Hour {p.hour}</span>
                        <span className="font-mono text-emerald-400">
                          Total Avail: {p.totalRenewableKwh.toFixed(1)} kWh
                        </span>
                      </div>
                      <div className="flex justify-between gap-4 text-slate-300">
                        <span className="text-amber-400">Solar (100 kWp):</span>
                        <span className="font-mono">{p.solarKwh.toFixed(1)} kWh</span>
                      </div>
                      <div className="flex justify-between gap-4 text-slate-300">
                        <span className="text-cyan-400">Wind (60 kW):</span>
                        <span className="font-mono">{p.windKwh.toFixed(1)} kWh</span>
                      </div>
                      <div className="flex justify-between gap-4 text-slate-300">
                        <span className="text-emerald-400">Biomass (50 kW cap):</span>
                        <span className="font-mono">{p.biomassKwh.toFixed(1)} kWh</span>
                      </div>
                      <div className="text-[10px] text-slate-400 italic pt-1 border-t border-slate-800/80">
                        *Potential capacity available. Does not represent final consumed energy.
                      </div>
                    </div>
                  );
                }
                return null;
              }}
            />
            <Line
              type="monotone"
              dataKey="solarKwh"
              stroke="#f59e0b"
              strokeWidth={2}
              dot={{ r: 2.5, fill: '#f59e0b' }}
            />
            <Line
              type="monotone"
              dataKey="windKwh"
              stroke="#06b6d4"
              strokeWidth={2}
              dot={{ r: 2.5, fill: '#06b6d4' }}
            />
            <Line
              type="stepAfter"
              dataKey="biomassKwh"
              stroke="#10b981"
              strokeWidth={2}
              dot={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
