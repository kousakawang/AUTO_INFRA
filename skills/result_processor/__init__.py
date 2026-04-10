"""
Result Processor Skill - Process and aggregate benchmark results.
"""
from .main import (
    ResultProcessorSkill,
    filter_by_slo,
    remove_outliers,
    aggregate_per_service_case,
    group_results,
    ServiceCaseAggregatedResult,
    GroupResult,
    GroupKey
)

__all__ = [
    "ResultProcessorSkill",
    "filter_by_slo",
    "remove_outliers",
    "aggregate_per_service_case",
    "group_results",
    "ServiceCaseAggregatedResult",
    "GroupResult",
    "GroupKey"
]
