import React from 'react';
import {
  ResponsiveContainer,
  ComposedChart,
  Bar,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from 'recharts';
import { HourlyAnalyticalProfileItem } from '../../types/api';
import { formatHour } from '../../utils/formatters';

interface DemandTariffChartProps {
  data: HourlyAnalyticalProfileItem[];
}

export const DemandTariffChart: React.FC<DemandTariffChartProps> = ({ data }) => {
  const chartData = data.map((item) => ({
    hour: formatHour(item.interval_index),
    interval: item.interval_index,
    demandKw: item.factory_demand_kw,
    tariff: item.grid_tariff_inr_per_kwh,
    isPeak: item.is_peak_tariff,
  }));

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4">
        <div>
          <h3 className="text-base font-bold text-slate-900 tracking-tight">
            Hourly Factory Demand & Grid ToD Tariffs
          </h3>
          <p className="text-xs text-slate-500">
            Factory active power (kW) compared with Time-of-Day utility tariff rates (₹/kWh)
          </p>
        </div>
        <div className="flex items-center gap-3 text-xs">
          <span className="flex items-center gap-1.5 text-slate-600">
            <span className="w-3 h-3 rounded bg-teal-500 inline-block"></span>
            Demand (kW)
          </span>
          <span className="flex items-center gap-1.5 text-slate-600">
            <span className="w-3 h-3 rounded bg-amber-500 inline-block"></span>
            Tariff (₹/kWh)
          </span>
        </div>
      </div>

      <div className="h-72 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={chartData} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
            <XAxis dataKey="hour" tick={{ fontSize: 11, fill: '#64748b' }} tickLine={false} />
            <YAxis
              yAxisId="left"
              tick={{ fontSize: 11, fill: '#64748b' }}
              tickLine={false}
              axisLine={false}
              unit=" kW"
            />
            <YAxis
              yAxisId="right"
              orientation="right"
              tick={{ fontSize: 11, fill: '#64748b' }}
              tickLine={false}
              axisLine={false}
              domain={[0, 15]}
              unit=" ₹"
            />
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const p = payload[0].payload;
                  return (
                    <div className="bg-slate-900 text-white p-3 rounded-lg shadow-xl text-xs space-y-1.5 border border-slate-800">
                      <div className="font-bold text-slate-200 border-b border-slate-800 pb-1 flex items-center justify-between gap-4">
                        <span>Hour {p.hour}</span>
                        {p.isPeak && (
                          <span className="bg-rose-500/20 text-rose-300 px-1.5 py-0.5 rounded text-[10px]">
                            Peak Tariff
                          </span>
                        )}
                      </div>
                      <div className="flex justify-between gap-4 text-slate-300">
                        <span>Demand:</span>
                        <span className="font-mono font-bold text-teal-400">
                          {p.demandKw.toFixed(1)} kW
                        </span>
                      </div>
                      <div className="flex justify-between gap-4 text-slate-300">
                        <span>Utility Tariff:</span>
                        <span className="font-mono font-bold text-amber-400">
                          ₹{p.tariff.toFixed(2)} / kWh
                        </span>
                      </div>
                    </div>
                  );
                }
                return null;
              }}
            />
            <Bar yAxisId="left" dataKey="demandKw" fill="#0d9488" radius={[4, 4, 0, 0]} barSize={14} />
            <Line
              yAxisId="right"
              type="monotone"
              dataKey="tariff"
              stroke="#f59e0b"
              strokeWidth={2.5}
              dot={{ r: 3, fill: '#f59e0b' }}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
