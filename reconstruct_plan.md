# AUTO_INFRA Reconstruction Plan

## Context

The AUTO_INFRA project is currently an automated AI model serving benchmark framework with a monolithic pipeline architecture. The goal is to break it down into modular, reusable skills that can be called by an agent autonomously to accomplish flexible tasks beyond fixed workflows.

### Current Architecture
The monolithic pipeline (`src/main.py`) currently handles:
1. Configuration loading and validation
2. Configuration expansion
3. Template loading
4. Service launching and management
5. Benchmark orchestration
6. Result collection and storage
7. Report generation with visualization

### Reconstruction Goal
Transform into a skill-based architecture where:
- Each stage is a standalone Claude Code skill
- Agent can compose skills dynamically based on task requirements
- Enables flexible scenarios like SLO-based throughput optimization, parameter search, etc.

---

## Stage 1: Skill Breakdown and Implementation

### Skill 1: Config Generator (Already Exists)
**Path:** `skills/config_generator/`
**Status:** Already implemented ✓
**Purpose:** Parse raw commands/requirements into config files
**Entry Point:** `skills/generate_config.py`

### Skill 2: Config Validator
**Path:** `skills/config_validator/`
**Purpose:** Validate and expand configuration files
**Key Functions:**
- Validate user_config against schema
- Expand config using ConfigExpander
- Load templates and OPT files
**Input:** Config dict or file path
**Output:** Expanded FullConfig object
**Reuses:** `src/config.py`, `src/config_generator.py`, `src/templates.py`

### Skill 3: Service Manager
**Path:** `skills/service_manager/`
**Purpose:** Launch, monitor, and terminate model serving services
**Key Functions:**
- Launch service from ServiceConfig
- Wait for service readiness
- Kill running services
- Cleanup all services
**Input:** ServiceConfig, dry_run flag
**Output:** ServiceInstance object
**Reuses:** `src/service_manager.py`

### Skill 4: Benchmark Runner
**Path:** `skills/benchmark_runner/`
**Purpose:** Run benchmarks on active services
**Key Functions:**
- Generate benchmark commands
- Run single benchmark case
- Run all benchmarks for a service
- Parse benchmark output
**Input:** ServiceInstance, BenchmarkCase(s)
**Output:** BenchmarkResult / ServiceResult
**Reuses:** `src/benchmark_orchestrator.py`, `src/benchmark_functions.py`

### Skill 5: Result Processor
**Path:** `skills/result_processor/`
**Purpose:** Process and aggregate benchmark results
**Key Functions:**
- Remove min/max outliers
- Calculate averages/statistics
- Apply SLO filters
- Group results by dimensions
**Input:** List of BenchmarkResult
**Output:** Aggregated statistics
**Reuses:** `src/data_processor.py`, `src/result_types.py`

### Skill 6: Report Generator
**Path:** `skills/report_generator/`
**Purpose:** Generate visualizations and reports
**Key Functions:**
- Create visualizations (bar charts, etc.)
- Generate markdown reports
- Save reports to files
**Input:** BenchmarkSuiteResult
**Output:** Report file path
**Reuses:** `src/report_generator.py`, `src/visualization.py`

### Skill 7: Pipeline Orchestrator (Simple Runner)
**Path:** `skills/pipeline_orchestrator/`
**Purpose:** Run the full end-to-end pipeline (for backward compatibility)
**Key Functions:**
- Orchestrate all skills in sequence
- Manage service queue and concurrency
**Input:** Config dict
**Output:** BenchmarkSuiteResult
**Reuses:** `src/main.py`, `src/service_queue.py`

---

## Stage 1 Implementation Steps

### Step 1.1: Create Skill Directories and Base Structure
Create skill package structure for each new skill:
```
skills/
├── config_validator/
│   ├── __init__.py
│   └── main.py
├── service_manager/
│   ├── __init__.py
│   └── main.py
├── benchmark_runner/
│   ├── __init__.py
│   └── main.py
├── result_processor/
│   ├── __init__.py
│   └── main.py
├── report_generator/
│   ├── __init__.py
│   └── main.py
└── pipeline_orchestrator/
    ├── __init__.py
    └── main.py
```

### Step 1.2: Extract Core Logic to Skills
For each skill:
1. Copy relevant code from `src/` into the skill
2. Create clean API functions
3. Add proper error handling
4. Add docstrings
5. Make it importable and callable

### Step 1.3: Refactor src/ to Use Skills
Update existing src/ modules to import from skills instead of duplicating code:
- Keep type definitions in `src/result_types.py`
- Keep data classes in `src/config_generator.py` (ServiceConfig, etc.)
- Refactor `src/main.py` to use the pipeline_orchestrator skill

### Step 1.4: Create Example Script
Create `examples/skill_based_pipeline.py` that demonstrates:
- Calling skills in sequence
- How to compose them for a complete pipeline
- Dry-run and real execution modes

### Step 1.5: Test the Implementation
1. Run existing test cases with `run_benchmark.py --dry-run`
2. Run with new skill-based script in dry-run mode
3. Verify dry-run results are identical (commands generated, mock output, etc.)
4. No real GPU execution needed - dry-run verification is sufficient

---

## Stage 2: Agent Guidelines and Documentation

### 2.1: Agent Usage Guide
Create `AGENT_GUIDELINES.md` that teaches the agent:
- What each skill does
- When to use each skill
- Skill input/output formats
- How to compose skills for different tasks

### 2.2: Example Scenarios
Document concrete examples:

**Scenario A: SLO-based Throughput Optimization**
```
Goal: Find max throughput under TTFT <= 100ms, TPOT <= 20ms
Steps:
1. Use config_generator to create base config
2. Use config_validator to validate and get FullConfig
3. Use service_manager to launch service once
4. Loop with increasing max_concurrency:
   - Create BenchmarkCase with current concurrency
   - Use benchmark_runner to run single benchmark case
   - Use result_processor to check SLO compliance
   - If SLO satisfied, keep track of throughput; else, break loop
5. Use service_manager to kill service
6. Use report_generator to create optimization report with best throughput found
```

**Scenario B: Parameter Search**
```
Goal: Find best server_args_opt for throughput
Steps:
1. Generate configs with different server_args_opt
2. For each:
   - Launch service
   - Run benchmarks
   - Collect results
3. Compare and recommend best option
```

### 2.3: Skill Reference Documentation
For each skill, document:
- Purpose and use cases
- Function signatures
- Input parameters
- Return values
- Example usage

---

## Critical Files to Modify/Create

### New Files:
- `skills/config_validator/main.py`
- `skills/service_manager/main.py`
- `skills/benchmark_runner/main.py`
- `skills/result_processor/main.py`
- `skills/report_generator/main.py`
- `skills/pipeline_orchestrator/main.py`
- `examples/skill_based_pipeline.py`
- `AGENT_GUIDELINES.md`

### Modified Files:
- `src/main.py` - Refactor to use skills
- `run_benchmark.py` - May need minor updates
- Existing skills may need minor tweaks

### Kept as-is (Core Types):
- `src/result_types.py` - Data classes for results
- `src/config_generator.py` - ServiceConfig, FullConfig, etc.
- `src/templates.py` - Template loading
- `src/result_store.py` - Result persistence

---

## Verification Plan

**Important:** Only dry-run verification is needed - no real GPU execution required.

1. **Backward Compatibility:** Existing `run_benchmark.py --dry-run` produces identical output as before
2. **Skill Independence:** Each skill can be called individually in dry-run mode
3. **Dry-run Result Consistency:** Both monolithic and skill-based pipelines produce:
   - Identical generated commands (server launch and benchmark)
   - Identical mock benchmark output
   - Identical reports (when using same random seed)
4. **Dry-run Support:** All skills support dry-run mode parameter
5. **Error Handling:** Skills handle errors gracefully and return meaningful messages

---

## Expected Outcome

After reconstruction:
- Agent can understand and use each skill independently
- Agent can compose skills for flexible tasks (SLO optimization, parameter search)
- Codebase is more modular and maintainable
- Backward compatibility preserved
- Clear documentation for agent guidance
