# GridMind AI — 3-Minute Competition Demonstration Script

**Platform URL**: `http://localhost:5173` (or deployed Firebase Hosting URL)  
**Total Target Duration**: 3 minutes (180 seconds)  
**Target Audience**: Judging Panel — AI Builder Cup

---

## Timeline & Spoken Script

### ⏱️ 0:00 – 0:25 | Hook & MSME Electricity Cost Problem
- **UI Action**: Show GridMind AI landing screen with the three core tabs visible (Factory Dashboard, AI Investigator, Renewable Simulator).
- **Spoken Script**:
  > *"Electricity is one of the highest operating expenses for over 60 million MSME manufacturers across India, often consuming 15 to 30% of their operational budget. Between complex Time-of-Day tariffs, uncoordinated motor starts, and underutilized solar and biomass, factories hemorrhage money every day.*
  > 
  > *Meet GridMind AI: an industrial intelligence platform that pairs deterministic mathematical optimization with Google Gemini to detect energy waste, orchestrate renewables, and slash electricity procurement costs."*

---

### ⏱️ 0:25 – 1:05 | Factory A: PrecisionWorks Factory (DEMO-FAC-001)
- **UI Action**:
  1. In the header dropdown, ensure **PrecisionWorks Factory** is selected.
  2. Scroll down on the **Factory Dashboard** to the **Detected Anomaly Alerts** section.
  3. Point to the **Off-Shift Standby Waste** alert (`FINDING-IDLE-WASTE-H03` in Zone 1: CNC Machining).
  4. Click **"Investigate with Gemini"** (or switch to the **AI Energy Investigator** tab).
  5. Click **"Run Investigation"** to show Gemini's grounded diagnostic reasoning.
- **Spoken Script**:
  > *"Here at PrecisionWorks Factory, a precision CNC machining facility, our deterministic heuristic engine detects 6 distinct energy waste events. Notice this critical finding at 03:00 AM: pneumatic air compressors and CNC auxiliary fans were left energized during non-production hours, leaking ₹4,200 in idle electricity.*
  > 
  > *With one click, we call Google Gemini. Notice that Gemini does not hallucinate math or replace physical readings: it consumes authoritative telemetry from our backend and generates a structured root-cause analysis—marking equipment degradation hypotheses as unconfirmed and providing prioritized maintenance steps."*

---

### ⏱️ 1:05 – 1:45 | Factory B: FreshField Factory (DEMO-FAC-002)
- **UI Action**:
  1. Open the **Active Factory** dropdown in the Header and select **FreshField Factory (DEMO-FAC-002)**.
  2. Notice how all KPIs, zone breakdowns, and tariff graphs immediately refresh with cold-storage telemetry.
  3. Navigate to the **Renewable Simulator** tab.
  4. Point out the **Grid-Only Baseline** vs. **Optimised Supply Cost**.
  5. Click **"Run Optimisation"** to show the live SciPy HiGHS LP solver in action.
- **Spoken Script**:
  > *"Now let's switch to FreshField Factory, a food processing and cold storage facility. Notice how every chart, tariff period, and demand curve instantly refreshes. Cold storage requires continuous baseline refrigeration that cannot simply be turned off during the expensive evening peak tariff.*
  > 
  > *Instead of guesswork, our SciPy HiGHS linear programming solver computes the cost-optimal hourly dispatch across rooftop solar, agricultural biomass briquettes, and utility grid power. The result? Substantial estimated electricity cost reduction, while keeping peak grid power safely within the 200 kW contract demand limit."*

---

### ⏱️ 1:45 – 2:25 | Factory C: WeaveWise Factory (DEMO-FAC-003)
- **UI Action**:
  1. Switch the factory dropdown to **WeaveWise Factory (DEMO-FAC-003)**.
  2. Scroll to the **Hourly Multi-Source Energy Dispatch** stacked bar chart.
  3. Highlight how solar generation (120 kWp) carries the midday spinning shift, and wind generation picks up in the late afternoon.
  4. Show the **Hourly Cost Comparison** chart showing significant cost clipping during peak hours.
- **Spoken Script**:
  > *"Next, we inspect WeaveWise Factory, a textile spinning and weaving facility. Ring-spinning and rapier looms run across two heavy production shifts. Notice the dynamic dispatch matrix: between 10:00 and 15:00, 120 kWp of rooftop solar covers nearly 70% of factory demand at zero marginal cost.*
  > 
  > *When evening approaches, our optimiser coordinates biomass pellets from cotton waste to arbitrage against high grid tariffs, keeping blended procurement costs at a predictable minimum."*

---

### ⏱️ 2:25 – 2:50 | Gemini AI Executive Synthesis & Explanation
- **UI Action**:
  1. Switch back to **AI Energy Investigator**.
  2. Click **"Generate Full Plant Report"** (or view the synthesized executive briefing).
  3. Highlight the **Prioritized Corrective Action Plan** and **Optimization Impact Summary**.
- **Spoken Script**:
  > *"Finally, Gemini acts as the factory manager's virtual energy engineer. It synthesizes all detected anomalies and mathematical optimization outcomes into an executive briefing—explaining why certain renewables were dispatched, which contract limits bound further savings, and which capital investments offer the fastest payback."*

---

### ⏱️ 2:50 – 3:00 | Conclusion & Impact
- **UI Action**: Pan back to the full dashboard overview.
- **Spoken Script**:
  > *"By uniting deterministic industrial physics, linear programming, and grounded generative AI, GridMind AI empowers MSMEs to cut electricity bills by 20 to 45% while accelerating India's clean energy transition. Thank you!"*

---

## Demo Checklist & Verification Steps Before Recording

1. **Backend Running**:
   - `http://localhost:8000/health` returns `status: ok`.
   - `http://localhost:8000/api/investigation/status` shows `is_available: true`.
2. **Frontend Running**:
   - `http://localhost:5173` loads without console errors.
3. **Pre-test Factory Switching**:
   - Verify selecting PrecisionWorks Factory shows CNC Machining & Heat Treatment zones.
   - Verify selecting FreshField Factory shows Cold Storage & Food Processing zones.
   - Verify selecting WeaveWise Factory shows Ring Spinning & Weaving zones.
4. **Backup Plan if Upstream Gemini Experiences Rate Limits or High Demand**:
   - The UI displays structured diagnostic fallback notes and analytical deviations without crashing.
   - All HiGHS LP dispatch charts, ToD tariffs, and cost calculations are 100% deterministic and will remain fully interactive.
