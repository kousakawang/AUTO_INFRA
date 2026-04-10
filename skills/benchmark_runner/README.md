# benchmark_runner Skill

Run benchmarks on active services and parse results.

## Purpose
This skill runs benchmarks on active model serving services. Use this when you need to:
- Generate benchmark commands without running them
- Run individual benchmark cases
- Run all benchmarks for a service
- Create custom benchmark cases with specific parameters

## Key Functions

### `create_benchmark_case(case_id: int, input_len: int, output_len: int, image_size: str, image_count: int, max_concurrency: int, num_prompts: Optional[int] = None) -> BenchmarkCase`
Create a BenchmarkCase with automatic num_prompts calculation.

**Args:**
- `case_id`: Case identifier
- `input_len`: Input token length
- `output_len`: Output token length
- `image_size`: Image resolution (e.g., "448x448")
- `image_count`: Number of images per prompt
- `max_concurrency`: Maximum concurrency
- `num_prompts`: Number of prompts (default: max_concurrency * 6)

**Returns:**
- `BenchmarkCase` object

**Example:**
```python
from skills.benchmark_runner import create_benchmark_case

case = create_benchmark_case(
    case_id=0,
    input_len=32,
    output_len=64,
    image_size="448x448",
    image_count=1,
    max_concurrency=20
)
```

---

## Key Class: `BenchmarkRunnerSkill`

### `BenchmarkRunnerSkill(template_loader: TemplateLoader, full_config: Optional[FullConfig] = None)`
Main skill class for running benchmarks.

**Methods:**

#### `.generate_benchmark_command(service_config: ServiceConfig, benchmark_case: BenchmarkCase) -> str`
Generate the benchmark command without running it.

---

#### `.run_benchmark(core_service_instance: CoreServiceInstance, case: BenchmarkCase, run_index: int = 0, dry_run: bool = False, mock_output: Optional[str] = None) -> BenchmarkResult`
Run a single benchmark on a service.

**Args:**
- `core_service_instance`: Core ServiceInstance from service_manager
- `case`: BenchmarkCase to run
- `run_index`: Index of this run (for multiple runs per case)
- `dry_run`: If True, don't actually run
- `mock_output`: Mock output to use for dry-run

**Returns:**
- `BenchmarkResult` with results

---

#### `.run_all_benchmarks_for_service(core_service_instance: CoreServiceInstance, dry_run: bool = False) -> ServiceResult`
Run all benchmarks for a service (as defined in its service_config).

**Returns:**
- `ServiceResult` with all benchmark results

---

## Convenience Functions (Global)

- `run_benchmark(core_service_instance, case, run_index=0, template_loader=None, dry_run=False)`
- `run_all_benchmarks_for_service(core_service_instance, template_loader=None, dry_run=False)`

## Example Usage: SLO Optimization Pattern

```python
from skills.config_validator import load_and_validate_config
from skills.service_manager import ServiceManagerSkill
from skills.benchmark_runner import BenchmarkRunnerSkill, create_benchmark_case

# Load config
full_config, template_loader, config_dict = load_and_validate_config("examples/demo_config.py")

# Initialize skills
service_skill = ServiceManagerSkill(template_loader, full_config)
benchmark_skill = BenchmarkRunnerSkill(template_loader, full_config)

# Launch service ONCE
service_config = full_config.services[0]
instance = service_skill.launch_service(service_config, dry_run=True)
service_skill.wait_for_ready(instance, dry_run=True)

SLO_TTFT_MAX = 100.0
SLO_TPOT_MAX = 20.0
best_throughput = 0
best_concurrency = None

try:
    # Try increasing concurrency levels
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
            ttft_ok = result.mean_ttft_ms <= SLO_TTFT_MAX
            tpot_ok = result.mean_tpot_ms <= SLO_TPOT_MAX

            if ttft_ok and tpot_ok:
                # Within SLO - track best
                if result.total_token_throughput > best_throughput:
                    best_throughput = result.total_token_throughput
                    best_concurrency = concurrency
                    print(f"New best: {best_throughput:.2f} tok/s @ concurrency {best_concurrency}")
            else:
                print(f"Concurrency {concurrency} violates SLO - stopping")
                break

finally:
    # Clean up ONCE
    service_skill.kill_service(instance, dry_run=True)

print(f"\nBest: {best_throughput:.2f} tok/s at concurrency {best_concurrency}")
```

## When to Use This Skill
1. **When you want to run individual benchmarks** (not full suite)
2. **For SLO-based throughput optimization** - vary concurrency on same service
3. **For custom benchmark parameters** - create your own BenchmarkCase
4. **When you need fine-grained control** over benchmark execution

## BenchmarkResult Fields
A successful BenchmarkResult contains:
- `.total_token_throughput` - Total token throughput (tok/s)
- `.request_throughput` - Request throughput (req/s)
- `.mean_ttft_ms` - Mean Time to First Token (ms)
- `.mean_tpot_ms` - Mean Time per Output Token (ms)
- `.success` - Whether benchmark succeeded

## See Also
- `skills/service_manager/README.md` - Launch services first
- `skills/result_processor/README.md` - Process benchmark results
- `AGENT_GUIDELINES.md` - Complete usage guide with patterns
