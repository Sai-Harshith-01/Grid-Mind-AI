"""Factory configuration and illustrative asset profiles.

IMPORTANT NOTICE:
All values in this configuration are synthetic parameters designed for
simulation and prototyping of energy optimisation algorithms.
They must NOT be treated as measured industrial telemetry or official benchmarks.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class MachineConfig(BaseModel):
    machine_id: str
    name: str
    rated_power_kw: float
    active_power_range_kw: tuple[float, float]
    idle_power_kw: float
    description: str


class ProductionZoneConfig(BaseModel):
    zone_id: str
    name: str
    description: str
    rated_power_kw: float
    max_production_capacity_units_per_hour: float
    machines: List[MachineConfig]


class ShiftSchedule(BaseModel):
    shift_name: str
    start_hour: int
    end_hour: int
    active_zones: List[str]
    production_target_multiplier: float
    description: str


class SolarConfig(BaseModel):
    installed_capacity_kw: float = 100.0
    panel_type: str = "Monocrystalline Silicon Rooftop"
    tilt_angle_deg: float = 18.5
    peak_efficiency: float = 0.88


class WindConfig(BaseModel):
    installed_capacity_kw: float = 60.0
    turbine_type: str = "Direct-Drive Industrial Wind Turbine"
    hub_height_m: float = 30.0
    cut_in_speed_mps: float = 3.0
    rated_speed_mps: float = 11.0


class BiomassConfig(BaseModel):
    installed_capacity_kw: float = 50.0
    fuel_type: str = "Agro-Waste Briquettes (Cotton Stalk & Bagasse)"
    daily_fuel_available_kg: float = 250.0
    specific_fuel_consumption_kg_per_kwh: float = 0.80
    fuel_cost_inr_per_kwh: float = 4.20
    is_dispatchable: bool = True

    @property
    def daily_energy_capacity_kwh(self) -> float:
        """Maximum daily energy output based on available fuel."""
        return self.daily_fuel_available_kg / self.specific_fuel_consumption_kg_per_kwh


class GridTariffPeriod(BaseModel):
    period_name: str
    hours: List[int]
    rate_inr_per_kwh: float
    description: str


class GridConfig(BaseModel):
    contract_demand_kw: float = 250.0
    voltage_level_kv: float = 11.0
    supply_company: str = "Regional Utility Distribution Company"
    tariffs: List[GridTariffPeriod] = Field(
        default_factory=lambda: [
            GridTariffPeriod(
                period_name="Off-Peak / Night",
                hours=[22, 23, 0, 1, 2, 3, 4, 5],
                rate_inr_per_kwh=6.50,
                description="Night incentive hours with lowest electricity rate.",
            ),
            GridTariffPeriod(
                period_name="Normal / Day",
                hours=[6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17],
                rate_inr_per_kwh=8.20,
                description="Standard commercial operating hours rate.",
            ),
            GridTariffPeriod(
                period_name="Peak / Evening Surcharge",
                hours=[18, 19, 20, 21],
                rate_inr_per_kwh=11.80,
                description="High-demand evening surcharge window (+INR 3.60/kWh).",
            ),
        ]
    )


class BatteryConfig(BaseModel):
    capacity_kwh: float = 100.0
    max_charge_power_kw: float = 50.0
    max_discharge_power_kw: float = 50.0
    roundtrip_efficiency: float = 0.90
    min_soc_percent: float = 20.0
    max_soc_percent: float = 95.0
    initial_soc_percent: float = 50.0


class FactoryProfile(BaseModel):
    factory_id: str = "DEMO-FAC-001"
    name: str = "PrecisionWorks Factory"
    sector: str = "Precision Engineering & CNC Machining"
    location: str = "Fictional Demonstration Facility (Synthetic Profile)"
    currency: str = "INR"
    power_unit: str = "kW"
    energy_unit: str = "kWh"
    production_unit: str = "finished_components"
    total_rated_connected_power_kw: float = 260.0
    facility_baseload_kw: float = 10.0

    zones: List[ProductionZoneConfig]
    shifts: List[ShiftSchedule]
    solar: SolarConfig = Field(default_factory=SolarConfig)
    wind: WindConfig = Field(default_factory=WindConfig)
    biomass: BiomassConfig = Field(default_factory=BiomassConfig)
    grid: GridConfig = Field(default_factory=GridConfig)
    battery: BatteryConfig = Field(default_factory=BatteryConfig)


def get_default_factory_profile() -> FactoryProfile:
    """Return the default factory profile configuration for PrecisionWorks Factory."""
    return FactoryProfile(
        zones=[
            ProductionZoneConfig(
                zone_id="zone_cnc",
                name="Zone 1: CNC Machining & Milling",
                description="High-precision 5-axis CNC machining centers and auxiliary pneumatic supply.",
                rated_power_kw=120.0,
                max_production_capacity_units_per_hour=120.0,
                machines=[
                    MachineConfig(
                        machine_id="CNC_VMC_01",
                        name="Vertical Machining Center 1",
                        rated_power_kw=45.0,
                        active_power_range_kw=(18.0, 26.0),
                        idle_power_kw=3.5,
                        description="5-axis precision milling machine for automotive cylinder heads.",
                    ),
                    MachineConfig(
                        machine_id="CNC_VMC_02",
                        name="Vertical Machining Center 2",
                        rated_power_kw=45.0,
                        active_power_range_kw=(18.0, 26.0),
                        idle_power_kw=3.5,
                        description="High-speed CNC lathe & milling unit for transmission shafts.",
                    ),
                    MachineConfig(
                        machine_id="COMP_AIR_01",
                        name="Industrial Air Compressor Main",
                        rated_power_kw=30.0,
                        active_power_range_kw=(14.0, 20.0),
                        idle_power_kw=4.0,
                        description="Screw compressor supplying pneumatic tool changers and clamping.",
                    ),
                ],
            ),
            ProductionZoneConfig(
                zone_id="zone_heat_treatment",
                name="Zone 2: Induction Heat Treatment & Annealing",
                description="Electromagnetic surface hardening, quench bath circulation, and induction tempering.",
                rated_power_kw=90.0,
                max_production_capacity_units_per_hour=80.0,
                machines=[
                    MachineConfig(
                        machine_id="IND_FURNACE_01",
                        name="Induction Hardening Furnace",
                        rated_power_kw=75.0,
                        active_power_range_kw=(35.0, 50.0),
                        idle_power_kw=5.0,
                        description="Electromagnetic induction coil for surface heat hardening.",
                    ),
                    MachineConfig(
                        machine_id="QUENCH_PUMP_01",
                        name="Quench Circulation Pumps",
                        rated_power_kw=15.0,
                        active_power_range_kw=(6.0, 10.0),
                        idle_power_kw=1.5,
                        description="Coolant recirculating pumps and chiller heat exchanger.",
                    ),
                ],
            ),
            ProductionZoneConfig(
                zone_id="zone_finishing_packaging",
                name="Zone 3: Finishing, Inspection & Packaging",
                description="Fine grinding, robotic optical inspection (CMM), and automated packaging.",
                rated_power_kw=40.0,
                max_production_capacity_units_per_hour=100.0,
                machines=[
                    MachineConfig(
                        machine_id="GRIND_DEBURR_01",
                        name="Surface Grinding and Deburring",
                        rated_power_kw=25.0,
                        active_power_range_kw=(8.0, 14.0),
                        idle_power_kw=2.0,
                        description="Continuous magnetic surface grinding and ultrasonic deburring.",
                    ),
                    MachineConfig(
                        machine_id="INSPECT_PACK_01",
                        name="Automated Inspection and Packaging",
                        rated_power_kw=15.0,
                        active_power_range_kw=(4.0, 8.0),
                        idle_power_kw=1.0,
                        description="High-speed optical CMM dimensional scanner and boxing arm.",
                    ),
                ],
            ),
        ],
        shifts=[
            ShiftSchedule(
                shift_name="Shift 1: Morning Primary",
                start_hour=8,
                end_hour=16,
                active_zones=["zone_cnc", "zone_heat_treatment", "zone_finishing_packaging"],
                production_target_multiplier=1.0,
                description="Full factory active shift running at rated throughput capacity.",
            ),
            ShiftSchedule(
                shift_name="Shift 2: Evening Secondary",
                start_hour=16,
                end_hour=24,
                active_zones=["zone_cnc", "zone_finishing_packaging"],
                production_target_multiplier=0.75,
                description="Moderate production shift; heat treatment furnace curtailed during peak tariff window.",
            ),
            ShiftSchedule(
                shift_name="Shift 3: Night Off-Shift / Maintenance",
                start_hour=0,
                end_hour=8,
                active_zones=[],
                production_target_multiplier=0.0,
                description="Production paused; maintenance checks and machinery on standby/idle power.",
            ),
        ],
    )
