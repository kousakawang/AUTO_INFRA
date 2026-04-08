# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an **automated testing and benchmarking framework for AI model serving systems** built primarily for evaluating and comparing performance of large language models (LLMs) and vision-language models (VLMs) using the SGLang framework.

## Repository Structure

```
/root/AUTO_TEST/
├── [important]_project_requirement.md   # Project requirements and architecture overview
├── [important]_example_workflow.md      # Example workflow and configuration guide
├── launch_server_basic.sh               # Basic server launch command example
├── benchmark_cmd_basic.sh               # Basic benchmark command example
├── benchmark_result_example.md          # Example benchmark report output
├── CLAUDE.md                            # This file - project documentation for Claude instances
├── launch_server_template/              # Server launch command templates
│   ├── launch_server_template_1.md
│   └── launch_server_template_2.md
├── benchmark_template/                  # Benchmark command templates
│   └── benchmark_template_1.md
├── OPT/                                 # Optimization configuration files
│   ├── SERVER_ARG_OPT.md               # Server argument optimization options
│   └── ENV_OPT.md                      # Environment variable optimization options
└── .claude/
    └── settings.local.json             # Claude Code configuration
```

## Project Type

**Language:** Python 3.8+ (Primary)
**Framework:** SGLang - A high-performance serving framework for LLMs/VLMs
**Purpose:** Performance testing and benchmarking of AI model serving
**OS:** Linux (CUDA-enabled GPUs required)

## Core Functionality

The project automates three main processes:

### 1. Service Launching
- Launch multiple AI model serving instances with configurable parameters
- Supports various deployment methods (tensor parallelism, device allocation, etc.)
- Handles CUDA device visibility and environment variables
- Manages server lifecycle (start/stop)

### 2. Performance Benchmarking
- Runs benchmark tests on active serving instances
- Measures throughput, latency, concurrency, and other performance metrics
- Supports image, text, and multi-modal benchmarks
- Configurable parameters: input length, output length, image resolution, concurrency, etc.

### 3. Report Generation
- Collects and aggregates benchmark results
- Generates visualizations and tables for comparison
- Removes outliers (min/max values) for accurate averages
- Creates comprehensive reports in markdown format

## Configuration System

### User Input Configuration

The system uses a hierarchical configuration system:

**Level 1 (Simple Configuration):** User-provided settings to reduce manual work
**Level 2 (Generated Configuration):** Complex configurations generated from Level 1 settings

Example configuration structure (from example_workflow.md):
```python
user_config = {
    "model_paths": ["/data01/models/Qwen3.5-9B", "/data01/models/Qwen3-VL-8B"],
    "model_test_times": [3, 1],
    "model_deploy_method": ["tp1", "tp2", "tp1", "tp1"],
    "device_id": [[0], [1,2], [3], [4]],
    "basic_template_id": [0, 0, 0, 1],
    "port": [8080, 8070, 8060, 8050],
    "env_opt_id": [[-1], [0], [-1], [-1]],
    "server_args_opt_id": [[0], [0], [1], [1]],
    "additional_option": [...],
    "benchmark_case_num": [[3], [3], [3], [1]],
    "benchmark_inputlen": [...],
    "benchmark_outputlen": [...],
    "benchmark_image_size": [...],
    "benchmark_image_count": [...],
    "benchmark_max_concurrency": [...],
}

pipline_config = {
    "per_config_benchmark_times": 5,
    "prompt_num_dvide_max_concurrency": 6,
    "data_watch_policy": "remove_min_max",
    "max_existed_service_num": 2,
    "do_visuallize":  True, # if False skip visualizing and report generation
    "SLO":[1e8, 1e8], # a two member list which contains[TTFT_MAX, TPOT_MAX], report should only include throught data in which case the  TTFT <= TTFT_MAX and TPOT <= TPOT_MAX
}
```

### Configuration Files Location

- **Optimization Options:** `/root/AUTO_TEST/OPT/`
  - `ENV_OPT.md` - Environment variable optimization settings
  - `SERVER_ARG_OPT.md` - Server argument optimization settings

- **Command Templates:** `/root/AUTO_TEST/*_template/` directories

## Launching Servers

### Basic Command Example (launch_server_basic.sh)

```bash
CUDA_VISIBLE_DEVICES=6 SGLANG_VLM_CACHE_SIZE_MB=0 python3 -m sglang.launch_server \
  --model-path /data01/models/Qwen3.5-9B/ \
  --host 127.0.0.1 \
  --port 8070 \
  --mem-fraction-static 0.7 \
  --cuda-graph-max-bs 128 \
  --tensor-parallel-size 1 \
  --mm-attention-backend fa3 \
  --cuda-graph-bs 128 120 112 104 96 88 80 72 64 56 48 40 32 24 16 8 4 2 1 \
  --disable-radix-cache \
  --context-length 262144 \
  --reasoning-parser qwen3
```

Key Parameters:
- `CUDA_VISIBLE_DEVICES`: GPU devices to use
- `--model-path`: Path to model weights
- `--port`: Serving port
- `--tensor-parallel-size`: Tensor parallelism degree (tp1, tp2, etc.)
- `--mem-fraction-static`: Static memory allocation
- `--mm-attention-backend`: Multi-modal attention backend

## Benchmarking

### Basic Command Example (benchmark_cmd_basic.sh)

```bash
python3 -m sglang.bench_serving \
  --backend sglang-oai-chat \
  --dataset-name image \
  --num-prompts 128 \
  --apply-chat-template \
  --random-output-len 64 \
  --random-input-len 32 \
  --image-resolution 448x448 \
  --image-format jpeg \
  --image-count 1 \
  --image-content blank \
  --random-range-ratio 1 \
  --max-concurrency 20 \
  --host=127.0.0.1 \
  --port=8070
```

### Measured Metrics

Each benchmark produces detailed reports including:

**Throughput Metrics:**
- Request throughput (req/s)
- Input token throughput (tok/s)
- Output token throughput (tok/s)
- Total token throughput (tok/s)

**Latency Metrics:**
- Mean/Median/P90/P99 End-to-End (E2E) Latency
- Time to First Token (TTFT)
- Time per Output Token (TPOT)
- Inter-Token Latency (ITL)

**Concurrency Metrics:**
- Max concurrency achieved
- Peak concurrent requests

## Workflow

### Typical Usage Flow

1. **Configuration Phase:**
   - User defines simple configuration in a Python dictionary
   - Execute generation script to create complex configuration

2. **Execution Phase:**
   - Run agent with single command
   - Agent generates server launch commands from templates and config
   - Launches servers (max 2 concurrent by default)
   - Runs benchmark command sets on each server
   - Manages server lifecycle (kill after testing completes)

3. **Reporting Phase:**
   - Collects all benchmark results
   - Generates comparison tables and visualizations
   - Handles data aggregation and outlier removal

### Key Principles

- **Automation:** Single-command test execution after configuration
- **Modularity:** Separate templates for server launch and benchmark
- **Scalability:** Support for multiple models, deployment methods, and configurations
- **Visualization:** Generate comprehensive HTML or Markdown reports
- **Efficiency:** Optimized for GPU resource utilization

## Templates

### Server Launch Templates

Located in `/root/AUTO_TEST/launch_server_template/`:

- **Template 1:** Base template with standard options
- **Template 2:** Template with additional features (e.g., radix cache disabled)

Templates use variables like `${ENV_OPT}`, `${MODEL_PATH}`, `${PORT}`, etc.

### Benchmark Templates

Located in `/root/AUTO_TEST/benchmark_template/`:

- **Template 1:** General-purpose image-based benchmark template
- Variables include `${NUM_PROMPT}`, `${OUT_LEN}`, `${IN_LEN}`, `${IMAGE_SIZE}`, etc.

## Optimization Options

### Environment Variables (ENV_OPT.md)

```
- SGLANG_USE_CUDA_IPC_TRANSPORT=1
- SGLANG_VIT_ENABLE_CUDA_GRAPH=1
- SGLANG_VISION_ATTN_FP8=1
```

### Server Arguments (SERVER_ARG_OPT.md)

```
--enable-piecewise-cuda-graph
--mm-enable-dp-encoder
--prefill-attention-backend fa3
--decode-attention-backend flashinfer
```

## Common Commands for Claude Instances

### Project Exploration

```bash
# List all files and directories
ls -la /root/AUTO_TEST/

# Read project requirements
cat /root/AUTO_TEST/[important]_project_requirement.md

# Read example workflow
cat /root/AUTO_TEST/[important]_example_workflow.md

# Check current template files
ls -la /root/AUTO_TEST/launch_server_template/
ls -la /root/AUTO_TEST/benchmark_template/
ls -la /root/AUTO_TEST/OPT/
```

### View Example Configurations

```bash
# View server launch template 1
cat /root/AUTO_TEST/launch_server_template/launch_server_template_1.md

# View server launch template 2
cat /root/AUTO_TEST/launch_server_template/launch_server_template_2.md

# View benchmark template
cat /root/AUTO_TEST/benchmark_template/benchmark_template_1.md

# View optimization options
cat /root/AUTO_TEST/OPT/ENV_OPT.md
cat /root/AUTO_TEST/OPT/SERVER_ARG_OPT.md
```

### Reference Examples

```bash
# View example benchmark report
cat /root/AUTO_TEST/benchmark_result_example.md

# View basic server launch command
cat /root/AUTO_TEST/launch_server_basic.sh

# View basic benchmark command
cat /root/AUTO_TEST/benchmark_cmd_basic.sh
```

## Development Notes

### Prerequisites

- NVIDIA GPU with CUDA 11.0+
- Python 3.8+
- SGLang framework installed
- Required libraries for benchmarks

### Notes for Claude Instances

1. **Read-only Mode:** This is a read-only exploration repository
2. **GPU Access:** Requires CUDA-enabled GPU in environment
3. **Configuration Files:** Always check the latest templates and OPT files
4. **JSON Output:** Benchmark results are usually in structured formats (JSON)
5. **SGLang Commands:** All commands use `python3 -m sglang.*` syntax

## Project Status

This is a **template/exploration project** designed to demonstrate the architecture and workflow of an automated testing system. The final implementation will include:

- Configuration generation scripts
- Service manager classes
- Benchmark orchestration logic
- Report generation modules
- Pipeline management

For the full implementation, refer to the [important]_project_requirement.md and [important]_example_workflow.md files.
