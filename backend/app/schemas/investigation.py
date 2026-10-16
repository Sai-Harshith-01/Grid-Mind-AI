"""Pydantic schemas for Phase 5 Gemini AI Energy Waste Investigation.

Defines typed data models for:
- Investigation status and AI metadata
- Anomaly investigation evidence and grounded context
- Qualitative explanations, hypotheses, and recommended actions
- Financial impact summaries grounded in backend calculations
- Single anomaly investigation requests and responses
- Batch investigation reports with partial failure tracking
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from app.schemas.factory import SimulationMetadata


class InvestigationPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class InvestigationStatus(str, Enum):
    COMPLETED = "completed"
    FAILED = "failed"
    UNAVAILABLE = "unavailable"
    PARTIAL = "partial"


class RecommendedAction(BaseModel):
    priority: InvestigationPriority = Field(
        ..., description="Execution priority: low, medium, high, critical."
    )
    action: str = Field(..., description="Concrete, actionable operational recommendation.")
    rationale: str = Field(..., description="Underlying engineering rationale for the action.")
    expected_operational_benefit: str = Field(
        ..., description="Expected operational or energy efficiency benefit."
    )
    safety_considerations: str = Field(
        ..., description="Industrial safety guidelines, interlocks, or equipment limits to observe."
    )
    verification_step: str = Field(
        ..., description="Specific measurement or check to verify that the issue has been resolved."
    )


class PossibleCause(BaseModel):
    hypothesis: str = Field(
        ..., description="Suspected physical or operational cause of the anomaly."
    )
    likelihood: str = Field(
        ..., description="Estimated qualitative likelihood (e.g. 'Possible', 'Probable', 'Low probability')."
    )
    supporting_evidence: str = Field(
        ..., description="Data points and observations that support this hypothesis."
    )
    is_confirmed: bool = Field(
        default=False,
        description="Always False unless independently confirmed by physical inspection or sensor telemetry.",
    )


class FinancialImpactSummary(BaseModel):
    detected_excess_energy_kwh: Optional[float] = Field(
        None, description="Excess energy consumed above threshold during anomaly interval(s) in kWh."
    )
    excess_energy_grid_cost_inr: Optional[float] = Field(
        None, description="Monetary impact of excess energy at interval tariff (₹)."
    )
    grid_only_baseline_cost_inr: Optional[float] = Field(
        None, description="24-hour baseline cost assuming 100% utility grid supply (₹)."
    )
    optimised_scenario_cost_inr: Optional[float] = Field(
        None, description="24-hour optimised multi-source supply cost from LP optimiser (₹)."
    )
    estimated_daily_savings_inr: Optional[float] = Field(
        None, description="Estimated total daily savings from renewable optimisation (₹)."
    )
    financial_caveats: str = Field(
        default=(
            "Calculated monetary impacts are simulated scenario estimates. "
            "Eliminating an anomaly does not automatically guarantee equivalent savings across the whole plant."
        ),
        description="Clear disclaimer explaining boundaries of financial estimates.",
    )


class InvestigationEvidence(BaseModel):
    anomaly_id: str
    interval_index: int
    timestamp: str
    category: str
    severity: str
    metric_name: str
    observed_value: float
    baseline_threshold: float
    deviation_value: float
    deviation_percent: float
    unit: str
    detection_rule_id: str
    detection_rule_description: str
    affected_zone_name: Optional[str] = None
    affected_machine_name: Optional[str] = None
    grid_tariff_inr_per_kwh: Optional[float] = None


class GeminiGeneratedInvestigation(BaseModel):
    """Structured qualitative response schema parsed directly from Gemini LLM output."""
    summary: str = Field(..., description="High-level executive summary of the investigation.")
    observations: List[str] = Field(
        ..., description="Factual observations derived strictly from the supplied evidence."
    )
    why_flagged_explanation: str = Field(
        ..., description="Technical explanation of why the Python detection rule triggered."
    )
    rule_evidence_vs_hypothesis: str = Field(
        ..., description="Explicit separation between rule-based data evidence and physical hypothesis."
    )
    possible_causes: List[PossibleCause] = Field(
        ..., description="Plausible physical causes, explicitly labelled as hypotheses."
    )
    recommended_actions: List[RecommendedAction] = Field(
        ..., description="Prioritised, safe operational actions for plant operators."
    )
    uncertainties: List[str] = Field(
        ..., description="Uncertainties, missing data points, or unverified assumptions."
    )
    follow_up_checks: List[str] = Field(
        ..., description="Specific physical or telemetry checks required to confirm root cause."
    )
    financial_observations: str = Field(
        ..., description="Qualitative commentary on the backend-calculated financial metrics."
    )


class InvestigationAiMetadata(BaseModel):
    model_name: str = Field(..., description="Google Gemini model identifier used.")
    provider: str = Field(default="Google Gemini", description="AI provider name.")
    is_mocked: bool = Field(
        default=False, description="True if response was generated by mock client for testing."
    )
    latency_ms: Optional[float] = Field(None, description="API response latency in milliseconds.")
    tokens_used: Optional[int] = Field(None, description="Total tokens consumed if reported by provider.")
    temperature: float = Field(default=0.2, description="Sampling temperature used.")


class InvestigationResponse(BaseModel):
    investigation_id: str = Field(..., description="Unique investigation run identifier.")
    anomaly_id: str = Field(..., description="Associated anomaly ID.")
    status: InvestigationStatus = Field(..., description="Investigation status.")
    summary: str = Field(..., description="Executive summary of the investigation.")
    observations: List[str] = Field(..., description="Key factual observations.")
    evidence: InvestigationEvidence = Field(..., description="Authoritative backend evidence.")
    possible_causes: List[PossibleCause] = Field(
        ..., description="Hypothesised causes (unconfirmed)."
    )
    recommended_actions: List[RecommendedAction] = Field(
        ..., description="Prioritised, safe operational actions."
    )
    financial_impact: FinancialImpactSummary = Field(
        ..., description="Authoritative backend financial impact metrics."
    )
    uncertainties: List[str] = Field(..., description="Documented uncertainties.")
    follow_up_checks: List[str] = Field(..., description="Recommended diagnostic follow-ups.")
    simulation_metadata: SimulationMetadata = Field(..., description="Dataset simulation metadata.")
    ai_metadata: InvestigationAiMetadata = Field(..., description="Gemini AI execution metadata.")


class InvestigationReportRequest(BaseModel):
    max_findings: int = Field(
        default=5, ge=1, le=10, description="Maximum number of anomalies to investigate in batch."
    )
    min_severity: Optional[str] = Field(
        default=None, description="Optional minimum severity filter: low, medium, high, critical."
    )


class FailedInvestigationItem(BaseModel):
    anomaly_id: str
    error_message: str


class InvestigationReportResponse(BaseModel):
    report_id: str = Field(..., description="Unique investigation report identifier.")
    generated_at: str = Field(..., description="ISO 8601 generation timestamp.")
    total_anomalies_evaluated: int = Field(..., description="Total anomalies evaluated in batch.")
    successful_investigations_count: int = Field(..., description="Count of successfully investigated anomalies.")
    failed_investigations_count: int = Field(..., description="Count of failed anomaly investigations.")
    overall_risk_summary: str = Field(..., description="Synthesised plant-wide energy risk assessment.")
    investigations: List[InvestigationResponse] = Field(
        default_factory=list, description="Detailed investigations for each evaluated anomaly."
    )
    partial_failures: List[FailedInvestigationItem] = Field(
        default_factory=list, description="Anomalies that could not be investigated."
    )
    prioritized_actions: List[RecommendedAction] = Field(
        default_factory=list, description="Aggregated, prioritised corrective action plan."
    )
    optimization_context: Optional[Dict[str, Any]] = Field(
        None, description="High-level LP optimisation summary for context."
    )
    simulation_metadata: SimulationMetadata
    ai_metadata: InvestigationAiMetadata


class InvestigationStatusResponse(BaseModel):
    is_configured: bool = Field(
        ..., description="True if GEMINI_API_KEY is configured in backend environment."
    )
    model_name: str = Field(..., description="Configured Gemini model name.")
    is_available: bool = Field(
        ..., description="True if AI investigation services are ready to accept requests."
    )
    status_message: str = Field(
        ..., description="Safe user-facing status message (secrets never included)."
    )
    supported_modes: List[str] = Field(
        default_factory=lambda: ["single_anomaly_investigation", "batch_investigation_report"],
        description="Supported investigation workflows.",
    )
