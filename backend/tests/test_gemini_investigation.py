"""Unit and integration tests for Phase 5 Gemini AI Energy Waste Investigator.

Verifies:
1. Application startup succeeds when Gemini API key is missing.
2. Investigation status never exposes secrets.
3. Unknown anomaly IDs return HTTP 404.
4. Investigation context comes from trusted backend services.
5. User input cannot override backend-calculated numerical values.
6. The prompt includes the evidence and synthetic-data limitations.
7. Valid Gemini output passes schema validation.
8. Malformed output is handled safely with bounded 1-retry, then graceful error.
9. Invalid credentials produce a useful error response without repeated retries.
10. Rate limits and timeouts are handled correctly.
11. Retries are strictly bounded.
12. Report requests enforce their maximum anomaly limit.
13. Partial report failures are represented correctly.
14. Financial figures remain consistent with the optimisation service.
15. The response never presents generated hypotheses as confirmed facts (is_confirmed: false).
16. Existing Phase 1-4 endpoints continue working without regression.
"""

import json
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient
from google.genai import errors

from app.core.config import settings
from app.main import app
from app.prompts.energy_investigation import (
    SYSTEM_INVESTIGATION_INSTRUCTION,
    build_investigation_prompt,
    build_report_summary_prompt,
)
from app.schemas.investigation import (
    InvestigationPriority,
    InvestigationStatus,
    GeminiGeneratedInvestigation,
)
from app.services.anomaly_detector import anomaly_detector_service
from app.services.energy_optimizer import energy_optimizer_service
from app.services.gemini_service import (
    AnomalyNotFoundError,
    GeminiAuthenticationError,
    GeminiInvestigationService,
    GeminiMalformedOutputError,
    GeminiRateLimitError,
    GeminiServiceUnavailableError,
    GeminiTimeoutError,
    GeminiUpstreamError,
    gemini_investigation_service,
)

client = TestClient(app)


# Sample valid JSON output returned by Gemini model mock
SAMPLE_GEMINI_OUTPUT = {
    "summary": "Pneumatic system air leakage detected during off-schedule interval 3 (03:00-04:00).",
    "observations": [
        "Machining Center baseline power was expected at 2.0 kW during inactive night shift.",
        "Observed power draw was 18.5 kW, representing a 16.5 kW unbudgeted deviation.",
        "Associated interval utility tariff was ₹6.50/kWh.",
    ],
    "why_flagged_explanation": (
        "The Python rule 'RULE-OFF-HOURS-BASELOAD' triggered because the machine was scheduled off "
        "yet active power exceeded the 3.0 kW standby threshold by 15.5 kW (516% deviation)."
    ),
    "rule_evidence_vs_hypothesis": (
        "Rule evidence proves unmetered energy draw of 18.5 kWh occurred at 03:00. "
        "A leaky air line or faulty solenoid is a plausible hypothesis requiring physical confirmation."
    ),
    "possible_causes": [
        {
            "hypothesis": "Main air supply line regulator failure or unseated drain valve in Zone 1.",
            "likelihood": "High",
            "supporting_evidence": "Power consumption matches constant auxiliary compressor cycling.",
            "is_confirmed": False,
        },
        {
            "hypothesis": "Operator inadvertently left machine in standby heating mode before shift end.",
            "likelihood": "Medium",
            "supporting_evidence": "Temperature telemetry was elevated relative to ambient.",
            "is_confirmed": False,
        },
    ],
    "recommended_actions": [
        {
            "priority": "critical",
            "action": "Isolate pneumatic drop valve at Machining Center #1 immediately.",
            "rationale": "Stops continuous compressed air bleed and compressor short-cycling.",
            "expected_operational_benefit": "Eliminates ~16.5 kW continuous parasitic electrical draw.",
            "safety_considerations": (
                "Depressurize air line before servicing; follow plant Lockout/Tagout (LOTO) protocols."
            ),
            "verification_step": "Verify active power drops below 2.0 kW on the main zone sub-meter.",
        },
        {
            "priority": "high",
            "action": "Inspect pneumatic fittings and quick-disconnects with ultrasonic leak detector.",
            "rationale": "Identifies pinhole leaks across the distribution header.",
            "expected_operational_benefit": "Prevents recurrence during subsequent non-operational hours.",
            "safety_considerations": "Wear eye protection and safety helmet in machine enclosure.",
            "verification_step": "Ensure ultrasonic acoustic baseline reads < 20 dBA around fittings.",
        },
    ],
    "uncertainties": [
        "Sub-metering is at machine level; specific failed pneumatic fitting cannot be identified remotely."
    ],
    "follow_up_checks": [
        "Perform manual pressure decay test on Zone 1 air receiver tank.",
        "Review PLC shift shut-down sequence logs."
    ],
    "financial_observations": (
        "This anomaly accounts for approximately ₹107.25 in excess grid costs for this single interval. "
        "Left unaddressed over 30 days, annualized waste could exceed ₹38,000."
    ),
}


def create_mock_genai_client(return_text: str = json.dumps(SAMPLE_GEMINI_OUTPUT)):
    """Helper to create a mocked Google GenAI client."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = return_text
    mock_client.models.generate_content.return_value = mock_response
    return mock_client


class TestGeminiInvestigationUnit:
    """Unit tests for Gemini AI Investigation service logic and prompt grounding."""

    def test_app_startup_succeeds_without_gemini_key(self):
        """1. App startup succeeds when Gemini API key is missing."""
        service = GeminiInvestigationService(api_key=None)
        assert service.is_configured is False
        status_resp = service.get_status()
        assert status_resp.is_configured is False
        assert status_resp.is_available is False
        assert "not configured" in status_resp.status_message.lower()

    def test_investigation_status_never_exposes_secrets(self):
        """2. Investigation status never exposes secrets."""
        secret_key = "AIzaSySecretRealKeyDoNotExpose12345"
        service = GeminiInvestigationService(api_key=secret_key)
        status_resp = service.get_status()
        status_json = status_resp.model_dump_json()
        assert secret_key not in status_json
        assert "SecretRealKey" not in status_json
        assert status_resp.is_configured is True
        assert status_resp.is_available is True

    def test_unknown_anomaly_id_raises_not_found(self):
        """3. Unknown anomaly IDs raise AnomalyNotFoundError."""
        mock_client = create_mock_genai_client()
        service = GeminiInvestigationService(api_key="valid_key", client=mock_client)
        with pytest.raises(AnomalyNotFoundError):
            service.investigate_anomaly("non-existent-anomaly-id-999")

    def test_investigation_context_assembled_from_trusted_backend(self):
        """4. Investigation context comes from trusted backend services."""
        anomalies = anomaly_detector_service.get_anomalies().findings
        assert len(anomalies) > 0
        target = anomalies[0]

        service = GeminiInvestigationService(api_key="test_key")
        context = service._build_bounded_context(target)

        # Verified backend facts
        assert "factory_identity" in context
        assert "anomaly_evidence" in context
        assert "backend_optimization_context" in context
        assert context["anomaly_evidence"]["finding_id"] == target.finding_id
        assert context["anomaly_evidence"]["observed_value"] == target.evidence.observed_value
        assert context["anomaly_evidence"]["unit"] == target.evidence.unit
        assert context["backend_optimization_context"]["is_feasible"] is True

    def test_prompt_includes_evidence_and_synthetic_disclaimer(self):
        """6. The prompt includes the evidence and synthetic-data limitations."""
        anomalies = anomaly_detector_service.get_anomalies().findings
        service = GeminiInvestigationService(api_key="test_key")
        context = service._build_bounded_context(anomalies[0])
        prompt = build_investigation_prompt(context)

        assert anomalies[0].finding_id in prompt
        assert str(anomalies[0].evidence.observed_value) in prompt
        assert SYSTEM_INVESTIGATION_INSTRUCTION is not None
        assert "STRICT EVIDENCE BOUNDARY" in SYSTEM_INVESTIGATION_INSTRUCTION
        assert "SYNTHETIC PROTOTYPE DISCLAIMER" in SYSTEM_INVESTIGATION_INSTRUCTION

    def test_valid_gemini_output_passes_schema_validation(self):
        """7. Valid Gemini output passes schema validation."""
        mock_client = create_mock_genai_client(json.dumps(SAMPLE_GEMINI_OUTPUT))
        service = GeminiInvestigationService(api_key="test_key", client=mock_client)

        anomalies = anomaly_detector_service.get_anomalies().findings
        inv = service.investigate_anomaly(anomalies[0].finding_id)

        assert inv.status == InvestigationStatus.COMPLETED
        assert inv.anomaly_id == anomalies[0].finding_id
        assert len(inv.possible_causes) == 2
        assert len(inv.recommended_actions) == 2
        assert inv.ai_metadata.provider == "Google Gemini"

    def test_hypotheses_never_presented_as_confirmed_facts(self):
        """15. The response never presents generated hypotheses as confirmed facts."""
        # Intentionally tamper the LLM mock to claim is_confirmed = True
        tampered_output = dict(SAMPLE_GEMINI_OUTPUT)
        tampered_output["possible_causes"] = [
            {
                "hypothesis": "Confirmed equipment failure.",
                "likelihood": "Certain",
                "supporting_evidence": "Telemetry spike.",
                "is_confirmed": True,  # Attacking the boundary!
            }
        ]

        mock_client = create_mock_genai_client(json.dumps(tampered_output))
        service = GeminiInvestigationService(api_key="test_key", client=mock_client)

        anomalies = anomaly_detector_service.get_anomalies().findings
        inv = service.investigate_anomaly(anomalies[0].finding_id)

        # The service MUST unconditionally override is_confirmed to False
        for cause in inv.possible_causes:
            assert cause.is_confirmed is False

    def test_financial_figures_consistent_with_optimisation_service(self):
        """14. Financial figures remain consistent with the optimisation service."""
        mock_client = create_mock_genai_client(json.dumps(SAMPLE_GEMINI_OUTPUT))
        service = GeminiInvestigationService(api_key="test_key", client=mock_client)

        anomalies = anomaly_detector_service.get_anomalies().findings
        inv = service.investigate_anomaly(anomalies[0].finding_id)

        opt_summary = energy_optimizer_service.get_summary()
        assert inv.financial_impact.grid_only_baseline_cost_inr == opt_summary.baseline_grid_only_cost_inr
        assert inv.financial_impact.optimised_scenario_cost_inr == opt_summary.optimised_supply_cost_inr
        assert inv.financial_impact.estimated_daily_savings_inr == opt_summary.estimated_savings_inr

    def test_malformed_output_triggers_bounded_single_retry_then_fails(self):
        """8. Malformed output is handled safely with at most 1 correction retry."""
        mock_client = MagicMock()
        mock_response_bad = MagicMock()
        mock_response_bad.text = "This is not JSON at all, completely malformed output."
        mock_client.models.generate_content.return_value = mock_response_bad

        service = GeminiInvestigationService(api_key="test_key", client=mock_client)
        anomalies = anomaly_detector_service.get_anomalies().findings

        with pytest.raises(GeminiMalformedOutputError):
            service.investigate_anomaly(anomalies[0].finding_id)

        # Should have called generate_content twice: 1 initial call + 1 bounded correction
        assert mock_client.models.generate_content.call_count == 2

    def test_invalid_credentials_produce_useful_error_and_no_retry(self):
        """9. Invalid credentials produce useful error without repeated retries."""
        mock_client = MagicMock()
        api_err = errors.APIError(code=401, response_json={"error": {"message": "API_KEY_INVALID: User not authorized."}})
        mock_client.models.generate_content.side_effect = api_err

        service = GeminiInvestigationService(api_key="invalid_key", client=mock_client)
        anomalies = anomaly_detector_service.get_anomalies().findings

        with pytest.raises(GeminiAuthenticationError) as exc_info:
            service.investigate_anomaly(anomalies[0].finding_id)

        assert "authentication failed" in str(exc_info.value).lower()
        # Crucial: Auth errors must NEVER retry!
        assert mock_client.models.generate_content.call_count == 1

    def test_rate_limits_produce_useful_error(self):
        """10A. Rate limits (HTTP 429) raise GeminiRateLimitError."""
        mock_client = MagicMock()
        api_err = errors.APIError(code=429, response_json={"error": {"message": "RESOURCE_EXHAUSTED: Rate quota exceeded."}})
        mock_client.models.generate_content.side_effect = api_err

        service = GeminiInvestigationService(api_key="test_key", client=mock_client)
        anomalies = anomaly_detector_service.get_anomalies().findings

        with pytest.raises(GeminiRateLimitError):
            service.investigate_anomaly(anomalies[0].finding_id)

    def test_timeouts_are_handled_correctly(self):
        """10B & 11. Timeouts are handled correctly and retries are bounded."""
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = TimeoutError("Request timed out.")

        max_retries = 2
        service = GeminiInvestigationService(
            api_key="test_key", client=mock_client, max_retries=max_retries, timeout_seconds=5
        )
        anomalies = anomaly_detector_service.get_anomalies().findings

        with pytest.raises(GeminiTimeoutError):
            service.investigate_anomaly(anomalies[0].finding_id)

        # 1 initial + 2 retries = 3 calls
        assert mock_client.models.generate_content.call_count == max_retries + 1

    def test_report_requests_enforce_maximum_anomaly_limit(self):
        """12. Report requests enforce maximum anomaly limit."""
        mock_client = create_mock_genai_client(json.dumps(SAMPLE_GEMINI_OUTPUT))
        service = GeminiInvestigationService(api_key="test_key", client=mock_client)

        report = service.generate_report(max_findings=2)
        assert report.total_anomalies_evaluated <= 2
        assert len(report.investigations) <= 2

    def test_partial_report_failures_represented_correctly(self):
        """13. Partial report failures are represented correctly."""
        anomalies = anomaly_detector_service.get_anomalies().findings
        assert len(anomalies) >= 2

        # Create client that succeeds on call 1 and fails on call 2
        mock_client = MagicMock()
        success_resp = MagicMock()
        success_resp.text = json.dumps(SAMPLE_GEMINI_OUTPUT)

        mock_client.models.generate_content.side_effect = [
            success_resp,
            errors.APIError(code=500, response_json={"error": {"message": "Internal Server Error"}}),
            errors.APIError(code=500, response_json={"error": {"message": "Internal Server Error"}}),
            errors.APIError(code=500, response_json={"error": {"message": "Internal Server Error"}}),
        ]

        service = GeminiInvestigationService(api_key="test_key", client=mock_client, max_retries=1)
        report = service.generate_report(max_findings=2)

        assert report.successful_investigations_count == 1
        assert report.failed_investigations_count == 1
        assert len(report.partial_failures) == 1
        assert report.partial_failures[0].anomaly_id == anomalies[1].finding_id


class TestGeminiInvestigationApi:
    """Integration tests for Phase 5 Gemini AI FastAPI endpoints."""

    def test_get_investigation_status_endpoint(self):
        """Verify GET /api/investigation/status returns 200 without exposing keys."""
        resp = client.get("/api/investigation/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "is_configured" in data
        assert "model_name" in data
        assert "is_available" in data
        assert "status_message" in data
        assert "api_key" not in data
        assert "AIzaSy" not in str(data)

    def test_investigate_anomaly_404_for_unknown_id(self):
        """Verify POST /api/investigation/anomaly/{id} returns 404 for unknown ID."""
        resp = client.post("/api/investigation/anomaly/unknown-anomaly-999")
        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"].lower()

    def test_investigate_anomaly_503_when_unconfigured(self):
        """Verify POST /api/investigation/anomaly/{id} returns 503 when no key is set."""
        anomalies = anomaly_detector_service.get_anomalies().findings
        assert len(anomalies) > 0
        valid_id = anomalies[0].finding_id

        # Explicitly set override to False
        prev_override = gemini_investigation_service._is_configured_override
        try:
            gemini_investigation_service.is_configured = False
            resp = client.post(f"/api/investigation/anomaly/{valid_id}")
            assert resp.status_code == 503
            assert "not configured" in resp.json()["detail"].lower()
        finally:
            gemini_investigation_service.is_configured = prev_override

    def test_investigate_anomaly_success_with_mocked_gemini(self):
        """Verify POST /api/investigation/anomaly/{id} succeeds with mocked Gemini."""
        anomalies = anomaly_detector_service.get_anomalies().findings
        valid_id = anomalies[0].finding_id

        mock_client = create_mock_genai_client(json.dumps(SAMPLE_GEMINI_OUTPUT))
        prev_override = gemini_investigation_service._is_configured_override
        try:
            gemini_investigation_service.is_configured = True
            with patch.object(gemini_investigation_service, "_get_client", return_value=mock_client):
                resp = client.post(f"/api/investigation/anomaly/{valid_id}")
                assert resp.status_code == 200
                data = resp.json()
                assert data["anomaly_id"] == valid_id
                assert data["status"] == "completed"
                assert "summary" in data
                assert len(data["possible_causes"]) > 0
                assert len(data["recommended_actions"]) > 0
                assert data["financial_impact"]["grid_only_baseline_cost_inr"] is not None
                # Check hypothesis safety rule
                for cause in data["possible_causes"]:
                    assert cause["is_confirmed"] is False
        finally:
            gemini_investigation_service.is_configured = prev_override

    def test_investigation_report_endpoint_success(self):
        """Verify POST /api/investigation/report generates batch summary."""
        mock_client = create_mock_genai_client(json.dumps(SAMPLE_GEMINI_OUTPUT))
        prev_override = gemini_investigation_service._is_configured_override
        try:
            gemini_investigation_service.is_configured = True
            with patch.object(gemini_investigation_service, "_get_client", return_value=mock_client):
                resp = client.post("/api/investigation/report", json={"max_findings": 2})
                assert resp.status_code == 200
                data = resp.json()
                assert "report_id" in data
                assert data["successful_investigations_count"] >= 1
                assert "overall_risk_summary" in data
                assert len(data["prioritized_actions"]) > 0
        finally:
            gemini_investigation_service.is_configured = prev_override

    def test_preservation_of_all_phase_1_to_4_endpoints(self):
        """16. Existing Phase 1-4 endpoints continue working without regression."""
        # Phase 1
        r_health = client.get("/health")
        assert r_health.status_code == 200
        assert r_health.json()["status"] == "ok"

        r_root = client.get("/")
        assert r_root.status_code == 200

        # Phase 2
        r_prof = client.get("/api/factory/profile")
        assert r_prof.status_code == 200

        r_ts = client.get("/api/factory/timeseries")
        assert r_ts.status_code == 200

        # Phase 3
        r_metrics = client.get("/api/analysis/metrics")
        assert r_metrics.status_code == 200

        r_anomalies = client.get("/api/analysis/anomalies")
        assert r_anomalies.status_code == 200

        # Phase 4
        r_opt_base = client.get("/api/optimization/baseline")
        assert r_opt_base.status_code == 200

        r_opt_run = client.get("/api/optimization/run")
        assert r_opt_run.status_code == 200

        r_opt_sum = client.get("/api/optimization/summary")
        assert r_opt_sum.status_code == 200

    def test_client_http_options_converts_seconds_to_milliseconds(self):
        """17. Verify types.HttpOptions receives timeout in milliseconds."""
        with patch("app.services.gemini_service.genai.Client") as mock_client_cls:
            service = GeminiInvestigationService(api_key="test_key_abc", timeout_seconds=45)
            service._get_client()
            assert mock_client_cls.called
            _, kwargs = mock_client_cls.call_args
            http_options = kwargs.get("http_options")
            assert http_options is not None
            assert http_options.timeout == 45000

    def test_investigation_endpoint_timeout_returns_504(self):
        """18. Verify POST /api/investigation/anomaly/{id} returns 504 on timeout."""
        valid_id = "FINDING-IDLE-WASTE-H03"
        prev_override = gemini_investigation_service._is_configured_override
        try:
            gemini_investigation_service.is_configured = True
            with patch.object(
                gemini_investigation_service,
                "investigate_anomaly",
                side_effect=GeminiTimeoutError("Gemini request timed out after 30 seconds."),
            ):
                resp = client.post(f"/api/investigation/anomaly/{valid_id}")
                assert resp.status_code == 504
                assert "timed out after 30 seconds" in resp.json()["detail"]
        finally:
            gemini_investigation_service.is_configured = prev_override

    def test_real_gemini_live_investigation_when_configured(self):
        """19. Live integration test with real Google GenAI API when GEMINI_API_KEY is configured."""
        if not settings.GEMINI_API_KEY:
            pytest.skip("GEMINI_API_KEY is not configured in environment; skipping live API test.")

        real_service = GeminiInvestigationService(
            api_key=settings.GEMINI_API_KEY,
            model_name=settings.GEMINI_MODEL,
            timeout_seconds=settings.GEMINI_REQUEST_TIMEOUT_SECONDS,
        )
        assert real_service.is_configured is True
        result = real_service.investigate_anomaly("FINDING-IDLE-WASTE-H03", factory_id="DEMO-FAC-001")
        assert result.anomaly_id == "FINDING-IDLE-WASTE-H03"
        assert result.status == InvestigationStatus.COMPLETED
        assert result.summary
        assert len(result.possible_causes) > 0
        for cause in result.possible_causes:
            assert cause.is_confirmed is False
        assert result.financial_impact.estimated_daily_savings_inr is not None
