import React, { useEffect, useState, useCallback } from 'react';
import {
  Sidebar,
  ActiveTab,
} from './components/layout/Sidebar';
import { Header } from './components/layout/Header';
import { DashboardPage } from './pages/DashboardPage';
import { InvestigatorPage } from './pages/InvestigatorPage';
import { OptimizationPage } from './pages/OptimizationPage';
import {
  fetchHealth,
  fetchFactories,
  fetchFactoryProfile,
  fetchFactoryTimeseries,
  fetchEnergyMetrics,
  fetchAnalyticalProfile,
  fetchAnomalies,
  fetchOptimizationSummary,
  runOptimization,
  fetchInvestigationStatus,
} from './api';
import {
  FactoryListItem,
  FactoryProfileResponse,
  FactoryTimeSeriesResponse,
  EnergyMetricsSummaryResponse,
  AnalyticalEnergyProfileResponse,
  OptimizationSummaryResponse,
  OptimizationRunResponse,
  DetectedAnomalyFinding,
  InvestigationStatusResponse,
} from './types/api';
import { AlertCircle, RefreshCw } from 'lucide-react';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<ActiveTab>('dashboard');
  const [selectedAnomalyId, setSelectedAnomalyId] = useState<string | null>(null);
  const [selectedFactoryId, setSelectedFactoryId] = useState<string>('DEMO-FAC-001');

  // Factories list
  const [factories, setFactories] = useState<FactoryListItem[]>([]);

  // Connection & Telemetry State
  const [isBackendHealthy, setIsBackendHealthy] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [globalError, setGlobalError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<string>('');

  // Operational Data State
  const [profile, setProfile] = useState<FactoryProfileResponse | null>(null);
  const [timeseries, setTimeseries] = useState<FactoryTimeSeriesResponse | null>(null);
  const [metrics, setMetrics] = useState<EnergyMetricsSummaryResponse | null>(null);
  const [analyticalProfile, setAnalyticalProfile] = useState<AnalyticalEnergyProfileResponse | null>(null);
  const [optSummary, setOptSummary] = useState<OptimizationSummaryResponse | null>(null);
  const [optRun, setOptRun] = useState<OptimizationRunResponse | null>(null);
  const [anomalies, setAnomalies] = useState<DetectedAnomalyFinding[]>([]);
  const [investigationStatus, setInvestigationStatus] = useState<InvestigationStatusResponse | null>(null);

  // Load factories list once on startup
  useEffect(() => {
    fetchFactories()
      .then((res) => {
        if (res.factories && res.factories.length > 0) {
          setFactories(res.factories);
        }
      })
      .catch((err) => {
        console.warn('Failed to load factories list:', err);
      });
  }, []);

  const loadAllData = useCallback(async (targetFactoryId?: string) => {
    const factoryId = targetFactoryId || selectedFactoryId;
    setIsLoading(true);
    setGlobalError(null);

    try {
      // 1. Health check
      try {
        const health = await fetchHealth();
        setIsBackendHealthy(health.status === 'ok');
      } catch {
        setIsBackendHealthy(false);
      }

      // 2. Load core telemetry and operational endpoints in parallel for target factory
      const [
        profileRes,
        timeseriesRes,
        metricsRes,
        analyticalRes,
        anomaliesRes,
        optSummaryRes,
        optRunRes,
        invStatusRes,
      ] = await Promise.all([
        fetchFactoryProfile(factoryId),
        fetchFactoryTimeseries(factoryId),
        fetchEnergyMetrics(factoryId),
        fetchAnalyticalProfile(factoryId),
        fetchAnomalies({ factory_id: factoryId }),
        fetchOptimizationSummary(factoryId),
        runOptimization(factoryId),
        fetchInvestigationStatus().catch(() => null),
      ]);

      setProfile(profileRes);
      setTimeseries(timeseriesRes);
      setMetrics(metricsRes);
      setAnalyticalProfile(analyticalRes);
      setAnomalies(anomaliesRes.findings);
      setOptSummary(optSummaryRes);
      setOptRun(optRunRes);
      setInvestigationStatus(invStatusRes);
      setLastUpdated(new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }));
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to fetch operational data';
      setGlobalError(msg);
      setIsBackendHealthy(false);
    } finally {
      setIsLoading(false);
    }
  }, [selectedFactoryId]);

  // Factory Switch Handler: clear stale selection and factory state immediately, then re-fetch
  const handleSelectFactory = async (newFactoryId: string) => {
    if (newFactoryId === selectedFactoryId) return;
    setSelectedFactoryId(newFactoryId);
    setSelectedAnomalyId(null);
    // Immediately clear previous factory state to prevent any stale data leakage
    setProfile(null);
    setTimeseries(null);
    setMetrics(null);
    setAnalyticalProfile(null);
    setAnomalies([]);
    setOptSummary(null);
    setOptRun(null);
    await loadAllData(newFactoryId);
  };

  const refreshOptimizationData = async () => {
    try {
      const [newSummary, newRun] = await Promise.all([
        fetchOptimizationSummary(selectedFactoryId),
        runOptimization(selectedFactoryId),
      ]);
      setOptSummary(newSummary);
      setOptRun(newRun);
    } catch (err) {
      console.error('Failed to re-run optimization:', err);
      throw err;
    }
  };

  useEffect(() => {
    loadAllData(selectedFactoryId);
  }, [selectedFactoryId, loadAllData]);

  // Handler to jump to AI Investigator from Anomaly alert click
  const handleInvestigateAnomaly = (anomalyId: string) => {
    setSelectedAnomalyId(anomalyId);
    setActiveTab('investigator');
  };

  const getPageHeader = () => {
    const factoryName = profile?.name ? ` • ${profile.name}` : '';
    switch (activeTab) {
      case 'dashboard':
        return {
          title: `Factory Energy Operations Dashboard${factoryName}`,
          subtitle: 'Real-time telemetry, load intensity, and algorithmic anomaly alerts across production zones',
        };
      case 'investigator':
        return {
          title: `AI Energy Waste Investigator${factoryName}`,
          subtitle: 'Grounded Google Gemini root-cause diagnosis, physical hypotheses, and prioritised operator action plans',
        };
      case 'optimization':
        return {
          title: `Renewable Dispatch Optimiser (HiGHS LP)${factoryName}`,
          subtitle: 'Cost-optimal multi-source generation allocation, ToD tariff arbitrage, and contract demand headroom',
        };
    }
  };

  const headerInfo = getPageHeader();

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col md:flex-row font-sans text-slate-800">
      {/* Industrial Sidebar Navigation */}
      <Sidebar
        activeTab={activeTab}
        onSelectTab={setActiveTab}
        factoryProfile={profile}
        isBackendHealthy={isBackendHealthy}
        onRefreshHealth={() => loadAllData(selectedFactoryId)}
        selectedFactoryId={selectedFactoryId}
        onSelectFactory={handleSelectFactory}
        factories={factories}
      />

      {/* Main Content Workspace */}
      <div className="flex-1 flex flex-col min-w-0 h-screen overflow-y-auto">
        <Header
          title={headerInfo.title}
          subtitle={headerInfo.subtitle}
          onRefresh={() => loadAllData(selectedFactoryId)}
          isLoading={isLoading}
          lastUpdated={lastUpdated}
          selectedFactoryId={selectedFactoryId}
          onSelectFactory={handleSelectFactory}
          factories={factories}
        />

        {/* Global Connection / Fetch Error */}
        {globalError && (
          <div className="m-8 p-4 bg-rose-50 border border-rose-200 text-rose-800 rounded-xl text-xs flex items-center justify-between">
            <div className="flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
              <span>
                <strong>Backend Communication Error:</strong> {globalError}. Ensure the FastAPI server is running at http://localhost:8000.
              </span>
            </div>
            <button
              onClick={() => loadAllData(selectedFactoryId)}
              className="flex items-center gap-1.5 px-3 py-1 rounded bg-rose-100 text-rose-800 font-semibold hover:bg-rose-200 transition-colors"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Retry</span>
            </button>
          </div>
        )}

        {/* Dynamic Screen View */}
        <main className="flex-1 pb-16">
          {activeTab === 'dashboard' && (
            <DashboardPage
              profile={profile}
              timeseries={timeseries}
              metrics={metrics}
              analyticalProfile={analyticalProfile}
              optSummary={optSummary}
              optRun={optRun}
              anomalies={anomalies}
              onInvestigateAnomaly={handleInvestigateAnomaly}
              onNavigateToSimulator={() => setActiveTab('optimization')}
            />
          )}

          {activeTab === 'investigator' && (
            <InvestigatorPage
              anomalies={anomalies}
              selectedAnomalyId={selectedAnomalyId}
              onSelectAnomaly={setSelectedAnomalyId}
              investigationStatus={investigationStatus}
              selectedFactoryId={selectedFactoryId}
              onNavigateToOptimizer={() => setActiveTab('optimization')}
            />
          )}

          {activeTab === 'optimization' && (
            <OptimizationPage
              profile={profile}
              optSummary={optSummary}
              optRun={optRun}
              onRefreshOptimization={refreshOptimizationData}
              selectedFactoryId={selectedFactoryId}
            />
          )}
        </main>

        {/* Mandatory Fictional Demonstration Disclosure Footer */}
        <footer className="py-2.5 px-6 border-t border-slate-200 bg-slate-50 text-center text-xs text-slate-500 shrink-0">
          <span>Fictional demonstration factories using synthetic data. Not actual customer facilities.</span>
        </footer>
      </div>
    </div>
  );
};

export default App;
