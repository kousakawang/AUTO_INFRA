"""
Data Processor - Handles result aggregation, outlier removal, and SLO filtering.
"""
import statistics
import logging
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field

from .result_types import BenchmarkResult, ServiceResult, BenchmarkSuiteResult

logger = logging.getLogger(__name__)


@dataclass
class ServiceCaseAggregatedResult:
    """Aggregated result for a single benchmark case on a single service."""
    service_global_id: int
    case_id: int
    model_path: str
    input_len: Optional[int]
    output_len: Optional[int]
    max_concurrency: Optional[int]
    image_size: Optional[str]
    image_count: Optional[int]
    deploy_method: Optional[str]
    template_id: Optional[int]
    env_opt_ids: Optional[List[int]] = field(default_factory=list)
    server_args_opt_ids: Optional[List[int]] = field(default_factory=list)
    additional_options: Optional[List[str]] = field(default_factory=list)

    # Aggregated metrics
    num_runs: int = 0
    avg_total_token_throughput: float = 0.0
    is_per_device_throughput: bool = False
    tensor_parallel_degree: int = 1
    avg_request_throughput: float = 0.0
    avg_input_token_throughput: float = 0.0
    avg_output_token_throughput: float = 0.0
    avg_mean_ttft_ms: float = 0.0
    avg_mean_tpot_ms: float = 0.0

    # Individual runs (for reference)
    individual_runs: List[BenchmarkResult] = field(default_factory=list)


@dataclass
class GroupKey:
    """Key for grouping results."""
    model_path: str
    input_len: Optional[int]
    output_len: Optional[int]
    max_concurrency: Optional[int]
    image_size: Optional[str]
    image_count: Optional[int]
    template_id: Optional[int]
    deploy_method: Optional[str]

    def __hash__(self):
        return hash((
            self.model_path,
            self.input_len,
            self.output_len,
            self.max_concurrency,
            self.image_size,
            self.image_count,
            self.template_id,
            self.deploy_method,
        ))

    def __eq__(self, other):
        if not isinstance(other, GroupKey):
            return False
        return (
            self.model_path == other.model_path and
            self.input_len == other.input_len and
            self.output_len == other.output_len and
            self.max_concurrency == other.max_concurrency and
            self.image_size == other.image_size and
            self.image_count == other.image_count and
            self.template_id == other.template_id and
            self.deploy_method == other.deploy_method
        )


@dataclass
class GroupResult:
    """Result for a single group."""
    group_key: GroupKey
    service_case_results: List[ServiceCaseAggregatedResult] = field(default_factory=list)


def parse_tensor_parallel_degree(deploy_method: Optional[str]) -> int:
    """Parse tensor parallelism degree from deploy_method string (e.g., 'tp2' -> 2)."""
    if not deploy_method:
        return 1
    match = re.match(r'tp(\d+)', deploy_method.lower())
    if match:
        return int(match.group(1))
    return 1


class DataProcessor:
    """
    Processes and aggregates benchmark results.

    Handles:
    - Per-case aggregation: for each (service, case), aggregate per_config_benchmark_times runs
    - Outlier removal (remove_min_max policy)
    - SLO filtering (TTFT and TPOT thresholds)
    - Per-device throughput calculation for tp>1
    - Grouping by model, config, template_id, and deploy_method
    """

    def __init__(
        self,
        data_watch_policy: str = "remove_min_max",
        slo_ttft_max: float = 1e8,
        slo_tpot_max: float = 1e8,
    ):
        self.data_watch_policy = data_watch_policy
        self.slo_ttft_max = slo_ttft_max
        self.slo_tpot_max = slo_tpot_max

    def filter_by_slo(self, results: List[BenchmarkResult]) -> List[BenchmarkResult]:
        """
        Filter results to only include those that meet SLO thresholds.

        Args:
            results: List of benchmark results to filter

        Returns:
            List of benchmark results that meet SLO criteria
        """
        filtered = []
        for result in results:
            if not result.success:
                continue

            # Check if TTFT and TPOT are within SLO limits
            ttft_ok = result.mean_ttft_ms <= self.slo_ttft_max
            tpot_ok = result.mean_tpot_ms <= self.slo_tpot_max

            if ttft_ok and tpot_ok:
                filtered.append(result)
            else:
                logger.debug(
                    f"Result excluded by SLO: TTFT={result.mean_ttft_ms:.2f}ms (limit: {self.slo_ttft_max}), "
                    f"TPOT={result.mean_tpot_ms:.2f}ms (limit: {self.slo_tpot_max})"
                )

        logger.info(f"Filtered {len(results)} results to {len(filtered)} that meet SLO criteria")
        return filtered

    def remove_outliers(self, results: List[BenchmarkResult]) -> List[BenchmarkResult]:
        """
        Remove outliers from the results based on the data_watch_policy.

        For "remove_min_max" policy: removes the min and max total_token_throughput values.
        If there are 3 or fewer results, no removal is done.

        Args:
            results: List of benchmark results to process

        Returns:
            List of benchmark results with outliers removed
        """
        if self.data_watch_policy != "remove_min_max":
            logger.warning(f"Unknown data_watch_policy: {self.data_watch_policy}, using remove_min_max")

        if len(results) <= 3:
            logger.debug(f"Not removing outliers: only {len(results)} results (needs > 3)")
            return results

        # Sort by total_token_throughput
        sorted_results = sorted(results, key=lambda r: r.total_token_throughput)

        # Remove min and max
        filtered = sorted_results[1:-1]

        logger.info(
            f"Removed outliers: kept {len(filtered)} of {len(results)} results "
            f"(removed min={sorted_results[0].total_token_throughput:.2f}, "
            f"max={sorted_results[-1].total_token_throughput:.2f})"
        )

        return filtered

    def aggregate_per_service_case(
        self,
        suite_result: BenchmarkSuiteResult,
        apply_slo_filter: bool = True,
        remove_outliers: bool = True,
    ) -> List[ServiceCaseAggregatedResult]:
        """
        Aggregate results per (service, case).

        For each service and benchmark case:
        - Collect all per_config_benchmark_times runs
        - Apply SLO filter
        - Remove outliers (min/max)
        - Calculate average of remaining results
        - Calculate per-device throughput if tp>1

        Args:
            suite_result: The benchmark suite result to aggregate
            apply_slo_filter: Whether to apply SLO filtering
            remove_outliers: Whether to remove outliers

        Returns:
            List of ServiceCaseAggregatedResult, one per (service, case)
        """
        aggregated_results: List[ServiceCaseAggregatedResult] = []

        for service_result in suite_result.service_results:
            # Group results by case_id within this service
            cases: Dict[int, List[BenchmarkResult]] = {}
            for result in service_result.results:
                case_id = result.case_id
                if case_id not in cases:
                    cases[case_id] = []
                cases[case_id].append(result)

            # Process each case
            for case_id, case_results in cases.items():
                # Filter to only successful results
                successful_results = [r for r in case_results if r.success]

                if not successful_results:
                    logger.warning(f"No successful results for service {service_result.service_global_id}, case {case_id}")
                    continue

                # Apply SLO filter
                results_to_process = successful_results
                if apply_slo_filter:
                    results_to_process = self.filter_by_slo(results_to_process)

                if not results_to_process:
                    logger.warning(f"No results left after SLO filter for service {service_result.service_global_id}, case {case_id}")
                    continue

                # Remove outliers
                final_results = results_to_process
                if remove_outliers:
                    final_results = self.remove_outliers(results_to_process)

                if not final_results:
                    logger.warning(f"No results left after outlier removal for service {service_result.service_global_id}, case {case_id}")
                    continue

                # Get first result for metadata
                first_result = final_results[0]

                # Calculate tensor parallel degree
                tp_degree = 1
                if first_result.deploy_method:
                    tp_degree = parse_tensor_parallel_degree(first_result.deploy_method)

                is_per_device = tp_degree > 1

                # Calculate metrics
                throughputs = []
                for r in final_results:
                    tp = r.total_token_throughput
                    if is_per_device:
                        tp = tp / tp_degree
                    throughputs.append(tp)

                request_throughputs = [r.request_throughput for r in final_results]
                input_throughputs = [r.input_token_throughput for r in final_results]
                output_throughputs = [r.output_token_throughput for r in final_results]
                ttfts = [r.mean_ttft_ms for r in final_results]
                tpots = [r.mean_tpot_ms for r in final_results]

                agg = ServiceCaseAggregatedResult(
                    service_global_id=service_result.service_global_id,
                    case_id=case_id,
                    model_path=service_result.model_path,
                    input_len=first_result.input_len,
                    output_len=first_result.output_len,
                    max_concurrency=first_result.max_concurrency,
                    image_size=first_result.image_size,
                    image_count=first_result.image_count,
                    deploy_method=first_result.deploy_method,
                    template_id=first_result.template_id,
                    env_opt_ids=first_result.env_opt_ids if first_result.env_opt_ids else [],
                    server_args_opt_ids=first_result.server_args_opt_ids if first_result.server_args_opt_ids else [],
                    additional_options=first_result.additional_options if first_result.additional_options else [],
                    num_runs=len(final_results),
                    avg_total_token_throughput=statistics.mean(throughputs),
                    is_per_device_throughput=is_per_device,
                    tensor_parallel_degree=tp_degree,
                    avg_request_throughput=statistics.mean(request_throughputs),
                    avg_input_token_throughput=statistics.mean(input_throughputs),
                    avg_output_token_throughput=statistics.mean(output_throughputs),
                    avg_mean_ttft_ms=statistics.mean(ttfts),
                    avg_mean_tpot_ms=statistics.mean(tpots),
                    individual_runs=case_results,  # Keep all original runs
                )

                aggregated_results.append(agg)

        logger.info(f"Generated {len(aggregated_results)} service-case aggregated results")
        return aggregated_results

    def group_results(
        self,
        aggregated_results: List[ServiceCaseAggregatedResult],
    ) -> List[GroupResult]:
        """
        Group aggregated results by model, input_len, output_len, max_concurrency,
        image_size, image_count, template_id, and deploy_method.

        Args:
            aggregated_results: List of ServiceCaseAggregatedResult to group

        Returns:
            List of GroupResult, one per unique group
        """
        groups: Dict[GroupKey, GroupResult] = {}

        for agg_result in aggregated_results:
            group_key = GroupKey(
                model_path=agg_result.model_path,
                input_len=agg_result.input_len,
                output_len=agg_result.output_len,
                max_concurrency=agg_result.max_concurrency,
                image_size=agg_result.image_size,
                image_count=agg_result.image_count,
                template_id=agg_result.template_id,
                deploy_method=agg_result.deploy_method,
            )

            if group_key not in groups:
                groups[group_key] = GroupResult(group_key=group_key)

            groups[group_key].service_case_results.append(agg_result)

        # Convert to list and sort
        group_results = list(groups.values())
        group_results.sort(key=lambda g: (
            g.group_key.model_path,
            g.group_key.template_id,
            g.group_key.deploy_method,
            g.group_key.input_len,
            g.group_key.output_len,
            g.group_key.max_concurrency,
        ))

        logger.info(f"Grouped {len(aggregated_results)} results into {len(group_results)} groups")
        return group_results
