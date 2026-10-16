"""Prompts package for GridMind AI."""

from app.prompts.energy_investigation import (
    SYSTEM_INVESTIGATION_INSTRUCTION,
    build_investigation_prompt,
    build_report_summary_prompt,
)

__all__ = [
    "SYSTEM_INVESTIGATION_INSTRUCTION",
    "build_investigation_prompt",
    "build_report_summary_prompt",
]
