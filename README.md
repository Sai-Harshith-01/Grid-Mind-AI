# GridMind AI

> **Intelligent Energy Optimisation for MSME Factories**  
> AI-powered renewable intelligence orchestrating Solar, Wind, Biomass, and Grid Electricity tariffs.

---

## 1. Project Overview

GridMind AI is an industrial energy intelligence platform designed to help Micro, Small, and Medium Enterprises (MSMEs) cut electricity bills and optimize self-consumption of renewable assets.

The core platform features (built incrementally across phases) are:
1. **Factory Energy Dashboard** — High-resolution monitoring of zone-level consumption, production throughput, and renewable availability.
2. **Energy Analysis & Anomaly Detection (Phase 3)** — Explainable rule-based anomaly detector, Time-of-Day (ToD) tariff cost baselining, and zone/shift energy intensity analytics.
3. **Renewable Energy Optimisation Simulator (Phase 4)** — Deterministic linear programming economic dispatch solver (HiGHS solver via SciPy) for optimal renewable allocation and ToD tariff arbitrage.
4. **Gemini AI Energy Waste Investigator (Phase 5)** — Generative contextual root-cause audits and plant manager advisory reports.
5. **Cloud Deployment (Phase 6)** — Containerized Google Cloud Run backend and Firebase Hosting frontend.

---

## 2. Phase 4: Renewable Energy Optimisation Engine

### 2.1. Mathematical Formulation
The dispatch problem is formulated as a linear program (LP) solved by **HiGHS** through `scipy.optimize.linprog(method='highs')`:

$$\min_{x} \sum_{h=0}^{23} \left( c_{\text{solar}} x_{\text{solar}, h} + c_{\text{wind}} x_{\text{wind}, h} + c_{\text{biomass}} x_{\text{biomass}, h} + c_{\text{grid}, h} x_{\text{grid}, h} \right)$$

Subject to:
1. **Energy Balance**: $x_{\text{solar}, h} + x_{\text{wind}, h} + x_{\text{biomass}, h} + x_{\text{grid}, h} = E_{\text{demand}, h}$
2. **Solar Upper Bound**: $0 \le x_{\text{solar}, h} \le \min(E_{\text{solar\_avail}, h}, 100.0\text{ kW} \times 1\text{ h})$
3. **Wind Upper Bound**: $0 \le x_{\text{wind}, h} \le \min(E_{\text{wind\_avail}, h}, 60.0\text{ kW} \times 1\text{ h})$
4. **Biomass Power Limit**: $0 \le x_{\text{biomass}, h} \le 50.0\text{ kW} \times 1\text{ h} = 50.0\text{ kWh}$
5. **Biomass Fuel Energy Budget**: $\sum_{h=0}^{23} x_{\text{biomass}, h} \le \frac{250.0\text{ kg}}{0.80\text{ kg/kWh}} = 312.5\text{ kWh}$
6. **Grid Contract Demand Limit**: $0 \le x_{\text{grid}, h} \le 250.0\text{ kW} \times 1\text{ h} = 250.0\text{ kWh}$
7. **Nonnegativity**: all $x \ge 0$.

### 2.2. Merit-Order Dispatch Hierarchy
- **Solar PV & Wind ($c = ₹0.00$)**: Dispatched up to available meteorological generation.
- **Biomass Gasifier ($c = ₹4.20$)**: Dispatched to displace grid power during normal (₹8.20) and peak (₹11.80) tariff windows, respecting the 50 kW generator limit and 312.5 kWh daily fuel stock.
- **Grid Electricity ($c = ₹6.50 – ₹11.80$)**: Imported only for the remaining balance.

### 2.3. Key Results on the Simulated Factory
- **Baseline 100% Grid Cost**: ₹22,458.95 (₹8.37/kWh blended rate)
- **Optimised Multi-Source Supply Cost**: ₹9,635.86
- **Estimated Scenario Savings**: **₹12,823.09 / day (57.1% reduction)**
- **Renewable Allocation Share**: **55.06%** of total demand served by renewables (1,477.96 kWh allocated).
- **Peak Grid Import**: Reduced from 238.5 kW down to 188.5 kW (75.4% contract utilisation).
- **Biomass Consumption**: 312.5 kWh electricity generated, fully consuming the 250 kg daily fuel stock.

### 2.4. Synthetic Assumptions Disclaimer
> **Fictional demonstration factories using synthetic data. Not actual customer facilities.**  
> All factory profiles (`DEMO-FAC-001`, `DEMO-FAC-002`, `DEMO-FAC-003`), equipment ratings, power curves, tariff rates, and anomaly events are **synthetic illustrative parameters** developed for algorithmic optimization and dashboard prototyping. None represent real customers, measured installations, or guaranteed commercial outcomes.

---

## 3. Repository Structure

```text
Grid-Mind/
├── .gitignore                   # Root git ignore (node_modules, venvs, cache, env files)
├── README.md                    # Project documentation and quickstart guide
├── docs/
│   ├── architecture.md          # Detailed system architecture specification
│   ├── data-model.md            # Phase 2 synthetic factory data model schemas
│   ├── energy-analysis.md       # Phase 3 analytical formulas, baselines, and detection rules
│   └── energy-optimization.md   # Phase 4 linear programming model, constraints, and solver docs
├── backend/
│   ├── .env.example             # Backend environment template
│   ├── .gitignore               # Python specific ignore rules
│   ├── pyproject.toml           # Python packaging configuration (SciPy, NumPy included)
│   ├── requirements.txt         # Dependencies (FastAPI, Uvicorn, Pydantic, SciPy, NumPy, pytest, httpx)
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI application entrypoint, CORS, route registration
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   └── config.py        # Centralized settings and CORS origins
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   └── routes/
│   │   │       ├── __init__.py
│   │   │       ├── health.py        # GET /health endpoint
│   │   │       ├── root.py          # GET / metadata endpoint
│   │   │       ├── factory.py       # GET /api/factory/* endpoints
│   │   │       ├── analysis.py      # GET /api/analysis/* endpoints
│   │   │       └── optimization.py  # GET /api/optimization/* endpoints
│   │   ├── data/
│   │   │   ├── __init__.py
│   │   │   ├── factory_config.py    # Factory parameters and equipment profiles
│   │   │   └── factory_simulator.py # Deterministic 24h simulation engine
│   │   ├── schemas/
│   │   │   ├── __init__.py          # Exported response models
│   │   │   ├── health.py            # Health schemas
│   │   │   ├── factory.py           # Factory data schemas
│   │   │   ├── analysis.py          # Metrics, anomalies, and analytical profile schemas
│   │   │   └── optimization.py      # LP dispatch allocation and baseline schemas
│   │   └── services/
│   │       ├── __init__.py
│   │       ├── factory_data_service.py # Singleton factory dataset caching service
│   │       ├── energy_metrics.py       # Phase 3 energy metrics & cost baseline service
│   │       ├── anomaly_detector.py     # Phase 3 rule-based anomaly detection service
│   │       ├── energy_optimizer.py     # Phase 4 linear programming dispatch service
│   │       └── gemini_service.py       # Phase 5 Gemini AI Energy Waste Investigator service
│   │   └── prompts/
│   │       ├── __init__.py
│   │       └── energy_investigation.py # Grounding system instructions & prompt builders
│   └── tests/
│       ├── __init__.py
│       ├── test_health.py              # Phase 1 health check tests
│       ├── test_factory_simulator.py   # Phase 2 simulation tests
│       ├── test_energy_analysis.py     # Phase 3 metrics and anomaly detection tests
│       ├── test_energy_optimizer.py    # Phase 4 LP dispatch and numerical integrity tests
│       ├── test_gemini_investigation.py # Phase 5 Gemini AI grounding & resilience tests
│       └── test_multi_factory.py       # Multi-factory engine, isolation & backward compatibility tests (110 tests total)
└── frontend/
    ├── .env.example             # Frontend environment template
    ├── .gitignore               # Frontend specific ignore rules
    ├── index.html               # HTML template
    ├── package.json             # React 18, Vite, TypeScript, Tailwind CSS
    ├── tsconfig.json            # TypeScript bundler configuration
    ├── vite.config.ts           # Vite server configuration
    └── src/
        ├── App.tsx              # Landing application
        ├── api/                 # Typed API utilities
        └── components/          # UI components
```

---

## 4. Phase 5: Gemini AI Energy Waste Investigator

### 4.1. Grounded Anomaly Investigation Pipeline
GridMind AI connects deterministic Python heuristics to Google's official `google-genai` SDK using strict evidence boundaries:

1. **Grounded Context Assembly**: Reads interval telemetry, observed power (kW), baseline thresholds, deviation percentages, ToD utility tariffs, and Phase 4 LP multi-source cost comparisons.
2. **Authoritative Backend Economics**: All financial figures (excess energy grid equivalent, baseline cost, optimized scenario cost, estimated daily savings) are computed strictly by the backend. The LLM is never allowed to hallucinate numerical totals.
3. **Hypothesis Boundary Enforcement**: Physical causes generated by Gemini (e.g. pneumatic leaks, solenoid failures, operator oversight) are strictly treated as unconfirmed hypotheses (`is_confirmed = False`).
4. **Industrial Safety Enforcement**: Recommendations enforce equipment ratings, PPE, and lockout/tagout (LOTO) protocols; bypassing safety interlocks is strictly prohibited.
5. **Schema Validation & Bounded Correction**: Model responses are validated against Pydantic schemas. If malformed, a single bounded correction retry is executed before raising a typed error.
6. **Graceful Degradation**: If `GEMINI_API_KEY` is omitted, the backend starts up cleanly and returns HTTP `503 Service Unavailable` with setup instructions upon request.

---

## 5. Getting Started (Windows PowerShell)

Run backend and frontend in **two separate PowerShell terminals**.

### Terminal 1: Backend Setup & Run

1. Navigate to the backend directory:
   ```powershell
   cd e:\Grid-Mind\backend
   ```

2. Create and activate a Python virtual environment:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. Install locked dependencies (including SciPy, NumPy, and Google GenAI):
   ```powershell
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. Configure `.env`:
   ```powershell
   Copy-Item .env.example .env -Force
   # Set your GEMINI_API_KEY inside backend/.env
   ```

5. Start the FastAPI backend server:
   ```powershell
   uvicorn app.main:app --reload --port 8000
   ```

### Terminal 2: Frontend Setup & Run

1. Navigate to the frontend directory:
   ```powershell
   cd e:\Grid-Mind\frontend
   ```

2. Install dependencies:
   ```powershell
   npm install
   ```

3. Start the Vite dev server:
   ```powershell
   npm run dev
   ```
   Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## 6. API Endpoints

Once the backend is running at `http://localhost:8000`:

| Method | Endpoint | Phase | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/health` | Phase 1 | Service operational health and UTC timestamp |
| `GET` | `/` | Phase 1 | Platform metadata, overview, and interactive docs URL |
| `GET` | `/api/factory/profile` | Phase 2 | Virtual factory profile, equipment ratings, zones, and schedule |
| `GET` | `/api/factory/timeseries` | Phase 2 | Deterministic 24-hour hourly energy & production intervals |
| `GET` | `/api/factory/anomaly-scenarios` | Phase 2 | Predefined reproducible anomaly scenarios with diagnostic metadata |
| `GET` | `/api/factory/overview` | Phase 2 | Summary aggregations, peak demand interval, and renewable totals |
| `GET` | `/api/analysis/metrics` | Phase 3 | Comprehensive demand metrics, zone/shift breakdowns, renewable availability, and ToD grid cost baseline |
| `GET` | `/api/analysis/anomalies` | Phase 3 | List detected anomaly findings with optional filters (`severity`, `category`, `zone_id`) |
| `GET` | `/api/analysis/anomalies/{id}` | Phase 3 | Single anomaly detail, baseline deviation, diagnostic evidence, and financial impact |
| `GET` | `/api/analysis/energy-profile` | Phase 3 | 24-hour analytical profile with hourly costs and renewable yields |
| `GET` | `/api/optimization/baseline` | Phase 4 | Reference 100% grid-only cost scenario, hourly demand, tariffs, and capacity feasibility |
| `GET` | `/api/optimization/run` | Phase 4 | Full linear programming dispatch solution with hourly source allocations and cost comparisons |
| `GET` | `/api/optimization/summary` | Phase 4 | Executive dashboard summary: estimated savings, renewable allocation %, peak grid power, fuel budget |
| `GET` | `/api/investigation/status` | Phase 5 | Service readiness, configured Gemini model, and supported modes (no secrets exposed) |
| `POST` | `/api/investigation/anomaly/{id}` | Phase 5 | Grounded Gemini AI investigation of specific anomaly finding |
| `POST` | `/api/investigation/report` | Phase 5 | Bounded batch diagnostic report and plant-wide risk synthesis |
| `GET` | `/docs` | — | Interactive Swagger OpenAPI documentation |

### Example PowerShell Requests:
```powershell
# Check Gemini AI Service Status
Invoke-RestMethod -Uri http://localhost:8000/api/investigation/status

# Investigate a Specific Anomaly (e.g. FINDING-IDLE-WASTE-H03)
Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/investigation/anomaly/FINDING-IDLE-WASTE-H03

# Generate Bounded Batch Diagnostic Report
Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/investigation/report -Body '{"max_findings": 3, "min_severity": "high"}' -ContentType 'application/json'
```

---

## 7. Running Automated Tests

To execute the complete automated test suite:

```powershell
cd e:\Grid-Mind\backend
.\.venv\Scripts\Activate.ps1
pytest tests/ -v
```

All 110 automated tests pass across:
- **Multi-Factory Engine**: 3 isolated fictional profiles (`DEMO-FAC-001`, `DEMO-FAC-002`, `DEMO-FAC-003`), factory switching, and backward-compatible legacy ID resolution.
- **Phase 1**: Health, app metadata, and CORS preflight.
- **Phase 2**: Deterministic synthetic factory generation, renewable profiles, and injected anomaly scenarios.
- **Phase 3**: Energy metrics, ToD baselining, and rule-based anomaly detection.
- **Phase 4**: SciPy HiGHS linear programming dispatch, numerical integrity, hand-calculated arithmetic verification, and ToD arbitrage.
- **Phase 5**: Gemini AI grounding, hypothesis boundary enforcement, prompt safety, rate limits, timeouts, bounded 1-retry schema validation, and partial report failure handling.

---

## 8. Next Phases Roadmap

- [x] **Phase 1**: Project Foundation (FastAPI, React + Vite + Tailwind, health endpoints, CORS).
- [x] **Phase 2**: Deterministic Synthetic Factory Telemetry Engine (24h load curves, weather generation, ToD tariffs).
- [x] **Phase 3**: Energy Analysis & Anomaly Detection (metrics, intensity, ToD baseline, explainable rule detector).
- [x] **Phase 4**: Renewable Energy Allocation & Optimisation Engine (SciPy HiGHS LP solver, merit-order dispatch).
- [x] **Phase 5**: Google Gemini AI Energy Waste Investigator (grounded root-cause diagnosis, safety enforcement).
- [x] **Phase 6**: Frontend Energy Intelligence Dashboard (interactive operations UI, charts, Gemini audit, LP simulator).
- [ ] **Phase 7**: Cloud Deployment (Google Cloud Run containerization and Firebase Hosting CI/CD pipeline).
