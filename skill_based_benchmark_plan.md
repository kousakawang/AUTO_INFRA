# Plan: Qwen3.5-9B Preliminary Performance Optimization Test

## Context

This plan executes a **preliminary performance optimization test** for the Qwen3.5-9B model as specified in `request_case/request_case_1.md`. The test will compare baseline performance with optimized configurations using the AUTO_INFRA skill-based framework.

**Key Requirements:**
- Model: `/data01/models/Qwen3.5-9B`
- All services must include `--context-length 262144 --reasoning-parser qwen3`
- Test type: Preliminary performance optimization testing
- **Use individual skills, NOT pipeline_orchestrator**

## Test Configuration Overview

Based on `dummy_template.md`, the preliminary performance optimization test includes:

### Services to Launch (4 total)

| Service | Template | Env Opt | Server Opt | Additional Opts | GPU | Port |
|---------|----------|---------|------------|-----------------|-----|------|
| 1 (Baseline - Small) | 2 (with `--disable-radix-cache`, `SGLANG_VLM_CACHE_SIZE_MB=0`) | -1 | -1 | `--context-length 262144 --reasoning-parser qwen3` | 0 | 8080 |
| 2 (Optimized - Small + flashinfer) | 2 | -1 | 3 (`--decode-attention-backend flashinfer`) | `--context-length 262144 --reasoning-parser qwen3` | 1 | 8070 |
| 3 (Baseline - Large) | 2 | -1 | -1 | `--context-length 262144 --reasoning-parser qwen3` | 2 | 8060 |
| 4 (Optimized - Large + FP8) | 2 | 2 (`SGLANG_VISION_ATTN_FP8=1`) | -1 | `--context-length 262144 --reasoning-parser qwen3` | 3 | 8050 |

### Benchmark Cases

**Service 1 & 2 (Small Image QA):**
| Case | Input Len | Output Len | Image Size | Concurrency |
|------|-----------|------------|------------|-------------|
| 0 | 64 | 32 | 448x448 | 2 |
| 1 | 64 | 32 | 448x448 | 4 |
| 2 | 64 | 32 | 448x448 | 8 |

**Service 3 & 4 (Large Image QA):**
| Case | Input Len | Output Len | Image Size | Concurrency |
|------|-----------|------------|------------|-------------|
| 0 | 128 | 64 | 1280x1280 | 2 |
| 1 | 128 | 64 | 1280x1280 | 4 |

### Pipeline Config
- `per_config_benchmark_times`: 3 runs per case
- `max_existed_service_num`: 2 concurrent services
- `data_watch_policy`: `remove_min_max`
- `do_visuallize`: True

## Implementation Steps

### Step 1: Create Configuration File
Create a config file `request_case/config_request_1.py` with the complete test configuration.

**File to create:** `/sgl-workspace/AUTO_INFRA/request_case/config_request_1.py`

### Step 2: Validate and Load Configuration
Use `config_validator` skill to load and validate the configuration:
- Verify all services have the required `--context-length 262144 --reasoning-parser qwen3`
- Check server launch commands match the template from `dummy_template.md`
- Confirm GPU assignments don't conflict
- Validate benchmark cases are correctly configured

### Step 3: Execute Benchmarks Using Individual Skills
Use skills in sequence to run the benchmark pipeline:

**3.1 Initialize Skills**
- `service_manager`: For launching/killing services
- `benchmark_runner`: For running benchmarks
- `result_processor`: For aggregating results
- `report_generator`: For generating reports

**3.2 Run Services in Batches (max 2 concurrent)**
- **Batch 1:** Service 1 (Baseline-Small) + Service 2 (Optimized-Small)
  - Launch both services
  - Wait for ready
  - Run all benchmarks for both services
  - Kill both services

- **Batch 2:** Service 3 (Baseline-Large) + Service 4 (Optimized-Large)
  - Launch both services
  - Wait for ready
  - Run all benchmarks for both services
  - Kill both services

**3.3 Collect All Results**
- Gather benchmark results from all runs
- Apply SLO filtering and outlier removal
- Aggregate results per service/case

### Step 4: Generate Report
Use `report_generator` skill to:
- Create comprehensive markdown report
- Generate visualizations comparing:
  - Baseline vs flashinfer (small image)
  - Baseline vs FP8 (large image)

## Critical Files

### Files to Create
- `/sgl-workspace/AUTO_INFRA/request_case/config_request_1.py` - Test configuration
- `/sgl-workspace/AUTO_INFRA/request_case/run_request_1.py` - Execution script using individual skills

### Files to Use
- `/sgl-workspace/AUTO_INFRA/skills/config_validator/__init__.py` - Load/validate config
- `/sgl-workspace/AUTO_INFRA/skills/service_manager/__init__.py` - Service lifecycle
- `/sgl-workspace/AUTO_INFRA/skills/benchmark_runner/__init__.py` - Run benchmarks
- `/sgl-workspace/AUTO_INFRA/skills/result_processor/__init__.py` - Process results
- `/sgl-workspace/AUTO_INFRA/skills/report_generator/__init__.py` - Generate reports
- `/sgl-workspace/AUTO_INFRA/launch_server_template/launch_server_template_2.md` - Server template
- `/sgl-workspace/AUTO_INFRA/benchmark_template/benchmark_template_1.md` - Benchmark template
- `/sgl-workspace/AUTO_INFRA/OPT/ENV_OPT.md` - Env options (index 2 = FP8)
- `/sgl-workspace/AUTO_INFRA/OPT/SERVER_ARG_OPT.md` - Server args (index 3 = flashinfer)

## Skills to Use

1. **config_validator** - Load and validate the configuration
2. **service_manager** - Launch and manage services
3. **benchmark_runner** - Run benchmark tests
4. **result_processor** - Process and aggregate results
5. **report_generator** - Generate visualizations and reports

## Verification Steps

After configuration creation but before full execution:
1. Dry-run validation with `config_validator`
2. Verify generated server commands match template requirements
3. Confirm all services include `--context-length 262144 --reasoning-parser qwen3`

After pipeline execution:
1. Check report was generated in `reports/` directory
2. Verify all 4 services were tested
3. Confirm visualization shows performance comparisons
