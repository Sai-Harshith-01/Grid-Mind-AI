GridMind AI

AI-Powered Energy Intelligence and Optimisation for MSME Manufacturing

Turning industrial energy data into actionable insights through AI-assisted investigation and mathematical optimisation.

GridMind AI is an energy intelligence prototype designed to help micro, small, and medium-sized manufacturing enterprises (MSMEs) understand electricity consumption, identify unusual energy usage, and evaluate cost-effective energy allocation strategies.

The platform combines Google Gemini for AI-assisted energy investigation with SciPy and the HiGHS optimisation solver to analyse consumption patterns, evaluate renewable energy utilisation, and compare baseline electricity costs with mathematically optimised scenarios.

By bringing energy analytics, anomaly detection, generative AI, and constrained optimisation into a unified interface, GridMind AI explores a practical approach to more efficient and sustainable industrial energy management.

«Project status: Prototype.

Data transparency: Factory identities and demonstration datasets are fictional and synthetic. Savings and energy allocation results are modelled estimates, not verified real-world outcomes.»

---

Table of Contents

- "Problem Statement" (#problem-statement)
- "Solution Overview" (#solution-overview)
- "Key Features" (#key-features)
- "System Workflow" (#system-workflow)
- "System Architecture" (#system-architecture)
- "Technology Stack" (#technology-stack)
- "Energy Optimisation Model" (#energy-optimisation-model)
- "Demonstration Factories" (#demonstration-factories)
- "Project Structure" (#project-structure)
- "Getting Started" (#getting-started)
- "Testing and Validation" (#testing-and-validation)
- "Security and Privacy" (#security-and-privacy)
- "Sustainability Impact" (#sustainability-impact)
- "Limitations" (#limitations)
- "Future Enhancements" (#future-enhancements)
- "Team" (#team)
- "License" (#license)

---

Problem Statement

Manufacturing facilities consume electricity across machinery, production lines, refrigeration, lighting, ventilation, and other industrial operations.

Smaller manufacturers may face challenges such as:

- Limited visibility into energy consumption patterns.
- Difficulty identifying unusual electricity usage.
- Increasing electricity costs during peak-demand periods.
- Limited tools for evaluating renewable energy utilisation.
- Difficulty comparing alternative energy allocation strategies.

Without accessible energy analytics, identifying potential inefficiencies and evaluating cost-saving opportunities can be challenging.

Proposed Solution

GridMind AI provides an integrated decision-support platform that:

1. Analyses factory energy consumption profiles.
2. Detects unusual usage patterns using configurable rules.
3. Uses generative AI to investigate potential causes.
4. Optimises energy allocation under configured constraints.
5. Compares baseline and optimised electricity costs.
6. Presents findings and modelled savings through a unified dashboard.

Objective: Explore how AI-assisted investigation and mathematical optimisation can help MSMEs make more informed energy management decisions.

---

Key Features

1. Energy Intelligence Dashboard

- Visualise factory-level electricity consumption and energy profiles.
- Review energy indicators and detected anomalies.
- Explore renewable energy availability and configured tariffs.
- Compare baseline and optimised energy scenarios.
- Present cost analysis and optimisation results in a unified interface.

2. Electricity Anomaly Detection

Identifies potentially unusual energy consumption using configured detection rules and baselines.

Capabilities include:

- Consumption baseline comparison.
- Identification of deviations from expected patterns.
- Highlighting of unusual operating periods.
- Generation of findings for further investigation.

An anomaly is an indicator for investigation, not independent proof of energy waste or equipment failure.

3. Gemini AI Energy Investigator

Integrates Google Gemini to interpret energy-related findings and generate contextual explanations.

The investigator can:

- Analyse available energy evidence.
- Suggest possible causes of unusual consumption.
- Recommend practical verification steps.
- Identify potential energy-efficiency opportunities.
- Translate analytical findings into understandable explanations.

AI-generated findings are advisory. They are not treated as verified measurements or as substitutes for numerical optimisation.

4. Constrained Energy Optimisation

Uses SciPy and the HiGHS solver to calculate an energy allocation that minimises modelled electricity costs.

The optimisation model can represent:

- Electricity demand requirements.
- Configured energy source costs.
- Renewable generation availability.
- Source capacity and grid supply limits.
- Time-dependent electricity tariffs.
- Other constraints implemented in the model.

The solver calculates a numerical solution to the configured mathematical problem; the quality of that solution depends on the accuracy and completeness of the model.

5. Energy Cost Analysis

- Compare baseline and optimised electricity costs.
- Calculate modelled daily cost differences.
- Estimate savings percentages.
- Generate annualised projections using configured operating days.
- Evaluate illustrative time-of-use tariff scenarios.

All savings calculations are conditional on the configured assumptions and constraints.

6. Multiple Factory Profiles

Includes three fictional industrial scenarios to demonstrate how different manufacturing energy profiles can be analysed using the same workflow.

---

System Workflow

GridMind AI follows a structured workflow from energy data to decision-support insights.

1. Factory Selection: Select a fictional manufacturing profile.
2. Energy Data Loading: Load the associated synthetic demand and energy source assumptions.
3. Energy Analysis: Evaluate consumption patterns and configured baselines.
4. Anomaly Detection: Flag unusual usage using predefined rules.
5. AI Investigation: Use Gemini to interpret the available findings and propose potential explanations.
6. Energy Optimisation: Formulate and solve the configured constrained optimisation problem using SciPy and HiGHS.
7. Cost Comparison: Calculate baseline and optimised costs from the model inputs.
8. Insight Presentation: Display analytical findings, AI-generated explanations, and numerical results through the dashboard.

The AI investigation and mathematical optimisation are separate processes: Gemini provides contextual interpretation, while the optimisation solver calculates the energy allocation.

---

System Architecture

The architecture separates the user interface, backend orchestration, analytical processing, AI investigation, optimisation, and cost calculations.

flowchart TD
    A["Synthetic Factory Energy Data"]
    B["React + TypeScript Frontend"]
    C["FastAPI Backend"]

    D["Energy Analytics"]
    E["Rule-Based Anomaly Detection"]
    F["Gemini AI Energy Investigator"]
    G["Constrained Optimisation Model"]
    H["SciPy + HiGHS Solver"]
    I["Energy Allocation Results"]
    J["Cost and Savings Calculations"]
    K["Dashboard Insights"]

    A --> C
    B <--> C
    C --> D
    D --> E
    E --> F
    D --> G
    G --> H
    H --> I
    I --> J
    F --> K
    J --> K
    K --> B

Architecture Components

Component| Responsibility
Frontend| Factory selection, dashboard visualisation, and presentation of results
FastAPI backend| API handling and coordination of analysis workflows
Energy analytics| Processing of consumption profiles and energy-related indicators
Anomaly detection| Identification of deviations using configured rules
Gemini AI investigator| Contextual explanations and potential corrective actions
Optimisation engine| Mathematical formulation and solver execution
HiGHS solver| Numerical solution of supported optimisation problems
Cost analysis| Calculation of modelled costs, differences, and savings
Dashboard insights| Presentation of AI explanations and numerical results

Core design principle: AI explains the evidence; mathematical optimisation calculates the solution.

---

Technology Stack

Technology| Purpose
React| Frontend interface
TypeScript| Frontend application logic and type safety
Vite| Frontend development and build tooling
Tailwind CSS| Interface styling
Python| Backend processing and analytical logic
FastAPI| Backend API framework
Uvicorn| ASGI application server
Google Gemini| AI-assisted energy investigation
"google-genai"| Google GenAI SDK
SciPy| Scientific computing and optimisation interface
HiGHS| Linear and mixed-integer optimisation solver, depending on the formulation

The table describes the intended technical stack; implementation details should be consistent with the actual repository dependencies.

---

Energy Optimisation Model

GridMind AI formulates energy allocation as a constrained cost-minimisation problem.

A simplified objective function is:

[
\min \sum_{t=1}^{T}\sum_{s\in S} c_{s,t}x_{s,t}
]

Where:

- (T) is the number of modelled time intervals.
- (S) is the set of available energy sources.
- (c_{s,t}) is the configured unit cost of source (s) during interval (t).
- (x_{s,t}) is the energy allocated from source (s) during interval (t).

Example Constraints

Demand-supply balance

[
\sum_{s\in S}x_{s,t}=D_t
]

Here, (D_t) represents electricity demand during interval (t). This equality is appropriate when the model requires all demand to be met exactly by the included sources.

Source capacity

[
0\leq x_{s,t}\leq U_{s,t}
]

Here, (U_{s,t}) is the maximum available supply from source (s) during interval (t).

Additional constraints may represent grid import limits, renewable availability, and other operating requirements supported by the implementation.

Modelled Energy Sources

- Solar: Supply constrained by the configured solar generation profile.
- Wind: Supply constrained by the configured wind generation profile.
- Biomass: Supply and fuel costs represented according to configured assumptions.
- Grid electricity: Supply priced using the configured electricity tariff.

The optimiser can only evaluate the sources, constraints, and cost components explicitly represented in its model. Renewable infrastructure costs, storage losses, maintenance, and capital expenditure should not be assumed to be included unless implemented.

Illustrative Time-of-Use Tariffs

Period| Example time window| Illustrative rate
Off-peak| 10 PM–6 AM| ₹6.50/kWh
Normal| 6 AM–6 PM| ₹8.20/kWh
Peak| 6 PM–10 PM| ₹11.80/kWh

These rates are illustrative values for demonstration purposes, not verified tariffs from a particular electricity provider. The values used in the README should match the application's actual configuration.

Cost and Savings Calculations

Modelled daily savings

[
S_{\mathrm{daily}}=C_{\mathrm{baseline}}-C_{\mathrm{optimised}}
]

Modelled savings percentage

[
S_{%}=
\frac{C_{\mathrm{baseline}}-C_{\mathrm{optimised}}}
{C_{\mathrm{baseline}}}\times100
]

Annualised savings estimate

[
S_{\mathrm{annual}}=S_{\mathrm{daily}}\times D
]

Where:

- (C_{\mathrm{baseline}}) is the baseline modelled electricity cost.
- (C_{\mathrm{optimised}}) is the optimised modelled electricity cost.
- (D) is the assumed number of operating days per year.

The savings percentage is undefined when the baseline cost is zero. The application should handle this case explicitly.

These calculations estimate potential cost differences under the model's assumptions. They do not guarantee that equivalent savings will occur in a real factory.

---

Demonstration Factories

GridMind AI includes three fictional manufacturing profiles.

Factory| Demonstration ID| Scenario
PrecisionWorks Factory| "DEMO-FAC-001"| Precision engineering, CNC machining, and off-shift consumption
FreshField Factory| "DEMO-FAC-002"| Food processing, cold storage, and peak demand
WeaveWise Factory| "DEMO-FAC-003"| Textile spinning, weaving, and shift-based energy consumption

Data disclosure: All factory identities and demonstration data are fictional. The profiles do not represent actual companies, customers, or measured industrial energy consumption.

---

Project Structure

The following is an illustrative high-level structure. Actual paths and filenames should match the repository.

Grid-Mind-AI/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── ...
│   ├── tests/
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   ├── package.json
│   └── ...
└── README.md

- "backend/" contains the API and server-side processing.
- "frontend/" contains the user interface and dashboard.
- "tests/" contains backend validation tests, if configured.
- ".env.example" documents required environment variable names without exposing secrets.

---

Getting Started

Prerequisites

- Python version compatible with the backend dependencies.
- Node.js and npm compatible with the frontend.
- Git.
- A Google Gemini API key for AI investigation functionality.

1. Clone the Repository

git clone https://github.com/Sai-Harshith-01/Grid-Mind-AI.git
cd Grid-Mind-AI

2. Set Up the Backend

cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt

If the repository includes ".env.example", create a local environment file:

Copy-Item .env.example .env

Configure the environment variables required by the application. Store the Gemini API key on the backend and never expose it through frontend code.

If the application entry point is "app.main", run:

uvicorn app.main:app --reload --port 8000

The entry point and required environment variables should be verified against the repository.

3. Set Up the Frontend

Open a second terminal:

cd frontend
npm install
npm run dev

Open the local development URL displayed by Vite. Configure the frontend API base URL using the environment variable names defined by the project.

4. Access API Documentation

If the application uses FastAPI's default documentation settings, open:

- Swagger UI: "http://localhost:8000/docs"
- OpenAPI schema: "http://localhost:8000/openapi.json"

These endpoints depend on the backend being available and documentation not being disabled or customised.

---

Testing and Validation

Testing should cover the analytical workflow, optimisation behaviour, API responses, and user interface.

Backend Tests

If pytest is configured and the repository contains the relevant test directory:

python -m pytest tests/ -v

Run this command from the backend directory.

Frontend Production Build Check

npm run build

Run this command from the frontend directory.

Recommended Validation Areas

- Anomaly detection against known synthetic test cases.
- Demand-supply balance and energy source capacity constraints.
- Optimisation solver status and infeasible scenarios.
- Baseline and optimised cost calculations.
- Zero-baseline savings percentage handling.
- Gemini API errors and unavailable responses.
- API input validation and error handling.
- Frontend presentation of missing or invalid results.

Test counts, build status, and successful execution should only be reported after they have been verified.

---

Security and Privacy

GridMind AI follows basic security practices for AI-enabled applications.

- Keep API keys and credentials on the backend.
- Exclude ".env" files and secrets from version control.
- Validate incoming API requests.
- Avoid logging credentials or other sensitive information.
- Restrict cross-origin requests to approved origins where applicable.
- Handle external AI service errors safely.
- Review authentication, authorisation, and rate limiting before any production use.

The demonstration uses synthetic factory data. Integrating actual industrial meter data would require additional security controls, access management, and appropriate data governance.

---

Sustainability Impact

GridMind AI explores the potential of energy analytics and constrained optimisation to support more efficient industrial operations.

Energy waste investigation: Anomaly detection can identify consumption patterns that warrant operational review.

Cost visibility: Tariff-aware comparisons can help users understand how different energy allocation scenarios affect modelled costs.

Renewable energy utilisation: The optimiser can evaluate available renewable generation within its configured constraints.

Accessible energy intelligence: A unified dashboard can make analytical findings easier for smaller manufacturers to explore.

Evidence-based decisions: Scenario comparisons can help identify potential improvements for subsequent engineering assessment.

These are intended benefits. Actual energy savings, financial outcomes, and emissions reductions require validation using real operational data and appropriate measurement methods.

---

Limitations

GridMind AI is a prototype and has important limitations:

- Factory profiles and demonstration datasets are synthetic.
- Illustrative tariffs may not match actual electricity tariffs.
- Optimisation outcomes depend on the mathematical formulation, inputs, and constraints.
- Capital expenditure, maintenance, storage losses, and other costs may be excluded.
- AI-generated explanations may be incomplete or incorrect.
- Anomaly detection identifies patterns, not confirmed equipment faults.
- Modelled savings are estimates rather than guaranteed outcomes.
- Real-world industrial performance has not been established by the demonstration data.

GridMind AI is intended for decision support. It is not a certified energy audit, a guarantee of cost reduction, or an autonomous industrial control system.

---

Future Enhancements

Potential areas for future development include:

- Integration with authorised industrial electricity meter data.
- Calibration against verified utility tariffs and production schedules.
- More detailed equipment and operating constraints.
- Historical energy trend analysis.
- Evaluation of anomaly detection accuracy.
- Validation of optimisation quality across different operating scenarios.
- Pilot studies with participating MSME manufacturers.
- Measurement of actual energy, cost, and environmental outcomes.

These items represent potential enhancements rather than claims of existing functionality.

---

Team

Team Name: Techies
Team Leader: Sai Harshith
Project: GridMind AI

Focus Areas: Sustainable energy, industrial efficiency, AI-assisted investigation, and mathematical optimisation.

---

License

No open-source license is currently specified. Unless a license is added to the repository, permissions to use, modify, or redistribute this project should not be assumed.

---

Vision

Smarter energy decisions. More efficient manufacturing. A sustainable future.

GridMind AI brings together generative AI and mathematical optimisation to explore how manufacturers can better understand energy consumption, investigate unusual patterns, and evaluate potential efficiency improvements.

By combining contextual AI explanations with numerical optimisation, the project aims to turn energy data into actionable insights and support more informed industrial energy management decisions.
