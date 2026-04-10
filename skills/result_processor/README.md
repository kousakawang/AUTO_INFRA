# result_processor Skill

Process, filter, and aggregate benchmark results.

## Purpose
This skill processes benchmark results. Use this when you need to:
- Filter results by SLO (Service Level Objective) thresholds
- Remove outliers (min/max values)
- Aggregate multiple runs per (service, case)
- Group results for comparison

## Key Class: `ResultProcessorSkill`

### `ResultProcessorSkill(data_watch_policy: str = "remove_min_max", slo_ttft_max: float = 1e8, slo_tpot_max: float = 1e8)`
Main skill class for result processing.

**Args:**
- `data_watch_policy`: Policy for handling outliers ("remove_min_max")
- `slo_ttft_max`: Maximum TTFT (ms) for SLO filtering
- `slo_tpot_max`: Maximum TPOT (ms) for SLO filtering

**Methods:**

---

#### `.filter_by_slo(results: List[BenchmarkResult]) -> List[BenchmarkResult]`
Filter results to only include those that meet SLO thresholds.

**Args:**
- `results`: List of benchmark results to filter

**Returns:**
- List of benchmark results that meet SLO criteria (TTFT <= slo_ttft_max AND TPOT <= slo_tpot_max)

**Example:**
```python
from skills.result_processor import ResultProcessorSkill

processor = ResultProcessorSkill(slo_ttft_max=100.0, slo_tpot_max=20.0)
filtered = processor.filter_by_slo(all_results)
print(f"Kept {len(filtered)}/{len(all_results)} results within SLO")
```

---

#### `.remove_outliers(results: List[BenchmarkResult]) -> List[BenchmarkResult]`
Remove outliers from the results based on data_watch_policy.

For "remove_min_max" policy: removes the min and max total_token_throughput values. If there are 3 or fewer results, no removal is done.

**Returns:**
- List of benchmark results with outliers removed

---

#### `.aggregate_per_service_case(suite_result: BenchmarkSuiteResult, apply_slo_filter: bool = True, remove_outliers: bool = True) -> List[ServiceCaseAggregatedResult]`
Aggregate results per (service, case).

For each service and benchmark case:
- Collect all per_config_benchmark_times runs
- Apply SLO filter (optional)
- Remove outliers (optional)
- Calculate average of remaining results
- Calculate per-device throughput if tensor parallelism > 1

**Returns:**
- List of `ServiceCaseAggregatedResult`, one per (service, case)

---

#### `.group_results(aggregated_results: List[ServiceCaseAggregatedResult]) -> List[GroupResult]`
Group aggregated results by model, input_len, output_len, max_concurrency, image_size, image_count, template_id, and deploy_method.

**Returns:**
- List of `GroupResult`, one per unique group

---

## Convenience Functions (Global)

These functions use default settings:

- `filter_by_slo(results, slo_ttft_max=1e8, slo_tpot_max=1e8)`
- `remove_outliers(results, data_watch_policy="remove_min_max")`
- `aggregate_per_service_case(suite_result, ...)`
- `group_results(aggregated_results)`

## Example Usage

```python
from skills.result_processor import ResultProcessorSkill

# Initialize with SLO thresholds
processor = ResultProcessorSkill(
    data_watch_policy="remove_min_max",
    slo_ttft_max=100.0,
    slo_tpot_max=20.0
)

# Aggregate results from a suite
aggregated = processor.aggregate_per_service_case(suite_result)

# Group for comparison
groups = processor.group_results(aggregated)

# Print results
for group in groups:
    key = group.group_key
    print(f"\n{key.model_path}, concurrency={key.max_concurrency}")
    for agg in group.service_case_results:
        print(f"  Throughput: {agg.avg_total_token_throughput:.2f} tok/s")
        print(f"  TTFT: {agg.avg_mean_ttft_ms:.2f} ms")
        print(f"  TPOT: {agg.avg_mean_tpot_ms:.2f} ms")
```

## ServiceCaseAggregatedResult Fields
Each aggregated result contains:
- `.avg_total_token_throughput` - Average total token throughput
- `.avg_request_throughput` - Average request throughput
- `.avg_mean_ttft_ms` - Average TTFT
- `.avg_mean_tpot_ms` - Average TPOT
- `.num_runs` - Number of runs included
- `.is_per_device_throughput` - Whether throughput is per-device (tp>1)
- `.tensor_parallel_degree` - Tensor parallelism degree

## When to Use This Skill
1. **When you need to filter results by SLO** - Keep only results within TTFT/TPOT limits
2. **When comparing multiple configurations** - Group and compare results
3. **When aggregating multiple runs** - Get averaged metrics with outliers removed
4. **After running benchmarks** - Process the raw results before reporting

## See Also
- `skills/benchmark_runner/README.md` - Generate benchmark results
- `skills/report_generator/README.md` - Generate reports from processed results
- `AGENT_GUIDELINES.md` - Complete usage guide
