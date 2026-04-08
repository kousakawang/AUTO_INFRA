# Development Plan: AI Model Serving Benchmark Framework

## Context

This project is an **automated testing and benchmarking framework** for AI model serving systems using SGLang. Currently, it only contains template files, documentation, and configuration examples - no actual implementation code exists yet. The goal is to build a complete system that can:
- Launch multiple model serving instances with different configurations
- Run benchmark tests on each instance
- Collect and aggregate results (focus on Total token throughput)
- Generate visual reports

## Architecture Overview

The system will be built in Python with three main modules:

1. **Service Manager** - Handles server lifecycle (launch/kill)
2. **Benchmark Orchestrator** - Runs benchmark tests on active servers
3. **Report Generator** - Aggregates results and creates visualizations

## Implementation Plan

### Phase 1: Core Infrastructure & Configuration

**Files to create:**
- `src/config.py` - Configuration handling and validation
- `src/config_generator.py` - Expands simple user config to full config
- `src/templates.py` - Template loading and variable substitution

**Key functionality:**
- Load and validate user configuration (Python dict/YAML/JSON)
- Auto-expand benchmark configs (repeat last value if needed)
- Load templates from `launch_server_template/` and `benchmark_template/`
- Load optimization options from `OPT/`
- Substitute variables in templates to generate actual commands

### Phase 2: Service Manager

**Files to create:**
- `src/service_manager.py` - Service lifecycle management
- `src/service_queue.py` - Queue of pending/active services

**Key functionality:**
- Generate full launch commands from config + templates
- Launch server processes with proper environment variables
- Track active services by port and global ID
- Kill services when benchmarking complete
- Maintain `max_existed_service_num` concurrent services
- Poll for service readiness before benchmarking

### Phase 3: Benchmark Orchestrator

**Files to create:**
- `src/benchmark_orchestrator.py` - Benchmark execution logic
- `src/benchmark_functions.py` - Individual benchmark function generators

**Key functionality:**
- Generate benchmark commands from config + templates
- Calculate `num-prompts = prompt_num_dvide_max_concurrency * max_concurrency`
- Run each benchmark `per_config_benchmark_times` times
- Capture benchmark output (JSON format preferred)
- Extract and store **Total token throughput (tok/s)** with service ID and benchmark config
- Notify service manager when benchmarking complete

### Phase 4: Result Collection & Storage

**Files to create:**
- `src/result_store.py` - Data storage and retrieval
- `src/data_processor.py` - Outlier removal and aggregation

**Key functionality:**
- Store benchmark results in structured format (Total token throughput only)
- Apply `remove_min_max` policy when calculating averages
- Group results by: model, benchmark config, template ID, deploy method
- Calculate aggregated Total token throughput metrics

### Phase 5: Report Generator

**Files to create:**
- `src/report_generator.py` - Markdown/HTML report generation
- `src/visualization.py` - Chart/plot generation (using matplotlib/seaborn)

**Key functionality:**
- Create comparison tables for grouped results (Total token throughput only)
- Generate plots with x-axis = optimization options, y-axis = Total token throughput (tok/s)
- Export full report in Markdown + HTML format
- (Optional) Real-time visualization dashboard
- Respect `do_visuallize` option: skip visualization and report generation when False
- Filter results using `SLO` thresholds: only include data where TTFT <= TTFT_MAX and TPOT <= TPOT_MAX

### Phase 6: Main Pipeline & CLI

**Files to create:**
- `src/main.py` - Main pipeline orchestration
- `run_benchmark.py` - Entry point script

**Key functionality:**
- End-to-end pipeline: config → launch → benchmark → report
- Signal handling between modules
- Progress tracking and logging
- Single-command execution interface

## Critical Files to Reference

**Existing template files:**
- `launch_server_template/launch_server_template_1.md` - Server command template
- `benchmark_template/benchmark_template_1.md` - Benchmark command template
- `OPT/ENV_OPT.md` - Environment variable optimizations
- `OPT/SERVER_ARG_OPT.md` - Server argument optimizations

**Example files:**
- `launch_server_basic.sh` - Example server launch command
- `benchmark_cmd_basic.sh` - Example benchmark command
- `benchmark_result_example.md` - Example output format

## Data Flow

```
User Config (simple)
    ↓
[Config Generator]
    ↓
Full Config
    ↓
[Service Queue] → [Service Manager] ← (launch/kill)
    ↓                    ↓
[Benchmark Orchestrator] ← (extract Total token throughput)
    ↓
[Result Store]
    ↓
[Data Processor]
    ↓
[Report Generator]
    ↓
Final Report (Total Throughput Tables + Plots)
```

## Configuration Format

Use Python dictionary format (as shown in [important]_example_workflow.md), with support for YAML/JSON import/export.

**Key pipeline_config additions:**
- `do_visuallize` (Boolean): If False, skip visualization and report generation
- `SLO` (List[float, float]): [TTFT_MAX, TPOT_MAX] - report only includes data where TTFT <= TTFT_MAX and TPOT <= TPOT_MAX

## Verification Plan

1. **Unit Tests** - Test each module in isolation
2. **Integration Test** - End-to-end pipeline with mock commands
3. **Dry Run Mode** - Generate commands without executing
4. **Actual GPU Test** - Run on real GPU with small model

## Recommended Tech Stack

- **Language:** Python 3.8+
- **Process Management:** `subprocess` with proper signal handling
- **Data Storage:** JSON files + optional SQLite
- **Visualization:** `matplotlib` + `seaborn`
- **Configuration:** `pydantic` for validation (optional but recommended)
- **Logging:** Standard `logging` module

## Project Decision: Develop as Total Project

This framework will be developed as a **complete, standalone Python project** rather than wrapped as skills. Reasons:
- Complex interconnected modules requiring state management and coordination
- Clear sequential data flow pipeline
- Better maintainability, testability, and reusability
- Can be used in different contexts beyond Claude Code CLI

Helper skills may be added later for common tasks, but core is a proper Python project.
