# How to Use This Repository for Automated Benchmarking and Report Generation

This guide explains how to use the AI Model Serving Benchmark Framework to run automated benchmarks and generate reports.

## Important: Agent Workflow

**When a user asks you to run benchmarks:**
1. **First**, generate a configuration Python file (e.g., `examples/my_config.py`) according to the user's requirements, and put the config  file under test_cases. Add time information in the file name
2. **Then**, execute the pipeline with this config file using the commands below
3. **Always start with a dry-run** to verify the configuration before running real benchmarks

## Overview

This framework automates three main processes:
1. **Service Launching**: Launch multiple AI model serving instances with configurable parameters
2. **Performance Benchmarking**: Run benchmark tests on active serving instances
3. **Report Generation**: Collect and aggregate benchmark results with visualizations

## A. How to Generate the Config File

The configuration file is a Python file that defines a `config_dict` variable containing both `user_config` and `pipeline_config`.

### Config File Structure

```python
config_dict = {
    "user_config": {
        # Model and service configuration
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
            [""],
            [""],
            [""]
        ],

        # Benchmark configuration
        "benchmark_case_num": [[3], [3], [3], [1]],
        "benchmark_inputlen": [[32, 32, 32], [32, 32, 32], [32, 64, 32], [32]],
        "benchmark_outputlen": [[64, 64, 64], [64, 64, 64], [64, 32, 32], [64]],
        "benchmark_image_size": [
            ["448x448", "448x448", "448x448"],
            ["448x448", "448x448", "448x448"],
            ["448x448", "448x448", "448x448"],
            ["1080x720"]
        ],
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

### Detailed Explanation of Each Option

#### user_config Options

**Model and Service Configuration:**

| Option | Type | Description |
|--------|------|-------------|
| `model_paths` | List[str] | List of model paths to test. Each path is a local filesystem path to the model weights. |
| `model_test_times` | List[int] | Number of times to test each model. Length must match `model_paths`. The sum of this list equals the total number of services to launch. |
| `model_deploy_method` | List[str] | Deployment method for each service. Use "tp1" for tensor parallelism 1 (single GPU), "tp2" for tensor parallelism 2 (2 GPUs), etc. Length must equal sum of `model_test_times`. |
| `device_id` | List[List[int]] | GPU device IDs for each service. Each sublist contains the CUDA device IDs to use for that service. Length must equal sum of `model_test_times`. |
| `basic_template_id` | List[int] | Which launch server template to use for each service. 0 = template 1, 1 = template 2, etc. See `launch_server_template/` directory. Length must equal sum of `model_test_times`. |
| `port` | List[int] | Port number for each service. Must be unique. Length must equal sum of `model_test_times`. |
| `env_opt_id` | List[List[int]] | Environment optimization IDs from `OPT/ENV_OPT.md`. Use `-1` for no optimization, `0` for first option, `1` for second option, etc. Can specify multiple optimizations. Length must equal sum of `model_test_times`. |
| `server_args_opt_id` | List[List[int]] | Server argument optimization IDs from `OPT/SERVER_ARG_OPT.md`. Use `-1` for no optimization, `0` for first option, `1` for second option, etc. Can specify multiple optimizations. Length must equal sum of `model_test_times`. |
| `additional_option` | List[List[str]] | Additional command-line arguments to append to the server launch command. Use `[""]` for no additional options. Length must equal sum of `model_test_times`. |

**Benchmark Configuration:**

| Option | Type | Description |
|--------|------|-------------|
| `benchmark_case_num` | List[List[int]] | Number of benchmark cases to run for each service. Each sublist contains one integer (the case count for that service). Length of outer list must equal sum of `model_test_times`. |
| `benchmark_inputlen` | List[List[int]] | Input token lengths for each benchmark case. For each service, if the **sublist** length is less than that service's `benchmark_case_num`, the last value is repeated. Length of outer list must equal sum of `model_test_times`. |
| `benchmark_outputlen` | List[List[int]] | Output token lengths for each benchmark case. Auto-expansion same as `benchmark_inputlen` (applies to each service's sublist). Length of outer list must equal sum of `model_test_times`. |
| `benchmark_image_size` | List[List[str]] | Image resolution (e.g., "448x448") for each benchmark case. Auto-expansion same as `benchmark_inputlen` (applies to each service's sublist). Length of outer list must equal sum of `model_test_times`. |
| `benchmark_image_count` | List[List[int]] | Number of images per prompt for each benchmark case. Auto-expansion same as `benchmark_inputlen` (applies to each service's sublist). Length of outer list must equal sum of `model_test_times`. |
| `benchmark_max_concurrency` | List[List[int]] | Maximum concurrency (number of parallel requests) for each benchmark case. Auto-expansion same as `benchmark_inputlen` (applies to each service's sublist). Length of outer list must equal sum of `model_test_times`. |

#### pipeline_config Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `per_config_benchmark_times` | int | 5 | Number of times to run each benchmark configuration (for statistical significance). |
| `prompt_num_dvide_max_concurrency` | int | 6 | Number of prompts to use = `max_concurrency * prompt_num_dvide_max_concurrency`. |
| `data_watch_policy` | str | "remove_min_max" | Policy for data aggregation: "remove_min_max" = remove min and max values before computing average. |
| `max_existed_service_num` | int | 2 | Maximum number of services to run simultaneously (to avoid resource contention). |
| `do_visuallize` | bool | True | Whether to generate visualizations and reports. Set to False to skip. |
| `SLO` | List[float] | [1e8, 1e8] | Service Level Objective thresholds: [TTFT_MAX, TPOT_MAX]. Only results with TTFT <= TTFT_MAX and TPOT <= TPOT_MAX are included in the report. Use large values (like 1e8) to disable filtering. |

### Template and OPT Files

- **Launch Server Templates**: Located in `launch_server_template/`
  - `launch_server_template_1.md`: Base template with standard options
  - `launch_server_template_2.md`: Template with radix cache disabled

- **Benchmark Templates**: Located in `benchmark_template/`
  - `benchmark_template_1.md`: General-purpose image-based benchmark template

- **Optimization Options**: Located in `OPT/`
  - `ENV_OPT.md`: Environment variable optimizations (index 0, 1, 2, ...)
  - `SERVER_ARG_OPT.md`: Server argument optimizations (index 0, 1, 2, ...)

## B. How to Run the Whole Pipeline

**Note**: Make sure you have generated the configuration file first according to the user's requirements (see Section A).

### Dry Run (Recommended First)

To verify your configuration without actually launching services or running benchmarks:

```bash
python3 run_benchmark.py --config examples/demo_config.py --dry-run
```

### Real Benchmark Run

Once your configuration is validated, run the full benchmark pipeline:

```bash
python3 run_benchmark.py --config examples/demo_config.py
```

### Command-Line Options

| Option | Description |
|--------|-------------|
| `--config`, `-c` | Path to configuration Python file (required) |
| `--dry-run`, `-d` | Dry run mode - don't actually launch services or run benchmarks |
| `--verbose`, `-v` | Enable verbose logging |
| `--help` | Show help message and exit |

### Outputs

The pipeline produces:

1. **Raw Results**: Saved to `outputs/benchmark_results_YYYYMMDD_HHMMSS.json`
2. **Report**: Generated at `reports/benchmark_report_YYYYMMDD_HHMMSS.md`
3. **Visualizations**: PNG files in `reports/` directory (if `do_visuallize` is True)

### Pipeline Workflow

1. **Configuration Validation**: Checks that all required fields are present and valid
2. **Configuration Expansion**: Expands user config to full service configurations
3. **Template Loading**: Loads server launch and benchmark templates
4. **Component Initialization**: Sets up service manager and benchmark orchestrator
5. **Execution**: Launches services (up to `max_existed_service_num` at once), runs benchmarks, and cleans up services
6. **Result Saving**: Stores raw results in JSON format
7. **Report Generation**: Creates markdown report with visualizations

## Example

See `examples/demo_config.py` for a complete example configuration.
