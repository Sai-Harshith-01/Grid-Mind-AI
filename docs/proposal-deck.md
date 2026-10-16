# GridMind AI — Intelligent Energy & Electricity Optimisation Platform
## AI Builder Cup Proposal Deck

---

### Slide 1: Title & Executive Summary
- **Product Name**: GridMind AI
- **Tagline**: The AI-Powered Electricity Intelligence & Renewable Optimisation Platform for MSMEs
- **Vision**: Democratizing industrial energy engineering for over 60 million micro, small, and medium manufacturing enterprises across India.
- **Core Technology Stack**:
  - Frontend: React 18, TypeScript, Tailwind CSS, Recharts, Vite
  - Backend: Python 3.11/3.13, FastAPI, Pydantic v2
  - Optimisation Engine: SciPy Linear Programming with the HiGHS Interior Point & Simplex Solvers
  - Generative AI Intelligence: Google Gemini 2.0 via Google GenAI SDK
  - Cloud Infrastructure: Google Cloud Run & Firebase Hosting

---

### Slide 2: The MSME Energy Problem
- **Massive Operating Expense**: Electricity is routinely the 2nd highest operational expense in manufacturing MSMEs, representing 15% to 35% of total production cost.
- **Punitive Time-of-Day (ToD) Tariffs**: Power distribution companies (e.g. Regional Utility, Regional Utility) charge up to 50% surcharges during peak hours (e.g. ₹11.80–₹12.20/kWh vs. ₹6.20/kWh off-peak).
- **Hidden Energy Waste**:
  - Auxiliary machines, chillers, and compressors left idling during shift handovers.
  - Uncoordinated simultaneous startup of heavy inductive loads causing peak contract demand penalties.
- **Suboptimal Clean Energy Usage**: MSMEs invest in rooftop solar, biomass gasifiers, or wind, but lack automated systems to dynamically orchestrate them against multi-tier grid tariffs and production schedules.

---

### Slide 3: The Solution — GridMind AI
GridMind AI introduces an intelligent, constraint-aware energy orchestration layer:
1. **Detect**: Deterministic industrial heuristics monitor equipment baseloads, consumption spikes, and contract demand headroom in real-time.
2. **Investigate with Gemini**: Google Gemini acts as an autonomous industrial energy engineer, diagnosing root causes without hallucinating math or physical facts.
3. **Optimise with HiGHS**: SciPy's HiGHS linear programming solver determines the cost-optimal hourly dispatch matrix across Solar, Wind, Biomass, and Grid power.
4. **Measure Impact**: Transparently calculates baseline grid-only cost versus optimised supply cost, surfacing verifiable rupee savings and clean energy percentages.

---

### Slide 4: System Architecture & Separation of Concerns

```
┌─────────────────────────────────────────────────────────────┐
│                 React + Tailwind Dashboard                  │
│       (Factory Switcher, Telemetry, KPIs, Recharts)         │
└──────────────────────────────┬──────────────────────────────┘
                               │ JSON REST API
┌──────────────────────────────▼──────────────────────────────┐
│                    FastAPI Backend Core                     │
├──────────────────────────────┬──────────────────────────────┤
│  Deterministic Physics Core  │   Grounded Generative AI     │
│  - 24h Time Series Simulator │   - Google GenAI SDK         │
│  - Rule-Based Anomaly Engine │   - Strict System Prompts    │
│  - SciPy HiGHS LP Solver     │   - Unconfirmed Hypothesis   │
│  - Tariff & Headroom Math    │     Boundaries               │
└──────────────────────────────┴──────────────────────────────┘
```

**Key Architectural Principle**:
The Large Language Model *never* calculates rupee balances, consumption totals, or dispatch limits. All numbers are authoritatively computed by the deterministic backend and injected into Gemini's prompt context as verified evidence.

---

### Slide 5: Three Fictional MSME Demo Scenarios

| Factory Profile | Location & Industry | Connected Load & Contract Demand | Energy Assets | Demo Scenario |
| :--- | :--- | :--- | :--- | :--- |
| **PrecisionWorks Factory** | Demonstration Zone 1<br>Auto CNC Machining | 260 kW Load<br>250 kW Grid Contract | 100 kWp Solar<br>60 kW Wind<br>50 kW Biomass | Off-shift compressor idling waste (03:00 AM) & peak demand surge (19:00 PM). |
| **FreshField Factory** | Demonstration Zone 2<br>Cold Storage & Processing | 210 kW Load<br>200 kW Grid Contract | 75 kWp Solar<br>20 kW Wind<br>35 kW Agro-Biomass | Continuous refrigeration demand during evening peak tariff (₹12.20/kWh). |
| **WeaveWise Factory** | Demonstration Zone 3<br>Spinning & Weaving | 280 kW Load<br>270 kW Grid Contract | 120 kWp Solar<br>50 kW Wind<br>45 kW Pellet Biomass | High midday solar self-consumption and wind/biomass arbitration against Regional Utility tariffs. |

---

### Slide 6: Mathematical Optimisation Formulation
**Objective Function**:
$$\min \sum_{t=0}^{23} \left( c_{\text{solar}} \cdot x_{\text{solar},t} + c_{\text{wind}} \cdot x_{\text{wind},t} + c_{\text{biomass}} \cdot x_{\text{biomass},t} + \text{Tariff}_t \cdot x_{\text{grid},t} \right)$$

**Subject to**:
1. **Demand Balance**: $x_{\text{solar},t} + x_{\text{wind},t} + x_{\text{biomass},t} + x_{\text{grid},t} = \text{Demand}_t \quad \forall t$
2. **Solar Resource Bound**: $0 \le x_{\text{solar},t} \le \min(\text{SolarAvailable}_t, \text{SolarCapacity})$
3. **Wind Resource Bound**: $0 \le x_{\text{wind},t} \le \min(\text{WindAvailable}_t, \text{WindCapacity})$
4. **Biomass Power Limit**: $0 \le x_{\text{biomass},t} \le \text{BiomassCapacity}$
5. **Biomass Fuel Inventory**: $\sum_{t=0}^{23} x_{\text{biomass},t} \le \frac{\text{FuelAvailableKg}}{\text{SFC}}$
6. **Grid Contract Headroom**: $0 \le x_{\text{grid},t} \le \text{ContractDemand}$
7. **Nonnegativity**: All decision variables $\ge 0$.

---

### Slide 7: Expected Impact & ROI
- **Procurement Cost Reduction**: 20% to 45% reduction in daily electricity costs via automated ToD tariff arbitrage and clean energy dispatch.
- **Peak Penalty Prevention**: Ensures grid imports never breach sanctioned contract demand limits, eliminating demand violation surcharges.
- **Payback Period**: 0 capital expenditure on software: cloud-delivered SaaS model with estimated 3–6 month payback from operational savings alone.
- **Decarbonization**: Maximizes on-site renewable yield, reducing MSME grid carbon intensity by an estimated 35–50%.

---

### Slide 8: Limitations, Assumptions & Future Roadmap
- **Synthetic Data Disclaimer**: All factory readings, equipment profiles, and savings figures are simulated scenario evaluations for prototyping and demonstration.
- **Zero Marginal Cost Assumption**: Solar and wind are assumed to have zero marginal fuel cost; capital amortization is excluded from daily dispatch.
- **Future Roadmap**:
  - Integration with industrial Modbus/MQTT IoT gateways for live edge telemetry.
  - Multi-day battery energy storage system (BESS) state-of-charge degradation modelling.
  - Automated demand response bidding into Indian energy exchanges (IEX).
