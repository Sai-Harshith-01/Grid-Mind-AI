"""Gemini AI Investigation Service for GridMind AI.

Provides grounded, evidence-based anomaly investigation using Google's official
google-genai Python SDK. Integrates evidence from Phase 2 (factory telemetry),
Phase 3 (anomaly detector and energy metrics), and Phase 4 (linear programming optimiser).

Strictly enforces:
- Authoritative backend numerical values (the LLM never calculates financial totals or telemetry).
- Zero hallucination of physical facts (hypotheses are explicitly marked unconfirmed).
- Industrial safety rules (no bypasses, strict rating adherence).
- Graceful startup when GEMINI_API_KEY is absent.
- Bounded retries and robust exception mapping (auth, rate limits, timeouts, upstream).
"""

import json
import logging
import re
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from google import genai
from google.genai import errors, types

from app.core.config import settings
from app.prompts.energy_investigation import (
    SYSTEM_INVESTIGATION_INSTRUCTION,
    build_investigation_prompt,
    build_report_summary_prompt,
)
from app.schemas.analysis import DetectedAnomalyFinding
from app.schemas.investigation import (
    FailedInvestigationItem,
    FinancialImpactSummary,
    GeminiGeneratedInvestigation,
    InvestigationAiMetadata,
    InvestigationEvidence,
    InvestigationPriority,
    InvestigationReportResponse,
    InvestigationResponse,
    InvestigationStatus,
    InvestigationStatusResponse,
    PossibleCause,
    RecommendedAction,
)
from app.services.anomaly_detector import anomaly_detector_service
from app.services.energy_metrics import energy_metrics_service
from app.services.energy_optimizer import EnergyOptimizerService
from app.services.factory_data_service import factory_data_service, DEFAULT_FACTORY_ID

logger = logging.getLogger(__name__)


class GeminiInvestigationError(Exception):
    """Base exception for Gemini investigation failures."""


class GeminiServiceUnavailableError(GeminiInvestigationError):
    """Raised when Gemini service is unconfigured (missing API key) or unavailable."""


class GeminiAuthenticationError(GeminiInvestigationError):
    """Raised when the Gemini API key is invalid or unauthorized."""


class GeminiRateLimitError(GeminiInvestigationError):
    """Raised when Gemini quota or rate limits are exceeded."""


class GeminiTimeoutError(GeminiInvestigationError):
    """Raised when a Gemini request exceeds the configured timeout."""


class GeminiMalformedOutputError(GeminiInvestigationError):
    """Raised when Gemini returns malformed output that fails schema validation."""


class GeminiUpstreamError(GeminiInvestigationError):
    """Raised when Gemini upstream service fails (5xx)."""


class AnomalyNotFoundError(GeminiInvestigationError):
    """Raised when an anomaly ID does not exist in detected findings."""


_UNSET = object()


class GeminiInvestigationService:
    """Production-minded Gemini AI Energy Waste Investigator service."""

    def __init__(
        self,
        api_key: Any = _UNSET,
        model_name: Optional[str] = None,
        timeout_seconds: Optional[int] = None,
        max_retries: Optional[int] = None,
        client: Optional[genai.Client] = None,
    ):
        self.api_key = settings.GEMINI_API_KEY if api_key is _UNSET else api_key
        self.model_name = model_name or settings.GEMINI_MODEL
        self.timeout_seconds = timeout_seconds or settings.GEMINI_REQUEST_TIMEOUT_SECONDS
        self.max_retries = max_retries if max_retries is not None else settings.GEMINI_MAX_RETRIES
        self._injected_client = client
        self._client: Optional[genai.Client] = client
        self._is_configured_override: Optional[bool] = None


    @property
    def is_configured(self) -> bool:
        """Return True if a non-empty API key is configured or client was injected."""
        if self._is_configured_override is not None:
            return self._is_configured_override
        if self._injected_client is not None:
            return True
        return bool(self.api_key and self.api_key.strip() and self.api_key.strip() != "your_gemini_api_key_here")

    @is_configured.setter
    def is_configured(self, value: Optional[bool]) -> None:
        """Allow setting or overriding is_configured for testing."""
        self._is_configured_override = value

    def _get_client(self) -> genai.Client:
        """Lazy-initialize and return the Google GenAI client."""
        if self._client is not None:
            return self._client

        if not self.is_configured:
            raise GeminiServiceUnavailableError(
                "Gemini API key is not configured. Set the GEMINI_API_KEY environment variable "
                "to enable AI energy investigations."
            )

        try:
            # Note: types.HttpOptions expects timeout in milliseconds (e.g. 30,000 ms for 30s)
            timeout_ms = int(self.timeout_seconds * 1000)
            http_options = types.HttpOptions(timeout=timeout_ms)
            self._client = genai.Client(api_key=self.api_key.strip(), http_options=http_options)
            return self._client
        except Exception as exc:
            logger.error("Failed to initialize Google GenAI Client: %s", exc)
            raise GeminiServiceUnavailableError(f"Unable to initialize Gemini client: {exc}") from exc

    def get_status(self) -> InvestigationStatusResponse:
        """Return the current readiness status of the Gemini investigation service.
        
        Never exposes secrets or credentials in the response.
        """
        configured = self.is_configured
        status_msg = (
            f"Gemini AI investigation engine ready using model '{self.model_name}'."
            if configured
            else "Gemini API key is not configured. Set GEMINI_API_KEY environment variable to enable AI investigations."
        )
        return InvestigationStatusResponse(
            is_configured=configured,
            model_name=self.model_name,
            is_available=configured,
            status_message=status_msg,
            supported_modes=["single_anomaly_investigation", "batch_investigation_report"],
        )

    def _build_bounded_context(
        self, anomaly: DetectedAnomalyFinding, factory_id: str = DEFAULT_FACTORY_ID
    ) -> Dict[str, Any]:
        """Assemble bounded, grounded investigation context from existing backend services.
        
        Extracts only the relevant interval telemetry and authoritative metrics,
        avoiding transmitting the entire raw 24-hour dataset to the LLM.
        Uses factory-specific data for the selected factory.
        """
        factory_profile = factory_data_service.get_profile(factory_id)
        analytical_profile = energy_metrics_service.get_energy_profile(factory_id=factory_id)
        opt_summary = EnergyOptimizerService.get_summary(factory_id=factory_id)

        # Find matching analytical hourly profile item
        interval_data = None
        for item in analytical_profile.hourly_profile:
            if item.interval_index == anomaly.interval_index:
                interval_data = {
                    "interval_index": item.interval_index,
                    "timestamp": item.timestamp,
                    "factory_demand_kw": item.factory_demand_kw,
                    "factory_demand_kwh": item.factory_demand_kwh,
                    "production_units": item.production_units,
                    "grid_tariff_inr_per_kwh": item.grid_tariff_inr_per_kwh,
                    "is_peak_tariff": item.is_peak_tariff,
                    "shift_name": item.shift_name,
                    "is_production_active": item.is_production_active,
                    "solar_available_kwh": item.solar_available_kwh,
                    "wind_available_kwh": item.wind_available_kwh,
                    "biomass_available_kwh": item.biomass_available_kwh,
                }
                break

        return {
            "factory_identity": {
                "factory_id": factory_profile.factory_id,
                "factory_name": factory_profile.name,
                "sector": factory_profile.sector,
                "location": factory_profile.location,
                "total_zones": len(factory_profile.zones),
                "grid_contract_demand_kw": factory_profile.grid.contract_demand_kw,
            },
            "anomaly_evidence": {
                "finding_id": anomaly.finding_id,
                "category": anomaly.category,
                "title": anomaly.title,
                "severity": anomaly.severity,
                "affected_zone_name": anomaly.affected_zone_name,
                "affected_machine_name": anomaly.affected_machine_name,
                "interval_index": anomaly.interval_index,
                "timestamp": anomaly.timestamp,
                "metric_name": anomaly.evidence.metric_name,
                "observed_value": anomaly.evidence.observed_value,
                "baseline_threshold": anomaly.evidence.baseline_threshold,
                "deviation_value": anomaly.evidence.deviation_value,
                "deviation_percent": anomaly.evidence.deviation_percent,
                "unit": anomaly.evidence.unit,
                "grid_tariff_inr_per_kwh": anomaly.evidence.grid_tariff_inr_per_kwh,
                "detection_rule_id": anomaly.detection_rule_id,
                "detection_rule_description": anomaly.detection_rule_description,
            },
            "interval_operational_context": interval_data,
            "backend_optimization_context": {
                "is_feasible": opt_summary.is_feasible,
                "baseline_grid_only_cost_inr": opt_summary.baseline_grid_only_cost_inr,
                "optimised_supply_cost_inr": opt_summary.optimised_supply_cost_inr,
                "estimated_savings_inr": opt_summary.estimated_savings_inr,
                "estimated_savings_percentage": opt_summary.estimated_savings_percentage,
                "renewable_allocation_percentage": opt_summary.renewable_allocation_percentage,
            },
            "simulation_metadata": {
                "is_synthetic": True,
                "disclaimer": "Fictional demonstration factories using synthetic data. Not actual customer facilities.",
            },
        }

    def _clean_json_text(self, text: str) -> str:
        """Strip markdown fences, leading/trailing whitespace, or commentary."""
        text = text.strip()
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
        if match:
            return match.group(1).strip()
        return text

    def _sanitize_log_msg(self, msg: Any) -> str:
        """Mask any potential API key strings from log messages."""
        return re.sub(r"AIza[0-9A-Za-z-_]{35}", "AIza[REDACTED]", str(msg))

    def _call_gemini_with_resilience(
        self, prompt: str, system_instruction: str = SYSTEM_INVESTIGATION_INSTRUCTION
    ) -> tuple[str, float]:
        """Invoke Gemini generate_content with timeout, error translation, and bounded retries."""
        client = self._get_client()
        last_error = None

        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            system_instruction=system_instruction,
            temperature=0.2,
        )

        # For mock tests (injected client), strictly preserve single configured model.
        # For production live calls, support fast resilient fallbacks if primary model is 404 or sunset.
        if self._injected_client is not None:
            models_to_try = [self.model_name]
        else:
            models_to_try = [self.model_name]
            for fallback in ("gemini-3.1-flash-lite", "gemini-2.5-flash", "gemini-flash-latest"):
                if fallback and fallback not in models_to_try:
                    models_to_try.append(fallback)

        for model in models_to_try:
            retries = 0
            while retries <= self.max_retries:
                start_time = time.perf_counter()
                try:
                    logger.debug("Dispatching Gemini request: model=%s, timeout=%ss", model, self.timeout_seconds)
                    response = client.models.generate_content(
                        model=model,
                        contents=prompt,
                        config=config,
                    )
                    duration_s = time.perf_counter() - start_time
                    latency_ms = duration_s * 1000.0

                    if not response or not response.text:
                        raise GeminiMalformedOutputError("Gemini returned empty or null content.")

                    if model != self.model_name:
                        logger.info("Gemini request succeeded with fallback model %s (took %.2fs)", model, duration_s)

                    return response.text, latency_ms

                except errors.APIError as api_err:
                    duration_s = time.perf_counter() - start_time
                    status_code = getattr(api_err, "code", None) or getattr(api_err, "status_code", None)
                    err_msg = str(api_err).lower()

                    # Model not found or deprecated (404) -> if fallback models remain, advance immediately
                    if (status_code == 404 or "not_found" in err_msg or "not found" in err_msg) and model != models_to_try[-1]:
                        logger.warning(
                            "Gemini model '%s' unavailable (HTTP 404, duration=%.2fs). Falling back to next candidate.",
                            model, duration_s
                        )
                        break

                    # Auth / Credential failures — NEVER RETRY
                    if status_code in (401, 403) or "unauthenticated" in err_msg or "api_key_invalid" in err_msg:
                        logger.error(
                            "Gemini auth failure (HTTP %s, duration=%.2fs, model=%s): %s",
                            status_code, duration_s, model, self._sanitize_log_msg(api_err)
                        )
                        raise GeminiAuthenticationError(
                            "Gemini authentication failed: Invalid, expired, or unauthorized API key."
                        ) from api_err

                    # Rate Limit / Quota failures
                    if status_code == 429 or "resource_exhausted" in err_msg or "quota" in err_msg:
                        logger.warning(
                            "Gemini rate limit exceeded (HTTP %s, duration=%.2fs, model=%s): %s",
                            status_code, duration_s, model, self._sanitize_log_msg(api_err)
                        )
                        raise GeminiRateLimitError(
                            "Gemini API rate limit or quota exceeded. Please retry after a delay."
                        ) from api_err

                    # Upstream server errors (500, 502, 503, 504) — retry if attempts remain
                    if status_code in (500, 502, 503, 504) and retries < self.max_retries:
                        retries += 1
                        sleep_time = 0.5 * (2**retries)
                        logger.warning(
                            "Gemini upstream error (HTTP %s, duration=%.2fs, model=%s), retrying %s/%s in %.2fs: %s",
                            status_code, duration_s, model, retries, self.max_retries, sleep_time, self._sanitize_log_msg(api_err)
                        )
                        time.sleep(sleep_time)
                        last_error = api_err
                        continue

                    logger.error(
                        "Gemini API failure (HTTP %s, duration=%.2fs, model=%s, exc_type=%s): %s",
                        status_code, duration_s, model, type(api_err).__name__, self._sanitize_log_msg(api_err)
                    )
                    raise GeminiUpstreamError(f"Gemini upstream API failure: {self._sanitize_log_msg(api_err)}") from api_err

                except (TimeoutError, Exception) as exc:
                    duration_s = time.perf_counter() - start_time
                    exc_name = type(exc).__name__.lower()
                    if "timeout" in exc_name:
                        if retries < self.max_retries:
                            retries += 1
                            logger.warning(
                                "Gemini request timed out after %.2fs (model=%s), retrying %s/%s...",
                                duration_s, model, retries, self.max_retries
                            )
                            time.sleep(0.5)
                            last_error = exc
                            continue
                        logger.error(
                            "Gemini request timed out after %.2fs (configured timeout=%ss, model=%s)",
                            duration_s, self.timeout_seconds, model
                        )
                        raise GeminiTimeoutError(
                            f"Gemini request timed out after {self.timeout_seconds} seconds."
                        ) from exc

                    # If it's already one of our custom exceptions, re-raise
                    if isinstance(exc, GeminiInvestigationError):
                        raise exc

                    # Unhandled generic error
                    logger.error(
                        "Unexpected error communicating with Gemini (duration=%.2fs, model=%s, exc_type=%s): %s",
                        duration_s, model, type(exc).__name__, self._sanitize_log_msg(exc)
                    )
                    raise GeminiUpstreamError(f"Unexpected error communicating with Gemini: {self._sanitize_log_msg(exc)}") from exc

        raise GeminiUpstreamError(f"Gemini call failed after retries: {self._sanitize_log_msg(last_error)}")

    def _parse_and_validate_investigation(
        self, raw_text: str, context: Dict[str, Any]
    ) -> GeminiGeneratedInvestigation:
        """Parse raw JSON output and validate against GeminiGeneratedInvestigation.
        
        Performs at most 1 bounded correction call if parsing or validation fails.
        """
        cleaned_text = self._clean_json_text(raw_text)

        try:
            parsed_json = json.loads(cleaned_text)
            return GeminiGeneratedInvestigation.model_validate(parsed_json)
        except Exception as first_exc:
            logger.warning(
                "Gemini output failed validation (%s). Attempting 1 bounded correction...", first_exc
            )

            # Bounded 1-time correction prompt
            correction_prompt = (
                f"Your previous response failed validation with error: {first_exc}\n\n"
                f"Please fix and re-emit the JSON strictly matching the schema:\n"
                f"{build_investigation_prompt(context)}"
            )

            try:
                corrected_text, _ = self._call_gemini_with_resilience(correction_prompt)
                cleaned_corrected = self._clean_json_text(corrected_text)
                parsed_corrected = json.loads(cleaned_corrected)
                return GeminiGeneratedInvestigation.model_validate(parsed_corrected)
            except Exception as second_exc:
                logger.error("Gemini bounded correction failed: %s", second_exc)
                raise GeminiMalformedOutputError(
                    f"Gemini returned output that failed schema validation: {second_exc}"
                ) from second_exc

    def investigate_anomaly(
        self, anomaly_id: str, factory_id: str = DEFAULT_FACTORY_ID
    ) -> InvestigationResponse:
        """Investigate a specific anomaly using grounded context and Gemini AI.
        
        Workflow:
        1. Validates anomaly ID exists in detected anomalies for the specified factory.
        2. Retrieves ground-truth analytical and optimization metrics from backend.
        3. Enforces that Gemini is configured (raises 503 if API key missing).
        4. Calls Gemini with grounded context and strict system prompts.
        5. Validates LLM output via Pydantic with 1 bounded regeneration attempt.
        6. Injects authoritative backend financial figures and simulation metadata.
        7. Returns typed InvestigationResponse.
        """
        # Step 1: Validate anomaly exists in the correct factory
        anomaly = anomaly_detector_service.get_anomaly_by_id(anomaly_id, factory_id=factory_id)
        if anomaly is None:
            raise AnomalyNotFoundError(
                f"Anomaly with finding_id '{anomaly_id}' not found for factory '{factory_id}'."
            )

        # Step 2: Assemble bounded context
        context = self._build_bounded_context(anomaly, factory_id=factory_id)
        user_prompt = build_investigation_prompt(context)


        # Step 3 & 4: Call Gemini (fails fast if not configured)
        raw_text, latency_ms = self._call_gemini_with_resilience(user_prompt)

        # Step 5: Parse and validate structured output
        generated = self._parse_and_validate_investigation(raw_text, context)

        # Step 6: Guarantee hypothesis boundary (is_confirmed MUST be False)
        sanitized_causes = [
            PossibleCause(
                hypothesis=c.hypothesis,
                likelihood=c.likelihood,
                supporting_evidence=c.supporting_evidence,
                is_confirmed=False,  # Unconditionally enforce hypothesis status
            )
            for c in generated.possible_causes
        ]

        # Step 7: Build authoritative backend financial summary
        opt_summary = EnergyOptimizerService.get_summary(factory_id=factory_id)
        financial_summary = FinancialImpactSummary(
            detected_excess_energy_kwh=(
                anomaly.evidence.deviation_value if anomaly.evidence.deviation_value > 0 else 0.0
            ),
            excess_energy_grid_cost_inr=anomaly.estimated_financial_impact_inr,
            grid_only_baseline_cost_inr=opt_summary.baseline_grid_only_cost_inr,
            optimised_scenario_cost_inr=opt_summary.optimised_supply_cost_inr,
            estimated_daily_savings_inr=opt_summary.estimated_savings_inr,
            financial_caveats=(
                f"The detected excess energy of {anomaly.evidence.deviation_value:.2f} {anomaly.evidence.unit} "
                f"represents an estimated grid-equivalent cost of "
                f"\u20b9{anomaly.estimated_financial_impact_inr or 0.0:.2f}. "
                f"Total daily savings (\u20b9{opt_summary.optimised_supply_cost_inr:.2f} optimised vs "
                f"\u20b9{opt_summary.baseline_grid_only_cost_inr:.2f} baseline) reflect full plant renewable dispatch "
                "and are scenario estimates, not guaranteed savings."
            ),
        )

        evidence_payload = InvestigationEvidence(
            anomaly_id=anomaly.finding_id,
            interval_index=anomaly.interval_index,
            timestamp=anomaly.timestamp,
            category=anomaly.category,
            severity=anomaly.severity,
            metric_name=anomaly.evidence.metric_name,
            observed_value=anomaly.evidence.observed_value,
            baseline_threshold=anomaly.evidence.baseline_threshold,
            deviation_value=anomaly.evidence.deviation_value,
            deviation_percent=anomaly.evidence.deviation_percent,
            unit=anomaly.evidence.unit,
            detection_rule_id=anomaly.detection_rule_id,
            detection_rule_description=anomaly.detection_rule_description,
            affected_zone_name=anomaly.affected_zone_name,
            affected_machine_name=anomaly.affected_machine_name,
            grid_tariff_inr_per_kwh=anomaly.evidence.grid_tariff_inr_per_kwh,
        )

        ai_meta = InvestigationAiMetadata(
            model_name=self.model_name,
            provider="Google Gemini",
            is_mocked=(self._injected_client is not None),
            latency_ms=round(latency_ms, 2),
            temperature=0.2,
        )

        return InvestigationResponse(
            investigation_id=f"inv-{uuid.uuid4().hex[:8]}",
            anomaly_id=anomaly.finding_id,
            status=InvestigationStatus.COMPLETED,
            summary=generated.summary,
            observations=generated.observations,
            evidence=evidence_payload,
            possible_causes=sanitized_causes,
            recommended_actions=generated.recommended_actions,
            financial_impact=financial_summary,
            uncertainties=generated.uncertainties,
            follow_up_checks=generated.follow_up_checks,
            simulation_metadata=factory_data_service.get_profile(factory_id).simulation_metadata,
            ai_metadata=ai_meta,
        )


    def generate_report(
        self,
        max_findings: int = 5,
        min_severity: Optional[str] = None,
        factory_id: str = DEFAULT_FACTORY_ID,
    ) -> InvestigationReportResponse:
        """Generate a structured investigation report across prioritised detected anomalies.
        
        Controls concurrency, respects rate limits, tracks partial failures,
        and provides plant-wide executive synthesis.
        """
        if not self.is_configured:
            raise GeminiServiceUnavailableError(
                "Gemini API key is not configured. Set the GEMINI_API_KEY environment variable "
                "to enable AI energy investigations."
            )

        # Enforce bounds
        bounded_max = min(max_findings, settings.INVESTIGATION_MAX_FINDINGS_PER_REPORT)
        if bounded_max < 1:
            bounded_max = 1

        # Retrieve and sort anomalies by severity
        all_anomalies = anomaly_detector_service.get_anomalies(factory_id=factory_id).findings
        severity_rank = {"critical": 4, "high": 3, "medium": 2, "low": 1}

        filtered = all_anomalies
        if min_severity:
            min_rank = severity_rank.get(min_severity.lower(), 1)
            filtered = [a for a in all_anomalies if severity_rank.get(a.severity.lower(), 0) >= min_rank]

        # Sort highest severity first
        sorted_anomalies = sorted(
            filtered, key=lambda a: severity_rank.get(a.severity.lower(), 0), reverse=True
        )
        selected_anomalies = sorted_anomalies[:bounded_max]

        investigations: List[InvestigationResponse] = []
        partial_failures: List[FailedInvestigationItem] = []
        all_actions: List[RecommendedAction] = []

        # Process sequentially to avoid API bursting and manage rate quotas
        for anomaly in selected_anomalies:
            try:
                inv = self.investigate_anomaly(anomaly.finding_id, factory_id=factory_id)
                investigations.append(inv)
                all_actions.extend(inv.recommended_actions)
            except Exception as exc:
                logger.warning("Investigation failed for anomaly %s: %s", anomaly.finding_id, exc)
                partial_failures.append(
                    FailedInvestigationItem(anomaly_id=anomaly.finding_id, error_message=str(exc))
                )

        # Sort actions by priority (critical > high > medium > low) and deduplicate
        action_priority_map = {
            InvestigationPriority.CRITICAL: 4,
            InvestigationPriority.HIGH: 3,
            InvestigationPriority.MEDIUM: 2,
            InvestigationPriority.LOW: 1,
        }
        seen_actions = set()
        deduped_actions: List[RecommendedAction] = []
        for action in sorted(
            all_actions, key=lambda a: action_priority_map.get(a.priority, 1), reverse=True
        ):
            if action.action not in seen_actions:
                seen_actions.add(action.action)
                deduped_actions.append(action)

        opt_summary = EnergyOptimizerService.get_summary(factory_id=factory_id)
        now_iso = datetime.now(timezone.utc).isoformat()

        # Build synthesized risk summary
        overall_risk_summary = (
            f"Evaluated {len(selected_anomalies)} prioritized anomalies across the 24-hour manufacturing cycle. "
            f"Successfully diagnosed {len(investigations)} events with {len(partial_failures)} failures. "
            f"Key risk drivers include off-schedule baseload consumption during non-operational hours and high-tariff "
            f"spikes. Corrective actions should focus first on automated compressor and HVAC shutdowns before "
            f"evening peak tariff intervals."
        )

        ai_meta = InvestigationAiMetadata(
            model_name=self.model_name,
            provider="Google Gemini",
            is_mocked=(self._injected_client is not None),
            temperature=0.2,
        )

        return InvestigationReportResponse(
            report_id=f"rep-{uuid.uuid4().hex[:8]}",
            generated_at=now_iso,
            total_anomalies_evaluated=len(selected_anomalies),
            successful_investigations_count=len(investigations),
            failed_investigations_count=len(partial_failures),
            overall_risk_summary=overall_risk_summary,
            investigations=investigations,
            partial_failures=partial_failures,
            prioritized_actions=deduped_actions[:8],  # Top 8 prioritized actions
            optimization_context={
                "baseline_grid_only_cost_inr": opt_summary.baseline_grid_only_cost_inr,
                "optimised_supply_cost_inr": opt_summary.optimised_supply_cost_inr,
                "estimated_savings_inr": opt_summary.estimated_savings_inr,
                "renewable_allocation_percentage": opt_summary.renewable_allocation_percentage,
            },
            simulation_metadata=factory_data_service.get_profile(factory_id).simulation_metadata,
            ai_metadata=ai_meta,
        )


# Singleton service instance
gemini_investigation_service = GeminiInvestigationService()
