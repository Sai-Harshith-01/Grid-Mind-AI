"""Factory registry for GridMind AI multi-factory prototype.

IMPORTANT NOTICE:
All three factory profiles are fictional demonstration factories using synthetic data.
Not actual customer facilities.
None of the factory names, electricity data, or savings figures represent
real customers, measured installations, or guaranteed outcomes.

Factories:
  DEMO-FAC-001 — PrecisionWorks Factory (precision engineering / CNC machining)
  DEMO-FAC-002 — FreshField Factory (food processing / cold storage)
  DEMO-FAC-003 — WeaveWise Factory (textile spinning / weaving)
"""

from typing import Dict
from app.data.factory_config import (
    FactoryProfile,
    ProductionZoneConfig,
    MachineConfig,
    ShiftSchedule,
    SolarConfig,
    WindConfig,
    BiomassConfig,
    GridConfig,
    GridTariffPeriod,
    BatteryConfig,
    get_default_factory_profile,
)

# ---------------------------------------------------------------------------
# Factory A — PrecisionWorks Factory (fictional MSME)
# ---------------------------------------------------------------------------

def get_precisionworks_profile() -> FactoryProfile:
    """Return the PrecisionWorks Factory profile."""
    return get_default_factory_profile()


# Backward-compatible alias
def get_apex_profile() -> FactoryProfile:
    return get_precisionworks_profile()


# ---------------------------------------------------------------------------
# Factory B — FreshField Factory (fictional MSME)
# ---------------------------------------------------------------------------

def get_freshfield_profile() -> FactoryProfile:
    """
    FreshField Factory — food processing and cold storage MSME.

    Simulated characteristics:
    - High continuous baseline from refrigeration compressors.
    - Processing equipment peaking during daytime shifts.
    - Higher demand during expensive peak tariff hours (refrigeration cannot be curtailed).
    - Medium solar capacity (roof-mounted over processing hall).
    - Moderate wind availability.
    - Biomass from agricultural by-products (grape pomace, soy husks).
    - Utility supply at commercial/industrial ToD tariffs.
    """
    return FactoryProfile(
        factory_id="DEMO-FAC-002",
        name="FreshField Factory",
        sector="Food Processing & Cold Storage",
        location="Fictional Demonstration Facility (Synthetic Profile)",
        currency="INR",
        power_unit="kW",
        energy_unit="kWh",
        production_unit="processed_kg",
        total_rated_connected_power_kw=210.0,
        facility_baseload_kw=30.0,  # Refrigeration always on
        zones=[
            ProductionZoneConfig(
                zone_id="zone_cold_storage",
                name="Zone 1: Cold Storage & Refrigeration",
                description="Multi-chamber cold store with compressor banks at -2°C to +8°C.",
                rated_power_kw=80.0,
                max_production_capacity_units_per_hour=0.0,  # Continuous, not batch
                machines=[
                    MachineConfig(
                        machine_id="COMP_BANK_01",
                        name="Refrigeration Compressor Bank A",
                        rated_power_kw=40.0,
                        active_power_range_kw=(28.0, 38.0),
                        idle_power_kw=22.0,
                        description="Screw compressor maintaining cold-store chambers.",
                    ),
                    MachineConfig(
                        machine_id="COMP_BANK_02",
                        name="Refrigeration Compressor Bank B",
                        rated_power_kw=40.0,
                        active_power_range_kw=(20.0, 35.0),
                        idle_power_kw=18.0,
                        description="Secondary compressor for overflow and frozen section.",
                    ),
                ],
            ),
            ProductionZoneConfig(
                zone_id="zone_processing",
                name="Zone 2: Food Processing & Washing",
                description="Fruit and vegetable sorting conveyors, washing drums, centrifugal dryers.",
                rated_power_kw=90.0,
                max_production_capacity_units_per_hour=2500.0,
                machines=[
                    MachineConfig(
                        machine_id="SORT_CONV_01",
                        name="Multi-Lane Sorting Conveyor",
                        rated_power_kw=22.0,
                        active_power_range_kw=(8.0, 16.0),
                        idle_power_kw=1.5,
                        description="Optical grading and weight-sorting conveyor for mixed produce.",
                    ),
                    MachineConfig(
                        machine_id="WASH_DRUM_01",
                        name="Industrial Washing Drum",
                        rated_power_kw=30.0,
                        active_power_range_kw=(12.0, 22.0),
                        idle_power_kw=2.0,
                        description="High-throughput rotating wash drum with recirculated chilled water.",
                    ),
                    MachineConfig(
                        machine_id="CENTRIFUGE_01",
                        name="Centrifugal Drying System",
                        rated_power_kw=38.0,
                        active_power_range_kw=(16.0, 28.0),
                        idle_power_kw=2.5,
                        description="Spin-dry stage before pre-cooling tunnel.",
                    ),
                ],
            ),
            ProductionZoneConfig(
                zone_id="zone_packaging",
                name="Zone 3: Packaging & Dispatch",
                description="Modified-atmosphere packaging, label printers, and refrigerated dispatch dock.",
                rated_power_kw=40.0,
                max_production_capacity_units_per_hour=1800.0,
                machines=[
                    MachineConfig(
                        machine_id="MAP_SEAL_01",
                        name="MAP Tray Sealer",
                        rated_power_kw=18.0,
                        active_power_range_kw=(6.0, 12.0),
                        idle_power_kw=1.0,
                        description="Nitrogen-flush modified-atmosphere tray sealer.",
                    ),
                    MachineConfig(
                        machine_id="DOCK_HVAC_01",
                        name="Dispatch Dock Refrigerated Area",
                        rated_power_kw=22.0,
                        active_power_range_kw=(8.0, 16.0),
                        idle_power_kw=10.0,
                        description="Climate-controlled dispatch bay to maintain cold chain.",
                    ),
                ],
            ),
        ],
        shifts=[
            ShiftSchedule(
                shift_name="Shift 1: Processing Day",
                start_hour=6,
                end_hour=18,
                active_zones=["zone_cold_storage", "zone_processing", "zone_packaging"],
                production_target_multiplier=1.0,
                description="Full processing shift; all zones active with peak solar availability.",
            ),
            ShiftSchedule(
                shift_name="Shift 2: Evening Packaging",
                start_hour=18,
                end_hour=22,
                active_zones=["zone_cold_storage", "zone_packaging"],
                production_target_multiplier=0.4,
                description="Reduced packaging shift during peak tariff window; refrigeration continuous.",
            ),
            ShiftSchedule(
                shift_name="Shift 3: Night Cold Hold",
                start_hour=22,
                end_hour=6,
                active_zones=["zone_cold_storage"],
                production_target_multiplier=0.0,
                description="Processing stopped; refrigeration maintains cold-store temperature overnight.",
            ),
        ],
        solar=SolarConfig(
            installed_capacity_kw=75.0,
            panel_type="Polycrystalline Rooftop (Processing Hall)",
            tilt_angle_deg=20.0,
            peak_efficiency=0.82,
        ),
        wind=WindConfig(
            installed_capacity_kw=20.0,  # Inland, lower resource
            turbine_type="Small Horizontal-Axis Turbine",
            hub_height_m=24.0,
            cut_in_speed_mps=3.5,
            rated_speed_mps=10.0,
        ),
        biomass=BiomassConfig(
            installed_capacity_kw=35.0,
            fuel_type="Grape Pomace & Soy Husk Briquettes",
            daily_fuel_available_kg=180.0,
            specific_fuel_consumption_kg_per_kwh=0.85,
            fuel_cost_inr_per_kwh=3.80,
            is_dispatchable=True,
        ),
        grid=GridConfig(
            contract_demand_kw=200.0,
            voltage_level_kv=11.0,
            supply_company="Regional Utility Distribution Company",
            tariffs=[
                GridTariffPeriod(
                    period_name="Off-Peak / Night",
                    hours=[23, 0, 1, 2, 3, 4, 5],
                    rate_inr_per_kwh=6.20,
                    description="Night hours — off-peak rate for continuous cold storage.",
                ),
                GridTariffPeriod(
                    period_name="Normal / Day",
                    hours=[6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17],
                    rate_inr_per_kwh=8.50,
                    description="Day processing hours — standard commercial rate.",
                ),
                GridTariffPeriod(
                    period_name="Peak / Evening",
                    hours=[18, 19, 20, 21, 22],
                    rate_inr_per_kwh=12.20,
                    description="Peak surcharge window — refrigeration cannot be curtailed.",
                ),
            ],
        ),
        battery=BatteryConfig(
            capacity_kwh=80.0,
            max_charge_power_kw=40.0,
            max_discharge_power_kw=40.0,
            roundtrip_efficiency=0.88,
            min_soc_percent=25.0,
            max_soc_percent=95.0,
            initial_soc_percent=60.0,
        ),
    )


# Backward-compatible alias
def get_freshharvest_profile() -> FactoryProfile:
    return get_freshfield_profile()


# ---------------------------------------------------------------------------
# Factory C — WeaveWise Factory (fictional MSME)
# ---------------------------------------------------------------------------

def get_weavewise_profile() -> FactoryProfile:
    """
    WeaveWise Factory — spinning and weaving MSME.

    Simulated characteristics:
    - High spinning motor demand during both shifts.
    - Weaving looms run continuously during production shifts.
    - Finishing (bleaching, dyeing) is heat-intensive with scheduled batch cycles.
    - Strong rooftop solar.
    - Moderate wind availability.
    - Biomass from cotton stalks and textile waste.
    - Utility supply with multi-tier ToD tariffs.
    """
    return FactoryProfile(
        factory_id="DEMO-FAC-003",
        name="WeaveWise Factory",
        sector="Textile Manufacturing — Spinning & Weaving",
        location="Fictional Demonstration Facility (Synthetic Profile)",
        currency="INR",
        power_unit="kW",
        energy_unit="kWh",
        production_unit="fabric_metres",
        total_rated_connected_power_kw=280.0,
        facility_baseload_kw=12.0,
        zones=[
            ProductionZoneConfig(
                zone_id="zone_spinning",
                name="Zone 1: Ring Spinning Section",
                description="Ring-frame spinning machines producing cotton yarn from roving.",
                rated_power_kw=140.0,
                max_production_capacity_units_per_hour=0.0,  # Measured in kg yarn, not fabric metres
                machines=[
                    MachineConfig(
                        machine_id="RING_FRAME_A",
                        name="Ring Frame Machine Bank A (480 spindles)",
                        rated_power_kw=55.0,
                        active_power_range_kw=(30.0, 48.0),
                        idle_power_kw=5.0,
                        description="High-speed ring-frame for 30s–40s cotton counts.",
                    ),
                    MachineConfig(
                        machine_id="RING_FRAME_B",
                        name="Ring Frame Machine Bank B (480 spindles)",
                        rated_power_kw=55.0,
                        active_power_range_kw=(30.0, 48.0),
                        idle_power_kw=5.0,
                        description="High-speed ring-frame for finer 60s count export yarn.",
                    ),
                    MachineConfig(
                        machine_id="HUMIDIFY_01",
                        name="Humidification Plant",
                        rated_power_kw=30.0,
                        active_power_range_kw=(14.0, 22.0),
                        idle_power_kw=4.0,
                        description="Evaporative cooling and humidification to maintain 65% RH.",
                    ),
                ],
            ),
            ProductionZoneConfig(
                zone_id="zone_weaving",
                name="Zone 2: Weaving Hall",
                description="Rapier and air-jet looms producing grey fabric from yarn.",
                rated_power_kw=100.0,
                max_production_capacity_units_per_hour=420.0,
                machines=[
                    MachineConfig(
                        machine_id="RAPIER_01",
                        name="Rapier Loom Bank (12 looms)",
                        rated_power_kw=48.0,
                        active_power_range_kw=(22.0, 40.0),
                        idle_power_kw=4.0,
                        description="Dornier rapier looms — 190cm reed width for shirting fabric.",
                    ),
                    MachineConfig(
                        machine_id="AIR_JET_01",
                        name="Air-Jet Loom Bank (8 looms)",
                        rated_power_kw=52.0,
                        active_power_range_kw=(24.0, 42.0),
                        idle_power_kw=4.5,
                        description="Toyota JAT air-jet looms — high-speed plain and twill weave.",
                    ),
                ],
            ),
            ProductionZoneConfig(
                zone_id="zone_finishing",
                name="Zone 3: Wet Processing & Finishing",
                description="Bleaching, dyeing, calendering, and stenter finishing of grey fabric.",
                rated_power_kw=40.0,
                max_production_capacity_units_per_hour=280.0,
                machines=[
                    MachineConfig(
                        machine_id="STENTER_01",
                        name="Gas-Heated Stenter Frame",
                        rated_power_kw=22.0,
                        active_power_range_kw=(10.0, 18.0),
                        idle_power_kw=2.5,
                        description="Electric drives and fans for heat-setting and finishing.",
                    ),
                    MachineConfig(
                        machine_id="JIGGER_DYE_01",
                        name="Jigger Dyeing Machines",
                        rated_power_kw=18.0,
                        active_power_range_kw=(6.0, 12.0),
                        idle_power_kw=1.5,
                        description="Electric-heated jigger vats for reactive dyeing.",
                    ),
                ],
            ),
        ],
        shifts=[
            ShiftSchedule(
                shift_name="Shift A: Morning Production",
                start_hour=6,
                end_hour=14,
                active_zones=["zone_spinning", "zone_weaving", "zone_finishing"],
                production_target_multiplier=1.0,
                description="Full production shift; all sections running with solar support.",
            ),
            ShiftSchedule(
                shift_name="Shift B: Afternoon/Evening Production",
                start_hour=14,
                end_hour=22,
                active_zones=["zone_spinning", "zone_weaving"],
                production_target_multiplier=0.85,
                description="Spinning and weaving continue; finishing batch ends at 14:00.",
            ),
            ShiftSchedule(
                shift_name="Shift C: Night Maintenance",
                start_hour=22,
                end_hour=6,
                active_zones=[],
                production_target_multiplier=0.0,
                description="Production stopped; equipment maintenance and lubrication.",
            ),
        ],
        solar=SolarConfig(
            installed_capacity_kw=120.0,
            panel_type="Monocrystalline Rooftop (Spinning & Weaving Shed)",
            tilt_angle_deg=12.0,  # Low tilt for large flat sheds
            peak_efficiency=0.90,
        ),
        wind=WindConfig(
            installed_capacity_kw=50.0,
            turbine_type="Medium Horizontal-Axis Turbine (Utility Connected)",
            hub_height_m=35.0,
            cut_in_speed_mps=2.8,
            rated_speed_mps=10.5,
        ),
        biomass=BiomassConfig(
            installed_capacity_kw=45.0,
            fuel_type="Cotton Stalk & Textile Waste Pellets",
            daily_fuel_available_kg=220.0,
            specific_fuel_consumption_kg_per_kwh=0.78,
            fuel_cost_inr_per_kwh=3.60,
            is_dispatchable=True,
        ),
        grid=GridConfig(
            contract_demand_kw=270.0,
            voltage_level_kv=11.0,
            supply_company="Regional Utility Distribution Company",
            tariffs=[
                GridTariffPeriod(
                    period_name="Off-Peak / Night",
                    hours=[22, 23, 0, 1, 2, 3, 4, 5],
                    rate_inr_per_kwh=5.80,
                    description="Night off-peak incentive rate.",
                ),
                GridTariffPeriod(
                    period_name="Normal / Day",
                    hours=[6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17],
                    rate_inr_per_kwh=7.60,
                    description="Standard commercial operating hours rate.",
                ),
                GridTariffPeriod(
                    period_name="Peak / Evening",
                    hours=[18, 19, 20, 21],
                    rate_inr_per_kwh=10.50,
                    description="Peak evening surcharge window.",
                ),
            ],
        ),
        battery=BatteryConfig(
            capacity_kwh=120.0,
            max_charge_power_kw=60.0,
            max_discharge_power_kw=60.0,
            roundtrip_efficiency=0.91,
            min_soc_percent=20.0,
            max_soc_percent=95.0,
            initial_soc_percent=50.0,
        ),
    )


# Backward-compatible alias
def get_loomcraft_profile() -> FactoryProfile:
    return get_weavewise_profile()


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

LEGACY_FACTORY_ID_MAP: Dict[str, str] = {
    "FAC-IN-PUNE-001": "DEMO-FAC-001",
    "FAC-IN-NASHIK-002": "DEMO-FAC-002",
    "FAC-IN-TIRUPPUR-003": "DEMO-FAC-003",
}

FACTORY_REGISTRY: Dict[str, FactoryProfile] = {
    "DEMO-FAC-001": get_precisionworks_profile(),
    "DEMO-FAC-002": get_freshfield_profile(),
    "DEMO-FAC-003": get_weavewise_profile(),
}

FACTORY_SEEDS: Dict[str, int] = {
    "DEMO-FAC-001": 42,
    "DEMO-FAC-002": 137,
    "DEMO-FAC-003": 251,
    # Backward compatibility
    "FAC-IN-PUNE-001": 42,
    "FAC-IN-NASHIK-002": 137,
    "FAC-IN-TIRUPPUR-003": 251,
}

FACTORY_SIMULATION_DATES: Dict[str, str] = {
    "DEMO-FAC-001": "2026-10-14",
    "DEMO-FAC-002": "2026-10-14",
    "DEMO-FAC-003": "2026-10-14",
    # Backward compatibility
    "FAC-IN-PUNE-001": "2026-10-14",
    "FAC-IN-NASHIK-002": "2026-10-14",
    "FAC-IN-TIRUPPUR-003": "2026-10-14",
}

VALID_FACTORY_IDS = list(FACTORY_REGISTRY.keys())


def resolve_factory_id(factory_id: str) -> str:
    """Resolve an incoming factory ID, mapping legacy IDs if provided."""
    clean_id = (factory_id or "").strip()
    return LEGACY_FACTORY_ID_MAP.get(clean_id, clean_id)


def get_factory_profile(factory_id: str) -> FactoryProfile:
    """Return a FactoryProfile for the given factory ID.

    Raises:
        KeyError: if factory_id is not in FACTORY_REGISTRY.
    """
    resolved_id = resolve_factory_id(factory_id)
    if resolved_id not in FACTORY_REGISTRY:
        raise KeyError(
            f"Unknown factory_id '{factory_id}'. "
            f"Valid IDs: {VALID_FACTORY_IDS}"
        )
    return FACTORY_REGISTRY[resolved_id]


def list_factory_ids() -> list:
    return VALID_FACTORY_IDS
