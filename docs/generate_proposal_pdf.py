"""Generate a high-quality PDF of the GridMind AI Proposal Deck using ReportLab."""

import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
    KeepTogether,
)

OUTPUT_PDF = os.path.join(os.path.dirname(__file__), "GridMind_AI_Proposal_Deck.pdf")

def build_pdf():
    doc = SimpleDocTemplate(
        OUTPUT_PDF,
        pagesize=A4,
        leftMargin=40,
        rightMargin=40,
        topMargin=40,
        bottomMargin=40,
    )

    styles = getSampleStyleSheet()
    
    # Custom typography
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=24,
        leading=28,
        textColor=colors.HexColor('#0f172a'),
        fontName='Helvetica-Bold',
        spaceAfter=4,
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#0d9488'),
        fontName='Helvetica-Bold',
        spaceAfter=15,
    )
    h2_style = ParagraphStyle(
        'Heading2Custom',
        parent=styles['Heading2'],
        fontSize=14,
        leading=18,
        textColor=colors.HexColor('#0f172a'),
        fontName='Helvetica-Bold',
        spaceBefore=12,
        spaceAfter=6,
    )
    body_style = ParagraphStyle(
        'BodyCustom',
        parent=styles['BodyText'],
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor('#334155'),
        spaceAfter=6,
    )
    bullet_style = ParagraphStyle(
        'BulletCustom',
        parent=styles['Normal'],
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#334155'),
        leftIndent=14,
        spaceAfter=3,
    )
    callout_style = ParagraphStyle(
        'Callout',
        parent=styles['Normal'],
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor('#92400e'),
        fontName='Helvetica-Oblique',
    )

    story = []

    # Title Block
    story.append(Paragraph("GridMind AI", title_style))
    story.append(Paragraph("AI-Powered Renewable Electricity Intelligence & Optimisation Platform for MSMEs", subtitle_style))
    story.append(Paragraph("AI Builder Cup — Final Proposal & Architecture Specification", body_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#0d9488'), spaceBefore=4, spaceAfter=12))

    # Executive Summary
    story.append(Paragraph("1. Executive Summary", h2_style))
    story.append(Paragraph(
        "Electricity procurement is typically the 2nd highest operational expense in manufacturing MSMEs, "
        "representing 15% to 35% of total operating budgets. Complex multi-tier Time-of-Day (ToD) tariffs, "
        "uncoordinated shift startups, and underutilised on-site solar, wind, and biomass result in heavy recurring losses. "
        "<b>GridMind AI</b> combines deterministic industrial physics, linear programming (SciPy HiGHS solver), "
        "and grounded Google Gemini AI to help MSME plant managers understand electricity waste, orchestrate clean energy sources, "
        "and reduce estimated procurement costs by 20% to 45%.",
        body_style
    ))

    # Architecture & Technology
    story.append(Paragraph("2. System Architecture & Technology Stack", h2_style))
    tech_data = [
        ["Layer", "Technology", "Role & Boundary"],
        ["Frontend UI", "React 18, Vite, TypeScript, Tailwind CSS, Recharts", "Factory switcher, real-time telemetry, LP dispatch charts, alerts"],
        ["Backend Core", "Python 3.11+, FastAPI, Pydantic v2", "Deterministic physics simulator, REST APIs, ToD tariff modeling"],
        ["Optimization", "SciPy HiGHS Solver (LP simplex & interior-point)", "Constrained cost-minimizing multi-source hourly energy allocation"],
        ["Generative AI", "Google Gemini 2.0 (via Google GenAI SDK)", "Evidence-grounded anomaly investigation & executive reporting"],
        ["Cloud Deploy", "Google Cloud Run & Firebase Hosting", "Containerized autoscaling microservices with Secret Manager"],
    ]
    t_tech = Table(tech_data, colWidths=[80, 190, 245])
    t_tech.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0f172a')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8.5),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor('#f8fafc'), colors.white]),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_tech)
    story.append(Spacer(1, 8))

    # Core Architectural Boundary
    boundary_box = [
        [Paragraph("<b>CRITICAL ARCHITECTURAL BOUNDARY:</b> The Large Language Model (Gemini) <i>never</i> calculates rupee balances, consumption totals, or dispatch limits. All numbers are computed authoritatively by the deterministic backend and supplied to Gemini as verified evidence.", callout_style)]
    ]
    t_box = Table(boundary_box, colWidths=[515])
    t_box.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#fef3c7')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#f59e0b')),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_box)
    story.append(Spacer(1, 8))

    # Three MSME Demo Factories
    story.append(Paragraph("3. Three Configured Demo MSME Factory Profiles", h2_style))
    story.append(Paragraph(
        "GridMind AI supports exactly three distinct Indian MSME factory archetypes with isolated datasets, distinct connected loads, and tailored generation profiles:",
        body_style
    ))

    fac_data = [
        ["Factory ID & Name", "Location & Industry", "Connected Load / Grid Limit", "Renewable Assets", "Key Demonstration Scenario"],
        [
            "DEMO-FAC-001\nPrecisionWorks Factory",
            "Demonstration Zone 1\nCNC & Auto Components",
            "260 kW Load\n250 kW Contract Demand",
            "100 kWp Solar\n60 kW Wind\n50 kW Biomass",
            "Detect off-shift standby compressor waste (03:00) & peak tariff surge (19:00)."
        ],
        [
            "DEMO-FAC-002\nFreshField Factory",
            "Demonstration Zone 2\nFood & Cold Storage",
            "210 kW Load\n200 kW Contract Demand",
            "75 kWp Solar\n20 kW Wind\n35 kW Agro-Biomass",
            "Continuous refrigeration demand during evening peak tariff (₹12.20/kWh)."
        ],
        [
            "DEMO-FAC-003\nWeaveWise Factory",
            "Demonstration Zone 3\nSpinning & Weaving",
            "280 kW Load\n270 kW Contract Demand",
            "120 kWp Solar\n50 kW Wind\n45 kW Pellet Biomass",
            "High solar self-consumption and wind/biomass arbitration against Regional Utility rates."
        ],
    ]
    t_fac = Table(fac_data, colWidths=[95, 105, 105, 95, 115])
    t_fac.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0f172a')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 7.5),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor('#f8fafc'), colors.white]),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_fac)
    story.append(Spacer(1, 8))

    # Mathematical Optimisation
    story.append(Paragraph("4. Linear Programming Dispatch Formulation (HiGHS)", h2_style))
    story.append(Paragraph("<b>Objective:</b> Minimize total daily electricity procurement cost across 24 hourly intervals:", body_style))
    story.append(Paragraph("• <i>min</i> &Sigma;<sub>t</sub> [ c<sub>solar</sub>&middot;x<sub>solar,t</sub> + c<sub>wind</sub>&middot;x<sub>wind,t</sub> + c<sub>biomass</sub>&middot;x<sub>biomass,t</sub> + Tariff<sub>t</sub>&middot;x<sub>grid,t</sub> ]", bullet_style))
    story.append(Paragraph("<b>Physical Constraints Enforced on Every Interval:</b>", body_style))
    story.append(Paragraph("1. <b>Energy Balance:</b> x<sub>solar,t</sub> + x<sub>wind,t</sub> + x<sub>biomass,t</sub> + x<sub>grid,t</sub> = Demand<sub>t</sub>", bullet_style))
    story.append(Paragraph("2. <b>Solar Resource Cap:</b> 0 &le; x<sub>solar,t</sub> &le; min(SolarAvailable<sub>t</sub>, SolarCapacity)", bullet_style))
    story.append(Paragraph("3. <b>Wind Resource Cap:</b> 0 &le; x<sub>wind,t</sub> &le; min(WindAvailable<sub>t</sub>, WindCapacity)", bullet_style))
    story.append(Paragraph("4. <b>Biomass Power & Fuel Budget:</b> 0 &le; x<sub>biomass,t</sub> &le; Capacity and &Sigma; x<sub>biomass,t</sub> &le; DailyBudgetKg / SFC", bullet_style))
    story.append(Paragraph("5. <b>Sanctioned Grid Headroom:</b> 0 &le; x<sub>grid,t</sub> &le; ContractDemandLimit", bullet_style))

    # Google Gemini GenAI Integration
    story.append(Paragraph("5. Google Gemini Grounded Intelligence", h2_style))
    story.append(Paragraph(
        "Gemini provides 5 production capabilities without hallucinating calculations: "
        "(1) <b>Single Anomaly Root-Cause Investigation</b> with structured hypotheses; "
        "(2) <b>Prioritized Action Recommendations</b> with safety checks; "
        "(3) <b>Mathematical Optimization Explanation</b> clarifying why sources were dispatched; "
        "(4) <b>Full Factory Executive Briefing</b> synthesizing plant-wide energy risks; and "
        "(5) <b>Context-Aware Operator Q&A</b>.",
        body_style
    ))

    # Verification & Impact
    story.append(Paragraph("6. Quality Verification & Test Coverage", h2_style))
    story.append(Paragraph("• <b>Backend Tests</b>: 97 automated pytest tests passing in ~10 seconds.", bullet_style))
    story.append(Paragraph("• <b>Frontend Build</b>: Zero TypeScript errors; production bundle built cleanly in ~19s.", bullet_style))
    story.append(Paragraph("• <b>Data Isolation</b>: Full per-factory cache isolation verified across all endpoints.", bullet_style))
    story.append(Paragraph("• <b>Disclaimer</b>: All factory readings, equipment telemetry, and savings figures are synthetically generated for prototype evaluation.", bullet_style))

    doc.build(story)
    print(f"Proposal PDF generated successfully at: {OUTPUT_PDF}")

if __name__ == "__main__":
    build_pdf()
