import React from 'react';
import { Sun, Wind, Flame, Zap, Sparkles } from 'lucide-react';

export const HeroSection: React.FC = () => {
  const energySources = [
    {
      name: 'Solar PV',
      icon: Sun,
      color: 'text-amber-400',
      bgColor: 'bg-amber-500/10 border-amber-500/20',
      description: 'On-site rooftop generation & real-time irradiance forecasting',
    },
    {
      name: 'Wind Turbines',
      icon: Wind,
      color: 'text-sky-400',
      bgColor: 'bg-sky-500/10 border-sky-500/20',
      description: 'Captive wind yield curves & aerodynamic output scheduling',
    },
    {
      name: 'Biomass Cogeneration',
      icon: Flame,
      color: 'text-emerald-400',
      bgColor: 'bg-emerald-500/10 border-emerald-500/20',
      description: 'Agricultural residue & thermal-to-electric boiler balancing',
    },
    {
      name: 'Grid Electricity',
      icon: Zap,
      color: 'text-violet-400',
      bgColor: 'bg-violet-500/10 border-violet-500/20',
      description: 'Time-of-Day (ToD) tariffs & peak-shaving dispatch optimisation',
    },
  ];

  return (
    <div className="text-center max-w-4xl mx-auto mb-10">
      {/* Badge */}
      <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-semibold uppercase tracking-wider mb-6">
        <Sparkles className="w-3.5 h-3.5" />
        <span>Phase 1 — Project Foundation</span>
      </div>

      {/* Main Title */}
      <h1 className="text-5xl sm:text-6xl font-extrabold tracking-tight text-white mb-4">
        GridMind <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 via-teal-300 to-cyan-400">AI</span>
      </h1>

      {/* Subtitle */}
      <h2 className="text-xl sm:text-2xl font-medium text-slate-300 mb-6">
        Intelligent Energy Optimisation for MSME Factories
      </h2>

      {/* Description mentioning solar, wind, biomass, and grid electricity */}
      <p className="text-slate-400 text-base sm:text-lg max-w-2xl mx-auto leading-relaxed mb-10">
        Empowering Micro, Small, and Medium Enterprises to slash operating costs and carbon intensity 
        by orchestrating <span className="text-amber-300 font-medium">solar</span>,{' '}
        <span className="text-sky-300 font-medium">wind</span>, and{' '}
        <span className="text-emerald-300 font-medium">biomass</span> generation alongside dynamic{' '}
        <span className="text-violet-300 font-medium">grid electricity</span> tariffs through advanced mathematical models and generative intelligence.
      </p>

      {/* Energy Pillars Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-left">
        {energySources.map((source) => {
          const Icon = source.icon;
          return (
            <div
              key={source.name}
              className={`p-4 rounded-xl border ${source.bgColor} backdrop-blur-sm transition-transform hover:-translate-y-0.5 duration-200`}
            >
              <div className="flex items-center gap-2.5 mb-2">
                <div className={`p-2 rounded-lg bg-slate-900/80 ${source.color}`}>
                  <Icon className="w-4 h-4" />
                </div>
                <h3 className="font-semibold text-slate-200 text-sm">{source.name}</h3>
              </div>
              <p className="text-xs text-slate-400 leading-normal">{source.description}</p>
            </div>
          );
        })}
      </div>
    </div>
  );
};
