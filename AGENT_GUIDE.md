# Agent Guide - AUTO_INFRA Benchmark Framework

This guide explains how to use the AUTO_INFRA framework to run automated AI model serving benchmarks using the skill-based architecture.

## Overview

AUTO_INFRA automates three main processes for AI model serving evaluation:
1. **Service Launching** - Launch multiple AI model serving instances (SGLang) with configurable parameters
2. **Performance Benchmarking** - Run benchmark tests measuring throughput, latency, and concurrency
3. **Report Generation** - Collect/aggregate results with visualizations

The framework is built around composable **skills** that can be used individually or orchestrated as a complete pipeline.

## Quick Start: Running the Full Pipeline

### Step 1: Generate or prepare a config file

**Option A: Use the config generator skill** (recommended for raw command files):
```bash
python3 -m skills.config_generator.generate_config --file request_case/raw_commands_requirement/raw_test_case.sh
```

**Option B: Manually create a config file** following the structure in `examples/demo_config.py`. Place config files under `test_cases/` with a timestamp in the filename.

**If the user provides raw launch server and benchmark commands:**
1. Compare with templates in `configs/templates/` to identify `basic_template_id`
2. Compare with `configs/OPT/ENV_OPT.md` and `configs/OPT/SERVER_ARG_OPT.md` for opt IDs
3. Extract model path, port, device IDs, tensor parallel size, benchmark params
4. Refer to `skills/config_generator/config_builder.py` for implementation details

### Step 2: Run the pipeline (always dry-run first)

```bash
python3 examples/skill_based_pipeline.py --config test_cases/your_config.py --example full
```

For manual skill composition mode:
```bash
python3 examples/skill_based_pipeline.py --config test_cases/your_config.py --example manual
```

### Outputs

- **Raw Results**: `outputs/benchmark_results_YYYYMMDD_HHMMSS.json`
- **Report**: `reports/benchmark_report_YYYYMMDD_HHMMSS.md`
- **Visualizations**: PNG files in `reports/`

---

## Configuration Reference

### Config File Structure

```python
config_dict = {
    "user_config": {
        "model_paths": ["/path/to/model1", "/path/to/model2"],
        "model_test_times": [3, 1],
        "model_deploy_method": ["tp1", "tp2", "tp1", "tp1"],
        "device_id": [[0], [1, 2], [3], [4]],
        "basic_template_id": [0, 0, 0, 1],
        "port": [8080, 8070, 8060, 8050],
        "env_opt_id": [[-1], [0], [-1], [-1]],
        "server_args_opt_id": [[0], [0], [1], [1]],
        "additional_option": [
            ["--context-length 262144 --reasoning-parser qwen3"],
            [""], [""], [""]
        ],
        "benchmark_case_num": [[3], [3], [3], [1]],
        "benchmark_inputlen": [[32, 32, 32], [32, 32, 32], [32, 64, 32], [32]],
        "benchmark_outputlen": [[64, 64, 64], [64, 64, 64], [64, 32, 32], [64]],
        "benchmark_image_size": [["448x448","448x448","448x448"], ["448x448","448x448","448x448"], ["448x448","448x448","448x448"], ["1080x720"]],
        "benchmark_image_count": [[1, 1, 1], [1, 1, 1], [1, 1, 1], [1]],
        "benchmark_max_concurrency": [[10, 20, 30], [10, 20, 30], [10, 20, 30], [10]],
    },
    "pipeline_config": {
        "per_config_benchmark_times": 5,
        "prompt_num_dvide_max_concurrency": 6,
        "data_watch_policy": "remove_min_max",
        "max_existed_service_num": 2,
        "do_visuallize": True,
        "SLO": [1e8, 1e8],
    }
}
```

### user_config Options

| Option | Type | Description |
|--------|------|-------------|
| `model_paths` | List[str] | Model paths to test. |
| `model_test_times` | List[int] | Times to test each model. Sum = total services. |
| `model_deploy_method` | List[str] | "tp1", "tp2", etc. Length = sum(model_test_times). |
| `device_id` | List[List[int]] | CUDA device IDs per service. |
| `basic_template_id` | List[int] | Template ID from `configs/templates/`. |
| `port` | List[int] | Unique port per service. |
| `env_opt_id` | List[List[int]] | Env opt IDs from `configs/OPT/ENV_OPT.md`. Use -1 for none. |
| `server_args_opt_id` | List[List[int]] | Server arg opt IDs from `configs/OPT/SERVER_ARG_OPT.md`. |
| `additional_option` | List[List[str]] | Extra CLI args. Use [""] for none. |
| `benchmark_case_num` | List[List[int]] | Number of benchmark cases per service. |
| `benchmark_inputlen` | List[List[int]] | Input token lengths per case. |
| `benchmark_outputlen` | List[List[int]] | Output token lengths per case. |
| `benchmark_image_size` | List[List[str]] | Image resolution per case (e.g. "448x448"). |
| `benchmark_image_count` | List[List[int]] | Images per prompt per case. |
| `benchmark_max_concurrency` | List[List[int]] | Max concurrency per case. |

### pipeline_config Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `per_config_benchmark_times` | int | 5 | Runs per benchmark config. |
| `prompt_num_dvide_max_concurrency` | int | 6 | num_prompts = max_concurrency * this. |
| `data_watch_policy` | str | "remove_min_max" | Outlier removal policy. |
| `max_existed_service_num` | int | 2 | Max concurrent services. |
| `do_visuallize` | bool | True | Generate visualizations. |
| `SLO` | List[float] | [1e8, 1e8] | [TTFT_MAX, TPOT_MAX] thresholds. |

### Template and OPT Files

- **Launch Server Templates**: `configs/templates/launch_server_template_*.md`
- **Benchmark Templates**: `configs/templates/benchmark_template_*.md`
- **Environment Optimizations**: `configs/OPT/ENV_OPT.md`
- **Server Argument Optimizations**: `configs/OPT/SERVER_ARG_OPT.md`

---

## Available Skills

### 1. config_validator
Load, validate, and expand configuration files.

```python
from skills.config_validator import load_and_validate_config
full_config, template_loader, config_dict = load_and_validate_config("examples/demo_config.py")
```

### 2. config_generator
Generate config files from raw launch/benchmark commands.

```python
from skills.config_generator import ConfigBuilder
builder = ConfigBuilder(project_root)
builder.add_launch_command(raw_cmd)
config_dict = builder.build_config()
```

### 3. service_manager
Launch, monitor, and terminate model serving services.

```python
from skills.service_manager import ServiceManagerSkill
service_skill = ServiceManagerSkill(template_loader, full_config)
instance = service_skill.launch_service(service_config, dry_run=True)
service_skill.wait_for_ready(instance, dry_run=True)
service_skill.kill_service(instance, dry_run=True)
```

### 4. benchmark_runner
Run benchmarks on active services and parse results.

```python
from skills.benchmark_runner import BenchmarkRunnerSkill, create_benchmark_case
benchmark_skill = BenchmarkRunnerSkill(template_loader, full_config)
case = create_benchmark_case(0, 32, 64, "448x448", 1, 20)
result = benchmark_skill.run_benchmark(instance._core_instance, case, 0, dry_run=True)
```

### 5. result_processor
Process, filter, and aggregate benchmark results.

```python
from skills.result_processor import ResultProcessorSkill
processor = ResultProcessorSkill(data_watch_policy="remove_min_max", slo_ttft_max=100.0, slo_tpot_max=20.0)
aggregated = processor.aggregate_per_service_case(suite_result)
groups = processor.group_results(aggregated)
```

### 6. report_generator
Generate visualizations and comprehensive reports.

```python
from skills.report_generator import ReportGeneratorSkill
report_skill = ReportGeneratorSkill(template_loader=template_loader)
report_path = report_skill.generate_report(suite_result)
```

### 7. pipeline_orchestrator
Run the complete end-to-end pipeline.

```python
from skills.pipeline_orchestrator import run_pipeline_from_file
result = run_pipeline_from_file("test_cases/config.py", dry_run=True)
```

---

## Skill Import Cheat Sheet

```python
from skills.config_validator import load_config_from_file, validate_config, expand_config, load_and_validate_config
from skills.service_manager import ServiceManagerSkill, launch_service, wait_for_ready, kill_service, cleanup_all_services
from skills.benchmark_runner import BenchmarkRunnerSkill, run_benchmark, run_all_benchmarks_for_service, create_benchmark_case
from skills.result_processor import ResultProcessorSkill, filter_by_slo, remove_outliers, aggregate_per_service_case, group_results
from skills.report_generator import ReportGeneratorSkill, generate_report
from skills.pipeline_orchestrator import PipelineOrchestratorSkill, run_pipeline, run_pipeline_from_file
```

---

## Common Workflow Patterns

### Pattern 1: Full Pipeline (Standard)
Use `pipeline_orchestrator` to run the standard end-to-end pipeline. Best for straightforward benchmarking.

### Pattern 2: SLO-Based Throughput Optimization
Find maximum throughput under SLO constraints:
1. Load config with `config_validator`
2. Launch service **once** with `service_manager`
3. Loop over increasing concurrency levels with `benchmark_runner`
4. Check TTFT/TPOT against SLO limits
5. Clean up and report

### Pattern 3: Parameter Search
Compare different optimization options:
1. Load base config
2. For each option: launch service → run benchmarks → collect results → kill service
3. Compare with `result_processor`
4. Report with `report_generator`

### Pattern 4: Flexible Single-Service Testing
Test one service with custom benchmark parameters:
1. Load config, pick one service
2. Launch with `service_manager`
3. Create custom `BenchmarkCase` objects
4. Run with `benchmark_runner`
5. Process and clean up

---

## Tips

1. **Always dry-run first** - Test with `dry_run=True` before real execution
2. **Always clean up** - Use try/finally to ensure services are killed
3. **Reuse services** - Don't restart between benchmark runs when only changing benchmark parameters
4. **Check SLOs early** - Use `result_processor.filter_by_slo()` to quickly evaluate
5. **See examples** - `examples/skill_based_pipeline.py` has working examples of full and manual modes
