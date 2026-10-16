"""Deterministic renewable energy allocation and optimisation engine.

Solves the constrained economic dispatch problem for MSME factories
using linear programming (HiGHS solver via SciPy).

Minimises total energy procurement cost across intervals:
    min sum(c_solar * x_solar + c_wind * x_wind + c_biomass * x_biomass + c_grid * x_grid)

Subject to:
    1. Energy balance: x_solar + x_wind + x_biomass + x_grid = factory_demand
    2. Solar availability: 0 <= x_solar <= min(solar_available, solar_capacity)
    3. Wind availability: 0 <= x_wind <= min(wind_available, wind_capacity)
    4. Biomass generator capacity: 0 <= x_biomass <= biomass_capacity
    5. Biomass daily fuel budget: sum(x_biomass) <= daily_fuel_energy_cap
    6. Grid contract demand: 0 <= x_grid <= grid_contract_demand
    7. Nonnegativity: all x >= 0

IMPORTANT:
All values are simulated scenario evaluations based on synthetic MSME telemetry.
Savings are scenario projections, not verified real-world operational guarantees.
"""

from typing import Dict, List, Optional, Tuple
import numpy as np
from scipy.optimize import linprog

from app.data.factory_config import FactoryProfile
from app.schemas.factory import SimulationMetadata, TimeSeriesInterval
from app.schemas.optimization import (
    HourlyBaselineItem,
    IntervalSourceAllocation,
    OptimizationBaselineResponse,
    OptimizationRunResponse,
    OptimizationSummaryResponse,
    SourceUtilizationSummary,
)
from app.services.factory_data_service import factory_data_service, DEFAULT_FACTORY_ID


class EnergyOptimizerService:
    """Service providing linear programming dispatch optimization and baseline comparison."""

    def __init__(self):
        # Marginal operating costs (INR/kWh)
        self.solar_marginal_cost_inr = 0.0
        self.wind_marginal_cost_inr = 0.0

    def calculate_baseline(
        self,
        intervals: List[TimeSeriesInterval],
        profile: FactoryProfile,
        tariff_multiplier: float = 1.0,
    ) -> OptimizationBaselineResponse:
        """Calculate reference 100% grid-supplied cost and capacity feasibility."""
        hourly_items: List[HourlyBaselineItem] = []
        total_demand_kwh = 0.0
        total_cost_inr = 0.0
        max_demand_kw = 0.0
        is_capacity_feasible = True

        contract_demand = profile.grid.contract_demand_kw

        for item in intervals:
            kwh = item.total_factory_energy_demand_kwh
            kw = item.total_factory_demand_kw
            rate = round(item.grid.tariff_rate_inr_per_kwh * tariff_multiplier, 2)
            cost = round(kwh * rate, 2)

            exceeds_cap = kw > contract_demand
            if exceeds_cap:
                is_capacity_feasible = False

            total_demand_kwh += kwh
            total_cost_inr += cost
            if kw > max_demand_kw:
                max_demand_kw = kw

            hourly_items.append(
                HourlyBaselineItem(
                    interval_index=item.interval_index,
                    timestamp=item.timestamp,
                    demand_kwh=kwh,
                    demand_kw=kw,
                    grid_tariff_inr_per_kwh=rate,
                    baseline_cost_inr=cost,
                    is_peak_tariff=item.grid.is_peak_tariff_period,
                    exceeds_grid_capacity=exceeds_cap,
                )
            )

        total_demand_kwh = round(total_demand_kwh, 2)
        total_cost_inr = round(total_cost_inr, 2)
        blended_rate = (
            round(total_cost_inr / total_demand_kwh, 2) if total_demand_kwh > 0 else 0.0
        )

        return OptimizationBaselineResponse(
            factory_id=profile.factory_id,
            simulation_date=intervals[0].timestamp[:10] if intervals else "2026-10-14",
            total_factory_demand_kwh=total_demand_kwh,
            grid_contract_demand_kw=contract_demand,
            is_capacity_feasible=is_capacity_feasible,
            peak_factory_demand_kw=round(max_demand_kw, 2),
            total_baseline_cost_inr=total_cost_inr,
            average_blended_rate_inr_per_kwh=blended_rate,
            hourly_baseline=hourly_items,
            simulation_metadata=SimulationMetadata(
                simulation_date=intervals[0].timestamp[:10] if intervals else "2026-10-14"
            ),
        )

    def optimize(
        self,
        intervals: List[TimeSeriesInterval],
        profile: FactoryProfile,
        solar_multiplier: float = 1.0,
        tariff_multiplier: float = 1.0,
    ) -> OptimizationRunResponse:
        """Execute linear programming optimization across intervals."""
        N = len(intervals)
        if N == 0:
            raise ValueError("Cannot optimize across empty intervals.")

        # Baseline reference
        baseline = self.calculate_baseline(intervals, profile, tariff_multiplier=tariff_multiplier)

        # Pre-check physical capacity per interval
        infeasible_intervals: List[int] = []
        unmet_demand_map: Dict[int, float] = {}
        for item in intervals:
            solar_avail = round(item.generation.solar_energy_kwh * solar_multiplier, 2)
            max_avail = (
                solar_avail
                + item.generation.wind_energy_kwh
                + (profile.biomass.installed_capacity_kw * item.interval_duration_hours)
                + (profile.grid.contract_demand_kw * item.interval_duration_hours)
            )
            if item.total_factory_energy_demand_kwh > max_avail:
                infeasible_intervals.append(item.interval_index)
                unmet_demand_map[item.interval_index] = round(
                    item.total_factory_energy_demand_kwh - max_avail, 2
                )

        # Build LP problem: 4 decision variables per interval [solar, wind, biomass, grid]
        # Total variables = 4 * N
        c = []
        bounds = []
        b_eq = []
        A_eq = np.zeros((N, 4 * N))

        # Biomass fuel cost
        c_biomass = profile.biomass.fuel_cost_inr_per_kwh

        for h, item in enumerate(intervals):
            tariff = round(item.grid.tariff_rate_inr_per_kwh * tariff_multiplier, 2)
            duration = item.interval_duration_hours

            # Objective coefficients with deterministic tie-breaking (solar slightly favored over wind if both 0)
            c.extend([
                self.solar_marginal_cost_inr,
                self.wind_marginal_cost_inr + 1e-6,
                c_biomass,
                tariff,
            ])

            # Bounds
            solar_avail = round(item.generation.solar_energy_kwh * solar_multiplier, 2)
            s_max = min(solar_avail, profile.solar.installed_capacity_kw * duration)
            w_max = min(item.generation.wind_energy_kwh, profile.wind.installed_capacity_kw * duration)
            b_max = profile.biomass.installed_capacity_kw * duration
            g_max = profile.grid.contract_demand_kw * duration

            bounds.append((0.0, s_max))
            bounds.append((0.0, w_max))
            bounds.append((0.0, b_max))
            bounds.append((0.0, g_max))

            # Energy balance equality
            A_eq[h, 4 * h : 4 * h + 4] = 1.0
            b_eq.append(item.total_factory_energy_demand_kwh)

        # Inequality constraint: Biomass daily fuel budget (kg / sfc = kWh)
        daily_biomass_kwh_cap = profile.biomass.daily_energy_capacity_kwh
        A_ub = np.zeros((1, 4 * N))
        for h in range(N):
            A_ub[0, 4 * h + 2] = 1.0
        b_ub = [daily_biomass_kwh_cap]

        # Solve LP using HiGHS
        res = linprog(c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq, bounds=bounds, method="highs")

        is_feasible = (res.status == 0) and (len(infeasible_intervals) == 0)
        solver_status_msg = res.message

        interval_allocations: List[IntervalSourceAllocation] = []
        total_demand_served = 0.0
        total_optimised_cost = 0.0
        total_solar_alloc = 0.0
        total_wind_alloc = 0.0
        total_biomass_alloc = 0.0
        total_grid_alloc = 0.0
        peak_grid_kw = 0.0

        for h, item in enumerate(intervals):
            kwh_demand = item.total_factory_energy_demand_kwh
            tariff = round(item.grid.tariff_rate_inr_per_kwh * tariff_multiplier, 2)
            duration = item.interval_duration_hours
            solar_avail = round(item.generation.solar_energy_kwh * solar_multiplier, 2)

            if res.status == 0:
                s_alloc = round(float(res.x[4 * h + 0]), 2)
                w_alloc = round(float(res.x[4 * h + 1]), 2)
                b_alloc = round(float(res.x[4 * h + 2]), 2)
                g_alloc = round(float(res.x[4 * h + 3]), 2)
            else:
                # If solver failed, report zero allocations rather than fabricated numbers
                s_alloc = 0.0
                w_alloc = 0.0
                b_alloc = 0.0
                g_alloc = 0.0

            renew_total = round(s_alloc + w_alloc + b_alloc, 2)
            src_op_cost = round(b_alloc * c_biomass, 2)
            grid_cost = round(g_alloc * tariff, 2)
            int_cost = round(src_op_cost + grid_cost, 2)
            base_cost = round(kwh_demand * tariff, 2)
            int_savings = round(base_cost - int_cost, 2)

            unmet = unmet_demand_map.get(h, max(0.0, round(kwh_demand - (s_alloc + w_alloc + b_alloc + g_alloc), 2)))
            balance_err = round(abs((s_alloc + w_alloc + b_alloc + g_alloc) - (kwh_demand - unmet)), 4)

            # Identify active constraints
            active_constraints: List[str] = []
            if s_alloc >= solar_avail - 0.05 and solar_avail > 0:
                active_constraints.append("solar_availability_cap")
            if w_alloc >= item.generation.wind_energy_kwh - 0.05 and item.generation.wind_energy_kwh > 0:
                active_constraints.append("wind_availability_cap")
            if b_alloc >= (profile.biomass.installed_capacity_kw * duration) - 0.05:
                active_constraints.append("biomass_power_capacity")
            if g_alloc >= (profile.grid.contract_demand_kw * duration) - 0.05:
                active_constraints.append("grid_contract_demand_limit")

            # Convert allocated grid energy (kWh) to average interval power (kW)
            interval_grid_power_kw = (g_alloc / duration) if duration > 0 else 0.0
            if interval_grid_power_kw > peak_grid_kw:
                peak_grid_kw = interval_grid_power_kw

            total_demand_served += (s_alloc + w_alloc + b_alloc + g_alloc)
            total_optimised_cost += int_cost
            total_solar_alloc += s_alloc
            total_wind_alloc += w_alloc
            total_biomass_alloc += b_alloc
            total_grid_alloc += g_alloc

            interval_allocations.append(
                IntervalSourceAllocation(
                    interval_index=h,
                    timestamp=item.timestamp,
                    factory_demand_kwh=kwh_demand,
                    solar_available_kwh=solar_avail,
                    solar_allocated_kwh=s_alloc,
                    wind_available_kwh=item.generation.wind_energy_kwh,
                    wind_allocated_kwh=w_alloc,
                    biomass_available_kwh=item.generation.biomass_max_energy_kwh,
                    biomass_allocated_kwh=b_alloc,
                    grid_allocated_kwh=g_alloc,
                    renewable_allocated_total_kwh=renew_total,
                    grid_tariff_inr_per_kwh=tariff,
                    source_operating_cost_inr=src_op_cost,
                    grid_tariff_cost_inr=grid_cost,
                    interval_total_cost_inr=int_cost,
                    baseline_grid_cost_inr=base_cost,
                    interval_savings_inr=int_savings,
                    unmet_demand_kwh=unmet,
                    active_constraints=active_constraints,
                    energy_balance_error=balance_err,
                    is_feasible=unmet <= 0.01,
                )
            )

        # Post-solve physical constraint verification
        constraint_violations: List[str] = []
        tol = 1e-2

        if res.status != 0:
            constraint_violations.append(f"HiGHS solver reported non-zero status: {res.message}")

        if total_biomass_alloc > daily_biomass_kwh_cap + tol:
            constraint_violations.append(
                f"Biomass total allocation ({total_biomass_alloc:.2f} kWh) exceeds daily fuel budget ({daily_biomass_kwh_cap:.2f} kWh)"
            )

        for h, alloc in enumerate(interval_allocations):
            item = intervals[h]
            dur = item.interval_duration_hours
            s_avail = round(item.generation.solar_energy_kwh * solar_multiplier, 2)
            w_avail = round(item.generation.wind_energy_kwh, 2)
            b_cap = round(profile.biomass.installed_capacity_kw * dur, 2)
            g_cap = round(profile.grid.contract_demand_kw * dur, 2)

            if alloc.solar_allocated_kwh < -tol:
                constraint_violations.append(f"Hour {h}: Solar allocation is negative ({alloc.solar_allocated_kwh})")
            if alloc.solar_allocated_kwh > s_avail + tol:
                constraint_violations.append(f"Hour {h}: Solar allocation ({alloc.solar_allocated_kwh}) exceeds available ({s_avail})")

            if alloc.wind_allocated_kwh < -tol:
                constraint_violations.append(f"Hour {h}: Wind allocation is negative ({alloc.wind_allocated_kwh})")
            if alloc.wind_allocated_kwh > w_avail + tol:
                constraint_violations.append(f"Hour {h}: Wind allocation ({alloc.wind_allocated_kwh}) exceeds available ({w_avail})")

            if alloc.biomass_allocated_kwh < -tol:
                constraint_violations.append(f"Hour {h}: Biomass allocation is negative ({alloc.biomass_allocated_kwh})")
            if alloc.biomass_allocated_kwh > b_cap + tol:
                constraint_violations.append(f"Hour {h}: Biomass allocation ({alloc.biomass_allocated_kwh}) exceeds capacity ({b_cap})")

            if alloc.grid_allocated_kwh < -tol:
                constraint_violations.append(f"Hour {h}: Grid allocation is negative ({alloc.grid_allocated_kwh})")
            if alloc.grid_allocated_kwh > g_cap + tol:
                constraint_violations.append(f"Hour {h}: Grid allocation ({alloc.grid_allocated_kwh}) exceeds contract demand ({g_cap})")

            if alloc.unmet_demand_kwh > tol:
                constraint_violations.append(f"Hour {h}: Unmet demand ({alloc.unmet_demand_kwh} kWh)")

        is_feasible = (len(constraint_violations) == 0) and (len(infeasible_intervals) == 0)
        if not is_feasible:
            solver_status_msg = f"Infeasible: {'; '.join(constraint_violations[:3])}" if constraint_violations else res.message
        else:
            solver_status_msg = "Optimal solution found. All physical energy balance and capacity constraints satisfied."

        total_demand_served = round(total_demand_served, 2)
        total_optimised_cost = round(total_optimised_cost, 2)
        total_baseline_cost = baseline.total_baseline_cost_inr
        estimated_savings = round(total_baseline_cost - total_optimised_cost, 2)

        # Savings percentage with zero-baseline protection
        savings_pct = (
            round((estimated_savings / total_baseline_cost) * 100.0, 2)
            if total_baseline_cost > 0
            else 0.0
        )

        total_renew_alloc = round(total_solar_alloc + total_wind_alloc + total_biomass_alloc, 2)
        renew_alloc_pct = (
            round((total_renew_alloc / total_demand_served) * 100.0, 2)
            if total_demand_served > 0
            else 0.0
        )
        grid_share_pct = (
            round((total_grid_alloc / total_demand_served) * 100.0, 2)
            if total_demand_served > 0
            else 0.0
        )

        contract_demand = profile.grid.contract_demand_kw
        peak_grid_util = round((peak_grid_kw / contract_demand) * 100.0, 2) if contract_demand > 0 else 0.0

        # Biomass fuel consumption (kWh * kg/kWh = kg)
        sfc = profile.biomass.specific_fuel_consumption_kg_per_kwh
        biomass_fuel_consumed = round(total_biomass_alloc * sfc, 2)
        biomass_remaining_fuel = round(
            max(0.0, profile.biomass.daily_fuel_available_kg - biomass_fuel_consumed), 2
        )

        # Production fulfilment
        total_prod_units = round(sum(i.actual_production_output_units for i in intervals), 1)

        # Source utilization breakdown
        total_solar_avail = round(sum(i.generation.solar_energy_kwh * solar_multiplier for i in intervals), 2)
        total_wind_avail = round(sum(i.generation.wind_energy_kwh for i in intervals), 2)
        total_biomass_avail = round(profile.biomass.daily_energy_capacity_kwh, 2)
        total_grid_avail = round(contract_demand * N, 2)

        source_breakdown = [
            SourceUtilizationSummary(
                source="solar",
                total_available_kwh=total_solar_avail,
                total_allocated_kwh=round(total_solar_alloc, 2),
                utilization_rate_percent=round((total_solar_alloc / total_solar_avail) * 100, 2) if total_solar_avail > 0 else 0.0,
                total_cost_inr=0.0,
                effective_cost_per_kwh_inr=0.0,
            ),
            SourceUtilizationSummary(
                source="wind",
                total_available_kwh=total_wind_avail,
                total_allocated_kwh=round(total_wind_alloc, 2),
                utilization_rate_percent=round((total_wind_alloc / total_wind_avail) * 100, 2) if total_wind_avail > 0 else 0.0,
                total_cost_inr=0.0,
                effective_cost_per_kwh_inr=0.0,
            ),
            SourceUtilizationSummary(
                source="biomass",
                total_available_kwh=total_biomass_avail,
                total_allocated_kwh=round(total_biomass_alloc, 2),
                utilization_rate_percent=round((total_biomass_alloc / total_biomass_avail) * 100, 2) if total_biomass_avail > 0 else 0.0,
                total_cost_inr=round(total_biomass_alloc * c_biomass, 2),
                effective_cost_per_kwh_inr=c_biomass,
            ),
            SourceUtilizationSummary(
                source="grid",
                total_available_kwh=total_grid_avail,
                total_allocated_kwh=round(total_grid_alloc, 2),
                utilization_rate_percent=round((total_grid_alloc / total_grid_avail) * 100, 2) if total_grid_avail > 0 else 0.0,
                total_cost_inr=round(sum(i.grid_tariff_cost_inr for i in interval_allocations), 2),
                effective_cost_per_kwh_inr=round(
                    sum(i.grid_tariff_cost_inr for i in interval_allocations) / total_grid_alloc, 2
                ) if total_grid_alloc > 0 else 0.0,
            ),
        ]

        unmet_demand_total = round(sum(i.unmet_demand_kwh for i in interval_allocations), 2)

        is_std = (abs(solar_multiplier - 1.0) < 1e-4) and (abs(tariff_multiplier - 1.0) < 1e-4)
        scenario_label = (
            "Standard Baseline (100% Solar, Standard ToD)"
            if is_std
            else f"What-If Scenario (Solar: {int(round(solar_multiplier * 100))}%, Tariffs: {int(round(tariff_multiplier * 100))}%)"
        )

        return OptimizationRunResponse(
            factory_id=profile.factory_id,
            simulation_date=intervals[0].timestamp[:10] if intervals else "2026-10-14",
            is_feasible=is_feasible,
            solver_status=solver_status_msg,
            total_demand_kwh=baseline.total_factory_demand_kwh,
            total_demand_served_kwh=total_demand_served,
            unmet_demand_total_kwh=unmet_demand_total,
            baseline_grid_only_cost_inr=total_baseline_cost,
            optimised_supply_cost_inr=total_optimised_cost,
            estimated_savings_inr=estimated_savings,
            estimated_savings_percentage=savings_pct,
            renewable_energy_allocated_kwh=total_renew_alloc,
            renewable_allocation_percentage=renew_alloc_pct,
            grid_energy_allocated_kwh=round(total_grid_alloc, 2),
            grid_energy_share_percentage=grid_share_pct,
            peak_grid_power_kw=round(peak_grid_kw, 2),
            peak_grid_contract_utilisation_percent=peak_grid_util,
            biomass_energy_consumed_kwh=round(total_biomass_alloc, 2),
            biomass_fuel_consumed_kg=biomass_fuel_consumed,
            biomass_remaining_fuel_budget_kg=biomass_remaining_fuel,
            infeasible_intervals_count=len(infeasible_intervals),
            production_fulfilment_units=total_prod_units,
            baseline_is_capacity_feasible=baseline.is_capacity_feasible,
            active_scenario_name=scenario_label,
            solar_multiplier=solar_multiplier,
            tariff_multiplier=tariff_multiplier,
            disclaimer="Modelled scenario projection based on synthetic telemetry. Not guaranteed commercial savings.",
            intervals=interval_allocations,
            source_breakdown=source_breakdown,
            simulation_metadata=profile.solar.__class__.__name__ and SimulationMetadata(
                simulation_date=intervals[0].timestamp[:10] if intervals else "2026-10-14"
            ),
        )

    @classmethod
    def get_baseline(
        cls, factory_id: str = DEFAULT_FACTORY_ID, tariff_multiplier: float = 1.0
    ) -> OptimizationBaselineResponse:
        """Return cached factory baseline comparison."""
        timeseries_resp = factory_data_service.get_timeseries(factory_id)
        profile = factory_data_service.get_raw_profile(factory_id)
        return cls().calculate_baseline(
            timeseries_resp.intervals, profile, tariff_multiplier=tariff_multiplier
        )

    @classmethod
    def run_optimization(
        cls,
        factory_id: str = DEFAULT_FACTORY_ID,
        solar_multiplier: float = 1.0,
        tariff_multiplier: float = 1.0,
    ) -> OptimizationRunResponse:
        """Run optimization on the current factory simulation."""
        timeseries_resp = factory_data_service.get_timeseries(factory_id)
        profile = factory_data_service.get_raw_profile(factory_id)
        return cls().optimize(
            timeseries_resp.intervals,
            profile,
            solar_multiplier=solar_multiplier,
            tariff_multiplier=tariff_multiplier,
        )

    @classmethod
    def get_summary(
        cls,
        factory_id: str = DEFAULT_FACTORY_ID,
        solar_multiplier: float = 1.0,
        tariff_multiplier: float = 1.0,
    ) -> OptimizationSummaryResponse:
        """Return executive summary of the optimization solution."""
        full_run = cls.run_optimization(
            factory_id=factory_id,
            solar_multiplier=solar_multiplier,
            tariff_multiplier=tariff_multiplier,
        )
        return OptimizationSummaryResponse(
            factory_id=full_run.factory_id,
            simulation_date=full_run.simulation_date,
            is_feasible=full_run.is_feasible,
            solver_status=full_run.solver_status,
            total_demand_kwh=full_run.total_demand_kwh,
            total_demand_served_kwh=full_run.total_demand_served_kwh,
            unmet_demand_total_kwh=full_run.unmet_demand_total_kwh,
            baseline_grid_only_cost_inr=full_run.baseline_grid_only_cost_inr,
            optimised_supply_cost_inr=full_run.optimised_supply_cost_inr,
            estimated_savings_inr=full_run.estimated_savings_inr,
            estimated_savings_percentage=full_run.estimated_savings_percentage,
            renewable_energy_allocated_kwh=full_run.renewable_energy_allocated_kwh,
            renewable_allocation_percentage=full_run.renewable_allocation_percentage,
            grid_energy_allocated_kwh=full_run.grid_energy_allocated_kwh,
            grid_energy_share_percentage=full_run.grid_energy_share_percentage,
            peak_grid_power_kw=full_run.peak_grid_power_kw,
            peak_grid_contract_utilisation_percent=full_run.peak_grid_contract_utilisation_percent,
            biomass_energy_consumed_kwh=full_run.biomass_energy_consumed_kwh,
            biomass_fuel_consumed_kg=full_run.biomass_fuel_consumed_kg,
            biomass_remaining_fuel_budget_kg=full_run.biomass_remaining_fuel_budget_kg,
            infeasible_intervals_count=full_run.infeasible_intervals_count,
            production_fulfilment_units=full_run.production_fulfilment_units,
            baseline_is_capacity_feasible=full_run.baseline_is_capacity_feasible,
            active_scenario_name=full_run.active_scenario_name,
            solar_multiplier=full_run.solar_multiplier,
            tariff_multiplier=full_run.tariff_multiplier,
            disclaimer=full_run.disclaimer,
            simulation_metadata=full_run.simulation_metadata,
        )


energy_optimizer_service = EnergyOptimizerService()

