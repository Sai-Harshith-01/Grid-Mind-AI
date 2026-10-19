⚡ GridMind AI

🌱 AI-Powered Energy Intelligence and Optimisation for MSME Manufacturing

Turning industrial energy data into actionable insights through AI-assisted investigation and mathematical optimisation.

GridMind AI is an energy intelligence prototype designed to help micro, small, and medium-sized manufacturing enterprises (MSMEs) understand electricity consumption, identify unusual energy usage, and evaluate cost-effective energy allocation strategies.

The platform combines Google Gemini for AI-assisted energy investigation with SciPy and HiGHS for constrained energy optimisation. It brings energy analytics, anomaly detection, AI-generated insights, and electricity cost analysis into a unified dashboard.

«🚧 Project Status: Prototype
🧪 Data Transparency: Factory profiles and demonstration datasets are fictional and synthetic. Savings and optimisation results are modelled estimates, not verified real-world outcomes.»

📌 Problem Statement

Manufacturing facilities consume electricity across machinery, production lines, refrigeration, lighting, and other industrial operations.

MSMEs may face challenges such as:

- 📊 Limited visibility into electricity consumption patterns.
- 🔍 Difficulty identifying unusual energy usage.
- 💸 Increasing electricity costs during peak-demand periods.
- ☀️ Limited tools for evaluating renewable energy utilisation.
- ⚙️ Difficulty comparing alternative energy allocation strategies.

GridMind AI explores how accessible analytics and mathematical optimisation can support more informed energy management decisions.

🚀 Key Features

📊 1. Energy Intelligence Dashboard

- Visualise factory energy consumption and energy profiles.
- Review energy indicators and detected anomalies.
- Compare baseline and optimised electricity costs.
- Explore energy allocation scenarios and modelled savings.

🔍 2. Electricity Anomaly Detection

Identifies potentially unusual consumption patterns using configured rules and baselines.

Detected anomalies are indicators for further investigation, not proof of energy waste or equipment failure.

🤖 3. Gemini AI Energy Investigator

Uses Google Gemini to interpret available energy findings, suggest possible causes of unusual consumption, and recommend practical verification steps.

AI-generated explanations are advisory and may require independent verification.

⚡ 4. Constrained Energy Optimisation

Uses SciPy and the HiGHS optimisation solver to calculate energy allocations that minimise modelled electricity costs under configured constraints.

The model can account for demand requirements, energy source availability, configured costs, and supported supply limits.

💰 5. Energy Cost Analysis

- Compare baseline and optimised electricity costs.
- Calculate modelled daily savings and savings percentages.
- Generate annualised estimates using configured operating days.
- Evaluate illustrative time-of-use tariff scenarios.

All savings depend on the model inputs, assumptions, and implemented constraints.

🏭 6. Multiple Factory Profiles

Includes three fictional manufacturing scenarios:

- ⚙️ PrecisionWorks Factory: Precision engineering and CNC machining.
- 🥬 FreshField Factory: Food processing and cold storage.
- 🧵 WeaveWise Factory: Textile spinning and weaving.

🔄 System Workflow

1. 🏭 Factory Selection: Select a demonstration manufacturing profile.
2. 📥 Data Loading: Load synthetic energy demand and source assumptions.
3. 📊 Energy Analysis: Evaluate consumption patterns and configured baselines.
4. 🔍 Anomaly Detection: Identify unusual usage using predefined rules.
5. 🤖 AI Investigation: Generate contextual explanations using Gemini.
6. ⚙️ Energy Optimisation: Calculate an allocation using SciPy and HiGHS.
7. 💰 Cost Comparison: Compare baseline and optimised costs.
8. 📈 Dashboard Insights: Present analytical findings and modelled results.

💡 Core Principle: AI interprets the evidence, while mathematical optimisation calculates the energy allocation.

🏗️ System Architecture

The system separates the user interface, backend processing, AI investigation, energy analytics, and mathematical optimisation.

- 🖥️ Frontend: React and TypeScript dashboard.
- 🔌 Backend API: FastAPI for request handling and workflow coordination.
- 📊 Analytics Engine: Energy consumption analysis and rule-based anomaly detection.
- 🤖 AI Engine: Gemini-powered interpretation of energy findings.
- ⚙️ Optimisation Engine: SciPy and HiGHS for constrained energy allocation.
- 💰 Cost Analysis: Baseline comparison and modelled savings calculations.
- 📈 Visualisation: Dashboard presentation of insights and numerical results.

🛠️ Technology Stack

Technology| Purpose
⚛️ React| Frontend interface
📘 TypeScript| Frontend logic and type safety
⚡ Vite| Frontend development and build tooling
🎨 Tailwind CSS| Interface styling
🐍 Python| Backend processing and analytics
🚀 FastAPI| Backend API framework
🌐 Uvicorn| ASGI application server
🤖 Google Gemini| AI-assisted energy investigation
🔗 Google GenAI SDK| Gemini API integration
🧮 SciPy| Scientific computing and optimisation
⚙️ HiGHS| Numerical optimisation solver

🧮 Energy Optimisation Model

GridMind AI formulates energy allocation as a cost-minimisation problem.

The objective is to minimise the modelled cost of meeting electricity demand while respecting configured energy source capacities and availability.

Model inputs may include:

- ⚡ Electricity demand.
- 💰 Energy source costs.
- ☀️ Renewable energy availability.
- 🔌 Grid supply limits.
- 🕒 Time-dependent electricity tariffs.

The model can evaluate configured sources such as solar, wind, biomass, and grid electricity.

The results depend on the mathematical formulation and the data supplied to the optimiser. Infrastructure costs, storage losses, maintenance, and capital expenditure are not assumed to be included unless explicitly implemented.

🏭 Demonstration Data

All demonstration factories and their energy datasets are fictional.

Factory| Demonstration ID| Scenario
⚙️ PrecisionWorks Factory| "DEMO-FAC-001"| Precision engineering
🥬 FreshField Factory| "DEMO-FAC-002"| Food processing and cold storage
🧵 WeaveWise Factory| "DEMO-FAC-003"| Textile manufacturing

🧪 Data Disclosure: Illustrative tariffs and modelled savings are used for demonstration purposes. They should not be interpreted as verified industrial measurements or guaranteed financial outcomes.

💻 Getting Started

📋 Prerequisites

- Git
- Python compatible with the backend dependencies
- Node.js and npm
- Google Gemini API key for AI investigation

1️⃣ Clone the Repository

git clone https://github.com/Sai-Harshith-01/Grid-Mind-AI.git
cd Grid-Mind-AI

2️⃣ Set Up the Backend

cd backend
python -m venv .venv

Activate the virtual environment on Windows:

.\.venv\Scripts\Activate.ps1

Install dependencies:

python -m pip install --upgrade pip
pip install -r requirements.txt

Configure the required environment variables using the project's environment configuration.

🔐 Keep the Gemini API key on the backend and never expose it in frontend code.

If the backend entry point is "app.main", start the development server with:

uvicorn app.main:app --reload --port 8000

3️⃣ Set Up the Frontend

Open a second terminal:

cd frontend
npm install
npm run dev

Open the local URL displayed by Vite.

4️⃣ 📖 API Documentation

If FastAPI's default documentation is enabled, access:

- 📘 Swagger UI: http://localhost:8000/docs
- 📄 OpenAPI Schema: http://localhost:8000/openapi.json

Verify the entry point and configuration against the actual repository before running these commands.

🧪 Testing and Validation

Recommended validation includes:

- 🔍 Anomaly detection using synthetic test cases.
- ⚡ Energy demand and source capacity constraints.
- 🧮 Optimisation solver status and infeasible scenarios.
- 💰 Baseline and optimised cost calculations.
- 🛡️ Invalid input and API error handling.
- 🤖 Gemini API failure handling.
- 🖥️ Frontend production build.

Backend tests, if configured:

python -m pytest tests/ -v

Frontend build check:

npm run build

Run the commands from their respective project directories. No test results or build status are claimed here.

🔐 Security and Privacy

- 🔑 Store API keys and credentials on the backend.
- 🚫 Exclude ".env" files and secrets from version control.
- ✅ Validate incoming API requests.
- 🛡️ Avoid logging sensitive information.
- 🌐 Restrict cross-origin requests to approved origins where applicable.
- ⚠️ Handle external AI service errors safely.
- 🔒 Review authentication, authorisation, and rate limiting before production deployment.

Using real industrial data would require additional security controls and appropriate data governance.

🌍 Sustainability Impact

GridMind AI explores how energy intelligence can support more efficient industrial operations.

- ♻️ Energy Efficiency: Identify consumption patterns that warrant investigation.
- 💸 Cost Visibility: Compare alternative energy allocation scenarios.
- ☀️ Renewable Utilisation: Evaluate available renewable generation within configured constraints.
- 📊 Data-Driven Decisions: Present analytical findings and modelled results in one dashboard.
- 🌱 Sustainability Assessment: Support future evaluation of energy and environmental outcomes.

These are intended benefits. Actual savings and emissions reductions require validation using real operational data.

⚠️ Limitations

- Demonstration factories and datasets are synthetic.
- Illustrative tariffs may differ from actual electricity tariffs.
- Optimisation quality depends on the model formulation and input accuracy.
- AI-generated explanations may be incomplete or incorrect.
- Anomaly detection does not confirm equipment faults.
- Modelled savings are estimates, not guaranteed outcomes.
- Real-world industrial performance has not been established.

GridMind AI is a decision-support prototype, not a certified energy audit or an autonomous industrial control system.

🔮 Future Enhancements

- 📡 Integration with authorised industrial electricity meter data.
- 📈 Historical energy trend analysis.
- 🎯 Calibration against verified tariffs and production schedules.
- 🧪 Evaluation of anomaly detection accuracy.
- ⚙️ Validation across additional optimisation scenarios.
- 🏭 Pilot studies with MSME manufacturers.
- 🌱 Measurement of actual energy savings and environmental outcomes.

👥 Team

Team Name: Techies
Team Leader: Sai Harshith
Project: GridMind AI

Focus Areas: Sustainable energy, industrial efficiency, AI-assisted investigation, and mathematical optimisation.

📄 License

No open-source license is currently specified. Unless a license is added to the repository, permissions to use, modify, or redistribute the project should not be assumed.

---

🌟 Vision

⚡ Smarter energy decisions. 🏭 More efficient manufacturing. 🌱 A sustainable future.

GridMind AI explores how generative AI and mathematical optimisation can help manufacturers understand energy consumption, investigate unusual patterns, and evaluate potential efficiency improvements.

Built to explore the future of intelligent industrial energy management.
