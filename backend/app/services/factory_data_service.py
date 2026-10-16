"""Factory data service providing cached, deterministic factory datasets.

Multi-factory version: maintains one FactorySimulator and cache per factory ID.
All API endpoints may specify a factory_id; the default is DEMO-FAC-001 (PrecisionWorks).

Ensures all API endpoints for the same factory share the identical generated dataset,
preventing cross-endpoint divergence within a request lifecycle.
"""

from typing import Dict, List, Optional
from app.data.factory_config import FactoryProfile
from app.data.factory_registry import (
    FACTORY_SEEDS,
    FACTORY_SIMULATION_DATES,
    VALID_FACTORY_IDS,
    get_factory_profile,
    resolve_factory_id,
)
from app.data.factory_simulator import FactorySimulator
from app.schemas.factory import (
    AnomalyScenario,
    AnomalyScenariosResponse,
    FactoryOverviewResponse,
    FactoryProfileResponse,
    FactoryTimeSeriesResponse,
    SimulationMetadata,
    TimeSeriesInterval,
)


DEFAULT_FACTORY_ID = "DEMO-FAC-001"


class FactoryDataService:
    """Service caching and exposing deterministic factory datasets for multiple factories."""

    def __init__(self):
        # Per-factory caches: factory_id -> cached data
        self._profiles: Dict[str, FactoryProfile] = {}
        self._simulators: Dict[str, FactorySimulator] = {}
        self._cached_intervals: Dict[str, Optional[List[TimeSeriesInterval]]] = {}
        self._cached_anomalies: Dict[str, Optional[List[AnomalyScenario]]] = {}
        self._cached_overviews: Dict[str, Optional[FactoryOverviewResponse]] = {}

    def validate_factory_id(self, factory_id: str) -> str:
        """Validate factory ID, mapping legacy IDs if provided, or raise ValueError."""
        fid = resolve_factory_id(factory_id)
        if fid not in VALID_FACTORY_IDS:
            raise ValueError(
                f"Unknown factory_id '{factory_id}'. "
                f"Valid IDs: {VALID_FACTORY_IDS}"
            )
        return fid

    def _ensure_factory_initialized(self, factory_id: str) -> None:
        """Initialize simulator and empty caches for a factory if not yet done."""
        fid = self.validate_factory_id(factory_id)
        if fid not in self._simulators:
            profile = get_factory_profile(fid)
            seed = FACTORY_SEEDS.get(fid, 42)
            sim_date = FACTORY_SIMULATION_DATES.get(fid, "2026-10-14")
            self._profiles[fid] = profile
            self._simulators[fid] = FactorySimulator(
                profile=profile, seed=seed, simulation_date=sim_date
            )
            self._cached_intervals[fid] = None
            self._cached_anomalies[fid] = None
            self._cached_overviews[fid] = None

    def _ensure_data_generated(self, factory_id: str) -> None:
        """Generate and cache simulation data on demand for the specified factory."""
        fid = self.validate_factory_id(factory_id)
        self._ensure_factory_initialized(fid)
        if self._cached_intervals[fid] is None:
            sim = self._simulators[fid]
            self._cached_intervals[fid] = sim.generate_timeseries()
            self._cached_anomalies[fid] = sim.get_anomaly_scenarios()
            self._cached_overviews[fid] = sim.generate_overview(
                self._cached_intervals[fid]
            )

    def get_profile(self, factory_id: str = DEFAULT_FACTORY_ID) -> FactoryProfileResponse:
        """Return the factory profile and configuration for the given factory."""
        fid = self.validate_factory_id(factory_id)
        self._ensure_data_generated(fid)
        profile = self._profiles[fid]
        seed = FACTORY_SEEDS[fid]
        sim_date = FACTORY_SIMULATION_DATES[fid]
        return FactoryProfileResponse(
            factory_id=profile.factory_id,
            name=profile.name,
            sector=profile.sector,
            location=profile.location,
            currency=profile.currency,
            power_unit=profile.power_unit,
            energy_unit=profile.energy_unit,
            production_unit=profile.production_unit,
            total_rated_connected_power_kw=profile.total_rated_connected_power_kw,
            facility_baseload_kw=profile.facility_baseload_kw,
            zones=profile.zones,
            shifts=profile.shifts,
            solar=profile.solar,
            wind=profile.wind,
            biomass=profile.biomass,
            grid=profile.grid,
            battery=profile.battery,
            simulation_metadata=SimulationMetadata(
                simulation_seed=seed,
                simulation_date=sim_date,
            ),
        )

    def get_timeseries(self, factory_id: str = DEFAULT_FACTORY_ID) -> FactoryTimeSeriesResponse:
        """Return the 24-hour time series dataset for the given factory."""
        fid = self.validate_factory_id(factory_id)
        self._ensure_data_generated(fid)
        profile = self._profiles[fid]
        intervals = self._cached_intervals[fid]
        seed = FACTORY_SEEDS[fid]
        sim_date = FACTORY_SIMULATION_DATES[fid]
        assert intervals is not None
        return FactoryTimeSeriesResponse(
            factory_id=profile.factory_id,
            factory_name=profile.name,
            simulation_date=sim_date,
            total_intervals=len(intervals),
            intervals=intervals,
            simulation_metadata=SimulationMetadata(
                simulation_seed=seed,
                simulation_date=sim_date,
            ),
        )

    def get_anomaly_scenarios(self, factory_id: str = DEFAULT_FACTORY_ID) -> AnomalyScenariosResponse:
        """Return the injected anomaly scenarios for the given factory."""
        fid = self.validate_factory_id(factory_id)
        self._ensure_data_generated(fid)
        anomalies = self._cached_anomalies[fid]
        seed = FACTORY_SEEDS[fid]
        sim_date = FACTORY_SIMULATION_DATES[fid]
        assert anomalies is not None
        return AnomalyScenariosResponse(
            total_anomalies=len(anomalies),
            scenarios=anomalies,
            simulation_metadata=SimulationMetadata(
                simulation_seed=seed,
                simulation_date=sim_date,
            ),
        )

    def get_overview(self, factory_id: str = DEFAULT_FACTORY_ID) -> FactoryOverviewResponse:
        """Return the descriptive summary overview of the dataset for the given factory."""
        fid = self.validate_factory_id(factory_id)
        self._ensure_data_generated(fid)
        overview = self._cached_overviews[fid]
        assert overview is not None
        return overview

    def get_raw_profile(self, factory_id: str = DEFAULT_FACTORY_ID) -> FactoryProfile:
        """Return the internal FactoryProfile Pydantic model (used by optimizer, etc.)."""
        fid = self.validate_factory_id(factory_id)
        self._ensure_factory_initialized(fid)
        return self._profiles[fid]

    @property
    def _profile(self) -> FactoryProfile:
        """Backward-compatible property: returns the default (DEMO-FAC-001) factory profile."""
        return self.get_raw_profile(DEFAULT_FACTORY_ID)

    def reload(self, factory_id: str = DEFAULT_FACTORY_ID) -> None:
        """Clear cached data for a specific factory, forcing re-generation on next access."""
        fid = self.validate_factory_id(factory_id)
        if fid in self._simulators:
            del self._simulators[fid]
            del self._profiles[fid]
            del self._cached_intervals[fid]
            del self._cached_anomalies[fid]
            del self._cached_overviews[fid]



# Global singleton instance — multi-factory aware
factory_data_service = FactoryDataService()
