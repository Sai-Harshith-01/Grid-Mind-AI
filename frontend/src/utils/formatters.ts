/**
 * Formatting utilities for industrial metrics, currency, and timestamps.
 */

export function formatINR(val: number | null | undefined): string {
  if (val === null || val === undefined || isNaN(val)) {
    return '—';
  }
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 2,
    minimumFractionDigits: 2,
  }).format(val);
}

export function formatLakhs(val: number | null | undefined): string {
  if (val === null || val === undefined || isNaN(val)) {
    return '—';
  }
  const lakhs = val / 100000;
  if (Math.abs(lakhs) >= 1) {
    return `₹${lakhs.toLocaleString('en-IN', { maximumFractionDigits: 2, minimumFractionDigits: 2 })} Lakhs`;
  }
  return formatINR(val);
}


export function formatKW(val: number | null | undefined): string {
  if (val === null || val === undefined || isNaN(val)) {
    return '—';
  }
  return `${val.toLocaleString('en-IN', { maximumFractionDigits: 1, minimumFractionDigits: 1 })} kW`;
}

export function formatKWH(val: number | null | undefined): string {
  if (val === null || val === undefined || isNaN(val)) {
    return '—';
  }
  return `${val.toLocaleString('en-IN', { maximumFractionDigits: 1, minimumFractionDigits: 1 })} kWh`;
}

export function formatPercent(val: number | null | undefined, decimals = 1): string {
  if (val === null || val === undefined || isNaN(val)) {
    return '—';
  }
  return `${val.toFixed(decimals)}%`;
}

export function formatHour(hour: number): string {
  return `${String(hour).padStart(2, '0')}:00`;
}

export function formatTime(isoStr: string | null | undefined): string {
  if (!isoStr) return '—';
  try {
    const d = new Date(isoStr);
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false });
  } catch {
    return isoStr;
  }
}

export function formatCategoryName(category: string): string {
  switch (category) {
    case 'idle_machine_waste':
      return 'Idle Machine Waste';
    case 'unexpected_consumption_spike':
      return 'Consumption Spike';
    case 'high_demand_period':
      return 'Peak Capacity Risk';
    default:
      return category
        .split('_')
        .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
        .join(' ');
  }
}

export function getSeverityBadgeClass(severity: string): string {
  switch (severity?.toLowerCase()) {
    case 'critical':
      return 'bg-rose-500/10 text-rose-400 border border-rose-500/30';
    case 'high':
      return 'bg-amber-500/10 text-amber-400 border border-amber-500/30';
    case 'medium':
      return 'bg-blue-500/10 text-blue-400 border border-blue-500/30';
    case 'low':
    default:
      return 'bg-slate-500/10 text-slate-400 border border-slate-500/30';
  }
}
