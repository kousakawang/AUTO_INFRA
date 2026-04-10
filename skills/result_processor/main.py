"""
Result Processor Skill - Main implementation.
Processes, aggregates, and filters benchmark results.
"""
import os
import sys
from typing import Dict, List, Optional

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from src.result_types import BenchmarkResult, ServiceResult, BenchmarkSuiteResult
from src.data_processor import (
    DataProcessor,
    ServiceCaseAggregatedResult,
    GroupResult,
    GroupKey
)


class ResultProcessorSkill:
    """
    Skill wrapper for result processing operations.
    """
    def __init__(self, data_watch_policy: str = "remove_min_max",
                 slo_ttft_max: float = 1e8, slo_tpot_max: float = 1e8):
        """
        Initialize the result processor.

        Args:
            data_watch_policy: Policy for handling outliers ("remove_min_max")
            slo_ttft_max: Maximum TTFT (ms) for SLO filtering
            slo_tpot_max: Maximum TPOT (ms) for SLO filtering
        """
        self.data_processor = DataProcessor(
            data_watch_policy=data_watch_policy,
            slo_ttft_max=slo_ttft_max,
            slo_tpot_max=slo_tpot_max
        )

    def filter_by_slo(self, results: List[BenchmarkResult]) -> List[BenchmarkResult]:
        """
        Filter results to only include those that meet SLO thresholds.

        Args:
            results: List of benchmark results to filter

        Returns:
            List of benchmark results that meet SLO criteria
        """
        return self.data_processor.filter_by_slo(results)

    def remove_outliers(self, results: List[BenchmarkResult]) -> List[BenchmarkResult]:
        """
        Remove outliers from the results based on data_watch_policy.

        Args:
            results: List of benchmark results to process

        Returns:
            List of benchmark results with outliers removed
        """
        return self.data_processor.remove_outliers(results)

    def aggregate_per_service_case(self, suite_result: BenchmarkSuiteResult,
                                    apply_slo_filter: bool = True,
                                    remove_outliers: bool = True) -> List[ServiceCaseAggregatedResult]:
        """
        Aggregate results per (service, case).

        Args:
            suite_result: The benchmark suite result to aggregate
            apply_slo_filter: Whether to apply SLO filtering
            remove_outliers: Whether to remove outliers

        Returns:
            List of ServiceCaseAggregatedResult, one per (service, case)
        """
        return self.data_processor.aggregate_per_service_case(
            suite_result, apply_slo_filter=apply_slo_filter, remove_outliers=remove_outliers
        )

    def group_results(self, aggregated_results: List[ServiceCaseAggregatedResult]) -> List[GroupResult]:
        """
        Group aggregated results by model, input_len, output_len, max_concurrency, etc.

        Args:
            aggregated_results: List of ServiceCaseAggregatedResult to group

        Returns:
            List of GroupResult, one per unique group
        """
        return self.data_processor.group_results(aggregated_results)


# Convenience functions with default processor
_default_processor: Optional[ResultProcessorSkill] = None


def _get_default_processor() -> ResultProcessorSkill:
    """Get or create the default processor instance."""
    global _default_processor
    if _default_processor is None:
        _default_processor = ResultProcessorSkill()
    return _default_processor


def filter_by_slo(results: List[BenchmarkResult], slo_ttft_max: float = 1e8,
                  slo_tpot_max: float = 1e8) -> List[BenchmarkResult]:
    """
    Filter results by SLO thresholds (convenience function).

    Args:
        results: List of benchmark results
        slo_ttft_max: Maximum TTFT in ms
        slo_tpot_max: Maximum TPOT in ms

    Returns:
        Filtered list of benchmark results
    """
    processor = ResultProcessorSkill(slo_ttft_max=slo_ttft_max, slo_tpot_max=slo_tpot_max)
    return processor.filter_by_slo(results)


def remove_outliers(results: List[BenchmarkResult],
                    data_watch_policy: str = "remove_min_max") -> List[BenchmarkResult]:
    """
    Remove outliers from results (convenience function).

    Args:
        results: List of benchmark results
        data_watch_policy: Policy for outlier removal

    Returns:
        List of benchmark results with outliers removed
    """
    processor = ResultProcessorSkill(data_watch_policy=data_watch_policy)
    return processor.remove_outliers(results)


def aggregate_per_service_case(suite_result: BenchmarkSuiteResult,
                                apply_slo_filter: bool = True,
                                remove_outliers_flag: bool = True,
                                data_watch_policy: str = "remove_min_max",
                                slo_ttft_max: float = 1e8,
                                slo_tpot_max: float = 1e8) -> List[ServiceCaseAggregatedResult]:
    """
    Aggregate results per (service, case) (convenience function).
    """
    processor = ResultProcessorSkill(
        data_watch_policy=data_watch_policy,
        slo_ttft_max=slo_ttft_max,
        slo_tpot_max=slo_tpot_max
    )
    return processor.aggregate_per_service_case(
        suite_result, apply_slo_filter=apply_slo_filter, remove_outliers=remove_outliers_flag
    )


def group_results(aggregated_results: List[ServiceCaseAggregatedResult]) -> List[GroupResult]:
    """
    Group aggregated results (convenience function).
    """
    processor = _get_default_processor()
    return processor.group_results(aggregated_results)
