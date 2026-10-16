# GridMind AI — Phase 4 Renewable Energy Allocation & Optimisation Engine

## 1. Executive Summary & Purpose

This document provides the mathematical formulation, constraints, solver architecture, and API specifications for the **Phase 4 Renewable Energy Allocation and Optimisation Engine**.

The optimiser solves the constrained economic dispatch problem for MSME factories, answering the core engineering question:
> *How should an MSME factory allocate on-site captive solar, wind, and dispatchable biomass generation alongside time-dependent grid electricity tariffs to minimise total energy supply cost while guaranteeing 100% demand satisfaction and respecting all physical and fuel limits?*

> [!IMPORTANT]
> **SIMULATION & SCENARIO DISCLAIMER**  
> All inputs, load curves, equipment capacities, and tariff schedules are synthetic parameters. All calculated economic savings, renewable allocation percentages, and fuel consumptions are **scenario projections**, not verified empirical measurements from physical factory telemetry.

---

## 2. Mathematical Optimization Model

The dispatch problem is formulated as a deterministic **Linear Program (LP)** solved via the **HiGHS** simplex/interior-point solver through SciPy (`scipy.optimize.linprog(method='highs')`).

### 2.1. Decision Variables
Let $N = 24$ be the number of hourly intervals in the daily horizon ($h \in \{0, 1, \dots, N-1\}$).  
For each interval $h$:
- $x_{\text{solar}, h} \ge 0$: Solar energy allocated to factory demand [kWh]
- $x_{\text{wind}, h} \ge 0$: Wind energy allocated to factory demand [kWh]
- $x_{\text{biomass}, h} \ge 0$: Biomass generator energy dispatched [kWh]
- $x_{\text{grid}, h} \ge 0$: Utility grid electricity imported [kWh]

Total decision vector dimension: $4N = 96$ continuous variables.

### 2.2. Objective Function
Minimise total energy supply expenditure across all intervals:
$$\min_{x} \sum_{h=0}^{N-1} \left( c_{\text{solar}} x_{\text{solar}, h} + c_{\text{wind}} x_{\text{wind}, h} + c_{\text{biomass}} x_{\text{biomass}, h} + c_{\text{grid}, h} x_{\text{grid}, h} \right)$$

Where the marginal operating costs are configured as:
| Energy Source | Cost Parameter | Configured Value | Economic Rationale |
| :--- | :--- | :--- | :--- |
| **Solar PV** | $c_{\text{solar}}$ | ₹0.00 / kWh | Zero marginal fuel cost (captive rooftop asset) |
| **Wind Turbine** | $c_{\text{wind}}$ | ₹0.00 / kWh (+ $10^{-6}$ tie-breaker) | Zero marginal fuel cost (captive wind asset) |
| **Biomass Cogeneration** | $c_{\text{biomass}}$ | ₹4.20 / kWh | Agro-waste briquettes fuel cost ($0.80\text{ kg/kWh} \times ₹5.25\text{/kg}$) |
| **Grid Electricity** | $c_{\text{grid}, h}$ | ₹6.50 – ₹11.80 / kWh | Dynamic Time-of-Day (ToD) tariff under Regional Utility HT-1 schedule |

#### Economic Merit Order Dispatch
Because $c_{\text{solar}} \approx c_{\text{wind}} (₹0.00) < c_{\text{biomass}} (₹4.20) < c_{\text{grid, off-peak}} (₹6.50) < c_{\text{grid, normal}} (₹8.20) < c_{\text{grid, peak}} (₹11.80)$, the linear program rigorously adheres to the least-cost merit order:
1. Solar and wind are fully dispatched up to real-time availability.
2. Biomass is dispatched up to its 50 kW capacity to displace expensive peak and normal grid electricity, bounded by its daily fuel budget.
3. Grid electricity supplies only the remaining balance up to the 250 kW contract demand.

---

### 2.3. Constraints

#### A. Energy Balance (Equality Constraint)
In every interval $h$, the sum of allocated power must exactly equal factory demand:
$$x_{\text{solar}, h} + x_{\text{wind}, h} + x_{\text{biomass}, h} + x_{\text{grid}, h} = E_{\text{demand}, h} \quad \forall h \in \{0, \dots, N-1\}$$

#### B. Solar Availability & Nameplate Upper Bound
$$0 \le x_{\text{solar}, h} \le \min\left( E_{\text{solar\_available}, h}, \; C_{\text{solar}} \times \Delta t_h \right) \quad \forall h$$
Where $C_{\text{solar}} = 100.0\text{ kW}$ and $\Delta t_h = 1.0\text{ h}$.

#### C. Wind Availability & Nameplate Upper Bound
$$0 \le x_{\text{wind}, h} \le \min\left( E_{\text{wind\_available}, h}, \; C_{\text{wind}} \times \Delta t_h \right) \quad \forall h$$
Where $C_{\text{wind}} = 60.0\text{ kW}$.

#### D. Biomass Generator Capacity Upper Bound
$$0 \le x_{\text{biomass}, h} \le C_{\text{biomass}} \times \Delta t_h \quad \forall h$$
Where $C_{\text{biomass}} = 50.0\text{ kW}$ ($50.0\text{ kWh}$ maximum output per 1-hour interval).

#### E. Biomass Daily Fuel Energy Budget Constraint (Coupled Inequality)
$$\sum_{h=0}^{N-1} x_{\text{biomass}, h} \le E_{\text{biomass\_daily\_cap}} = \frac{M_{\text{fuel\_available\_kg}}}{\text{SFC}} = \frac{250.0\text{ kg}}{0.80\text{ kg/kWh}} = 312.5\text{ kWh}$$

#### F. Grid Sanctioned Contract Demand Limit
$$0 \le x_{\text{grid}, h} \le C_{\text{grid}} \times \Delta t_h \quad \forall h$$
Where $C_{\text{grid}} = 250.0\text{ kW}$ ($250.0\text{ kWh}$ maximum hourly draw).

---

## 3. Baseline vs. Optimised Scenario Methodology

### 3.1. Reference Grid-Only Baseline Scenario
The baseline scenario models the reference operating cost assuming the factory had zero on-site renewable generation:
$$\text{Baseline Cost} = \sum_{h=0}^{N-1} \left( E_{\text{demand}, h} \times c_{\text{grid}, h} \right) \quad [\text{INR / ₹}]$$
If $E_{\text{demand}, h} > C_{\text{grid}} \times \Delta t_h$ for any interval, the baseline is flagged with `is_capacity_feasible = False`.

### 3.2. Performance Metrics & Formulas
- **Estimated Savings (INR)**:
  $$\text{Estimated Savings} = \text{Baseline Cost} - \text{Optimised Cost}$$
- **Estimated Savings (%)**:
  $$\text{Savings \%} = \begin{cases} \dfrac{\text{Estimated Savings}}{\text{Baseline Cost}} \times 100\% & \text{if Baseline Cost} > 0 \\ 0.0\% & \text{if Baseline Cost} = 0 \end{cases}$$
- **Renewable Allocation Percentage**:
  $$\text{Renewable Allocation \%} = \frac{\sum_{h} (x_{\text{solar}, h} + x_{\text{wind}, h} + x_{\text{biomass}, h})}{\text{Total Demand Served}} \times 100\%$$
  *(Critically uses **allocated** renewable energy, NOT raw meteorological availability!)*
- **Grid Share Percentage**:
  $$\text{Grid Share \%} = \frac{\sum_{h} x_{\text{grid}, h}}{\text{Total Demand Served}} \times 100\%$$
- **Peak Grid Power & Contract Utilisation**:
  $$P_{\text{grid, peak}} = \max_h (x_{\text{grid}, h}) \quad [\text{kW}]$$
  $$\text{Contract Utilisation \%} = \frac{P_{\text{grid, peak}}}{C_{\text{grid}}} \times 100\%$$
- **Biomass Fuel Tracking**:
  $$M_{\text{consumed\_kg}} = \sum_{h=0}^{N-1} x_{\text{biomass}, h} \times \text{SFC} \quad [\text{kg}]$$
  $$M_{\text{remaining\_kg}} = \max(0.0, \; M_{\text{daily\_stock\_kg}} - M_{\text{consumed\_kg}}) \quad [\text{kg}]$$

---

## 4. Battery Energy Storage System (BESS) Support Status

The factory profile in `factory_config.py` specifies physical parameters for a 100 kWh / 50 kW battery system.  
In Phase 4, multi-period inter-temporal dynamic storage optimization (simultaneous state-of-charge tracking, C-rate limits, and degradation arbitrage) is explicitly deferred to Phase 5 in order to prioritize the stability, transparency, and numerical determinism of the core generation-dispatch linear program.

---

## 5. Infeasibility & Error Handling

The optimiser guarantees safe, non-crashing behavior under physical capacity deficits:
1. **Pre-check Capacity Bounds**: If an interval's demand exceeds the theoretical maximum possible generation from all assets + grid contract capacity:
   $$E_{\text{demand}, h} > \text{Solar Available}_h + \text{Wind Available}_h + C_{\text{biomass}} + C_{\text{grid}}$$
   The interval is flagged as `is_feasible = False`, and `unmet_demand_kwh` records the exact unserved energy.
2. **Solver Termination Check**: If the HiGHS solver reports an infeasible formulation (`res.status != 0`), the engine sets `is_feasible = False`, explains the exact solver message, reports zero fabricated allocations, and returns a structured response rather than raising an uncaught HTTP 500 error.

---

## 6. API Endpoints Reference

### 6.1. `GET /api/optimization/baseline`
Returns the 100% grid-only reference scenario under Time-of-Day tariffs.
```json
{
  "factory_id": "DEMO-FAC-001",
  "simulation_date": "2026-10-14",
  "total_factory_demand_kwh": 2684.26,
  "grid_contract_demand_kw": 250.0,
  "is_capacity_feasible": true,
  "peak_factory_demand_kw": 238.5,
  "total_baseline_cost_inr": 22458.95,
  "average_blended_rate_inr_per_kwh": 8.37,
  "hourly_baseline": [
    {
      "interval_index": 0,
      "timestamp": "2026-10-14T00:00:00+05:30",
      "demand_kwh": 28.52,
      "demand_kw": 28.52,
      "grid_tariff_inr_per_kwh": 6.5,
      "baseline_cost_inr": 185.38,
      "is_peak_tariff": false,
      "exceeds_grid_capacity": false
    }
  ],
  "simulation_metadata": { "is_synthetic": true, "simulation_seed": 42, "simulation_date": "2026-10-14" }
}
```

### 6.2. `GET /api/optimization/summary`
Returns high-level economic performance metrics.
```json
{
  "factory_id": "DEMO-FAC-001",
  "simulation_date": "2026-10-14",
  "is_feasible": true,
  "solver_status": "Optimization terminated successfully. (HiGHS Status 7: Optimal)",
  "total_demand_kwh": 2684.26,
  "total_demand_served_kwh": 2684.26,
  "unmet_demand_total_kwh": 0.0,
  "baseline_grid_only_cost_inr": 22458.95,
  "optimised_supply_cost_inr": 9635.86,
  "estimated_savings_inr": 12823.09,
  "estimated_savings_percentage": 57.1,
  "renewable_energy_allocated_kwh": 1477.96,
  "renewable_allocation_percentage": 55.06,
  "grid_energy_allocated_kwh": 1206.3,
  "grid_energy_share_percentage": 44.94,
  "peak_grid_power_kw": 188.5,
  "peak_grid_contract_utilisation_percent": 75.4,
  "biomass_energy_consumed_kwh": 312.5,
  "biomass_fuel_consumed_kg": 250.0,
  "biomass_remaining_fuel_budget_kg": 0.0,
  "infeasible_intervals_count": 0,
  "production_fulfilment_units": 3614.8,
  "simulation_metadata": { "is_synthetic": true, "simulation_seed": 42, "simulation_date": "2026-10-14" }
}
```

### 6.3. `GET /api/optimization/run`
Returns the complete hourly allocation schedule (`intervals: List[IntervalSourceAllocation]`) and per-source availability/utilization statistics (`source_breakdown: List[SourceUtilizationSummary]`).
