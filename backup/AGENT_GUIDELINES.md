# Agent Guidelines - Using the Reconstructed Skills

This guide teaches you how to use the skill-based AUTO_INFRA framework to accomplish flexible benchmarking tasks.

## Overview

The AUTO_INFRA project has been reconstructed into modular skills that you can compose dynamically to accomplish various tasks beyond the fixed pipeline workflow.

## Available Skills

### 1. config_validator
**Purpose:** Load, validate, and expand configuration files.

**Key Functions:**
- `load_config_from_file(filepath)` - Load config dict from Python file
- `validate_config(config_dict)` - Validate config, returns (is_valid, errors)
- `expand_config(config_dict)` - Expand user config to FullConfig object
- `load_and_validate_config(filepath)` - All-in-one: load, validate, expand, load templates

**When to use:**
- When you need to load a config file
- Before launching services (to ensure config is valid)
- When you need to inspect what services would be launched

**Example:**
```python
from skills.config_validator import load_and_validate_config

full_config, template_loader, config_dict = load_and_validate_config("examples/demo_config.py")
print(f"Loaded {len(full_config.services)} services")
```

---

### 2. service_manager
**Purpose:** Launch, monitor, and terminate model serving services.

**Key Functions:**
- `ServiceManagerSkill(template_loader, full_config)` - Main skill class
  - `.launch_service(service_config, dry_run=False)` - Launch a service
  - `.wait_for_ready(instance, timeout=300, dry_run=False)` - Wait for service to be ready
  - `.kill_service(instance, dry_run=False)` - Kill a running service
  - `.cleanup_all(dry_run=False)` - Clean up all services

**When to use:**
- When you need to launch a model serving instance
- When you want fine-grained control over service lifecycle
- For scenarios where you need to keep a service running while varying other parameters

**Example:**
```python
from skills.service_manager import ServiceManagerSkill

# Initialize skill
service_skill = ServiceManagerSkill(template_loader, full_config)

# Get first service config
service_config = full_config.services[0]

# Launch service
instance = service_skill.launch_service(service_config, dry_run=True)
print(f"Service command: {instance.launch_command}")

# Wait for ready
if service_skill.wait_for_ready(instance, dry_run=True):
    print("Service is ready!")

# Clean up
service_skill.kill_service(instance, dry_run=True)
```

---

### 3. benchmark_runner
**Purpose:** Run benchmarks on active services and parse results.

**Key Functions:**
- `BenchmarkRunnerSkill(template_loader, full_config)` - Main skill class
  - `.generate_benchmark_command(service_config, case)` - Get command without running
  - `.run_benchmark(core_instance, case, run_index, dry_run=False)` - Single benchmark run
  - `.run_all_benchmarks_for_service(core_instance, dry_run=False)` - All benchmarks for service
- `create_benchmark_case(case_id, input_len, output_len, image_size, image_count, max_concurrency, num_prompts=None)` - Create a custom benchmark case

**When to use:**
- When you want to run individual benchmarks (not the full suite)
- When you need to dynamically vary benchmark parameters (like concurrency)
- For optimization searches over benchmark parameters

**Example (SLO Optimization Pattern):**
```python
from skills.benchmark_runner import BenchmarkRunnerSkill, create_benchmark_case

benchmark_skill = BenchmarkRunnerSkill(template_loader, full_config)

# Launch service ONCE
service_config = full_config.services[0]
instance = service_skill.launch_service(service_config, dry_run=True)
service_skill.wait_for_ready(instance, dry_run=True)

# Try increasing concurrency levels
best_throughput = 0
best_concurrency = None
SLO_TTFT_MAX = 100.0  # ms
SLO_TPOT_MAX = 20.0   # ms

for concurrency in [10, 20, 30, 40, 50]:
    # Create benchmark case with current concurrency
    case = create_benchmark_case(
        case_id=0,
        input_len=32,
        output_len=64,
        image_size="448x448",
        image_count=1,
        max_concurrency=concurrency
    )

    # Run benchmark
    result = benchmark_skill.run_benchmark(
        instance._core_instance, case, run_index=0, dry_run=True
    )

    if result.success:
        # Check SLO
        if result.mean_ttft_ms <= SLO_TTFT_MAX and result.mean_tpot_ms <= SLO_TPOT_MAX:
            # Within SLO - check if this is better
            if result.total_token_throughput > best_throughput:
                best_throughput = result.total_token_throughput
                best_concurrency = concurrency
                print(f"New best: {best_throughput:.2f} tok/s at concurrency {best_concurrency}")
        else:
            print(f"Concurrency {concurrency} violates SLO - stopping")
            break

# Clean up service
service_skill.kill_service(instance, dry_run=True)
print(f"\nBest throughput: {best_throughput:.2f} tok/s at concurrency {best_concurrency}")
```

---

### 4. result_processor
**Purpose:** Process, filter, and aggregate benchmark results.

**Key Functions:**
- `ResultProcessorSkill(data_watch_policy, slo_ttft_max, slo_tpot_max)` - Main skill class
  - `.filter_by_slo(results)` - Keep only results within SLO thresholds
  - `.remove_outliers(results)` - Remove min/max outliers
  - `.aggregate_per_service_case(suite_result, apply_slo_filter=True, remove_outliers=True)` - Aggregate results
  - `.group_results(aggregated_results)` - Group results for comparison
- Standalone convenience functions: `filter_by_slo()`, `remove_outliers()`, `aggregate_per_service_case()`, `group_results()`

**When to use:**
- When you need to filter results by SLO criteria
- When comparing different configurations
- When aggregating multiple runs

**Example:**
```python
from skills.result_processor import ResultProcessorSkill

processor = ResultProcessorSkill(
    data_watch_policy="remove_min_max",
    slo_ttft_max=100.0,
    slo_tpot_max=20.0
)

# Aggregate results
aggregated = processor.aggregate_per_service_case(suite_result)

# Group for comparison
groups = processor.group_results(aggregated)

for group in groups:
    print(f"\nGroup: {group.group_key}")
    for agg in group.service_case_results:
        print(f"  {agg.avg_total_token_throughput:.2f} tok/s")
```

---

### 5. report_generator
**Purpose:** Generate visualizations and comprehensive reports.

**Key Functions:**
- `ReportGeneratorSkill(reports_dir, do_visualize, slo_ttft_max, slo_tpot_max, data_watch_policy, template_loader)` - Main skill class
  - `.generate_report(suite_result, report_name=None)` - Generate full report
- `generate_report(suite_result, ...)` - Convenience function

**When to use:**
- When you have benchmark results to visualize
- At the end of an optimization search to document findings
- When comparing multiple configurations

---

### 6. pipeline_orchestrator
**Purpose:** Run the complete end-to-end benchmark pipeline (for backward compatibility).

**Key Functions:**
- `run_pipeline(config_dict, dry_run=False)` - Run from config dict
- `run_pipeline_from_file(filepath, dry_run=False)` - Run from config file

**When to use:**
- When you just want to run the standard pipeline
- For backward compatibility with existing config files

---

## Common Workflow Patterns

### Pattern 1: SLO-Based Throughput Optimization

**Goal:** Find the maximum achievable throughput while staying within SLO (Service Level Objective) constraints for TTFT and TPOT.

**Steps:**
1. Use `config_validator` to load your base config
2. Use `service_manager` to launch the service **once**
3. Loop over increasing `max_concurrency` values:
   - Use `benchmark_runner.create_benchmark_case()` with current concurrency
   - Use `benchmark_runner.run_benchmark()` to run it
   - Check if TTFT and TPOT are within SLO limits
   - If yes, keep track of the best throughput; if no, break the loop
4. Use `service_manager` to kill the service
5. Use `report_generator` to document your findings

**Key Insight:** Launch the service once at the beginning - you don't need to restart it for each benchmark!

---

### Pattern 2: Parameter Search

**Goal:** Find the best optimization option (env_opt or server_args_opt) for maximum throughput.

**Steps:**
1. Use `config_validator` to load a base config
2. For each option you want to test:
   - Create a modified ServiceConfig with the current option
   - Use `service_manager` to launch the service
   - Use `benchmark_runner` to run benchmarks
   - Collect results
   - Use `service_manager` to kill the service
3. Use `result_processor` to compare all results
4. Use `report_generator` to create a comparison report

---

### Pattern 3: Flexible Single-Service Testing

**Goal:** Test a single service with custom benchmark parameters without running the full pipeline.

**Steps:**
1. Load config and pick one ServiceConfig
2. Launch service with `service_manager`
3. Create custom BenchmarkCase objects with your parameters
4. Run benchmarks with `benchmark_runner`
5. Process results with `result_processor`
6. Clean up service

---

## Skill Import Cheat Sheet

```python
# Config handling
from skills.config_validator import (
    load_config_from_file,
    validate_config,
    expand_config,
    load_and_validate_config
)

# Service management
from skills.service_manager import (
    ServiceManagerSkill,
    launch_service,
    wait_for_ready,
    kill_service,
    cleanup_all_services
)

# Benchmark running
from skills.benchmark_runner import (
    BenchmarkRunnerSkill,
    run_benchmark,
    run_all_benchmarks_for_service,
    create_benchmark_case
)

# Result processing
from skills.result_processor import (
    ResultProcessorSkill,
    filter_by_slo,
    remove_outliers,
    aggregate_per_service_case,
    group_results
)

# Report generation
from skills.report_generator import (
    ReportGeneratorSkill,
    generate_report
)

# Full pipeline (backward compatibility)
from skills.pipeline_orchestrator import (
    PipelineOrchestratorSkill,
    run_pipeline,
    run_pipeline_from_file
)
```

## Tips for Success

1. **Always clean up:** Use try/finally blocks to ensure services are killed even if something fails.
2. **Dry-run first:** Test your workflow with `dry_run=True` before real execution.
3. **Reuse services:** Don't restart services between benchmark runs when only changing benchmark parameters.
4. **Check SLOs early:** Use `result_processor.filter_by_slo()` to quickly evaluate results.
5. **Look at examples:** See `examples/skill_based_pipeline.py` for working examples.

## Example: The SLO Optimization Workflow (Full)

See `examples/skill_based_pipeline.py` for a runnable example. Here's the pattern:

```python
# Import skills
from skills.config_validator import load_and_validate_config
from skills.service_manager import ServiceManagerSkill
from skills.benchmark_runner import BenchmarkRunnerSkill, create_benchmark_case

# Step 1: Load config
full_config, template_loader, config_dict = load_and_validate_config("examples/demo_config.py")

# Step 2: Initialize skills
service_skill = ServiceManagerSkill(template_loader, full_config)
benchmark_skill = BenchmarkRunnerSkill(template_loader, full_config)

# Step 3: Launch service ONCE
service_config = full_config.services[0]
instance = service_skill.launch_service(service_config, dry_run=True)
service_skill.wait_for_ready(instance, dry_run=True)

try:
    # Step 4: Find max concurrency under SLO
    best_throughput = 0
    best_concurrency = None

    for concurrency in [10, 20, 30, 40, 50]:
        # Create and run benchmark
        case = create_benchmark_case(0, 32, 64, "448x448", 1, concurrency)
        result = benchmark_skill.run_benchmark(
            instance._core_instance, case, 0, dry_run=True
        )

        # Check SLO and track best
        if result.success:
            if result.mean_ttft_ms <= 100 and result.mean_tpot_ms <= 20:
                if result.total_token_throughput > best_throughput:
                    best_throughput = result.total_token_throughput
                    best_concurrency = concurrency
            else:
                break  # SLO violated, stop increasing

finally:
    # Step 5: Always clean up
    service_skill.kill_service(instance, dry_run=True)

print(f"Best: {best_throughput} tok/s at concurrency {best_concurrency}")
```
