# Skill-Based AUTO_INFRA Quick Start Guide

## Overview

The AUTO_INFRA project has been reconstructed into modular, composable skills. You can use the project in backward-compatible mode or use the individual skills for flexible workflows.

## Quick Start

### Option 1: Backward Compatible (Original Pipeline)

```bash
# Run exactly like before
python3 run_benchmark.py --config examples/demo_config.py --dry-run
```

### Option 2: Use Skill-Based Pipeline

```bash
# Full pipeline via orchestrator skill
python3 examples/skill_based_pipeline.py --config examples/demo_config.py --example full

# Manual skill composition demo
python3 examples/skill_based_pipeline.py --config examples/demo_config.py --example manual

# See SLO optimization pattern sketch
python3 examples/skill_based_pipeline.py --config examples/demo_config.py --example slo-sketch
```

## Available Skills

| Skill | Purpose | Documentation |
|-------|---------|----------------|
| config_validator | Load, validate, expand configs | `skills/config_validator/README.md` |
| service_manager | Launch/manage services | `skills/service_manager/README.md` |
| benchmark_runner | Run benchmarks | `skills/benchmark_runner/README.md` |
| result_processor | Filter/aggregate results | `skills/result_processor/README.md` |
| report_generator | Generate reports | `skills/report_generator/README.md` |
| pipeline_orchestrator | Full pipeline | `skills/pipeline_orchestrator/README.md` |
| config_generator | Parse raw commands | `skills/config_generator/README.md` (existing) |

## Agent Usage

For full documentation on how to compose skills for flexible tasks like:
- SLO-based throughput optimization
- Parameter search
- Custom benchmark workflows

See:
- **`AGENT_GUIDELINES.md`** - Complete agent guide with patterns and examples
- **`examples/skill_based_pipeline.py`** - Runnable code examples

## Directory Structure

```
AUTO_INFRA/
├── skills/                    # All skills here
│   ├── config_validator/
│   ├── service_manager/
│   ├── benchmark_runner/
│   ├── result_processor/
│   ├── report_generator/
│   ├── pipeline_orchestrator/
│   └── config_generator/      # (pre-existing)
├── examples/
│   └── skill_based_pipeline.py  # Skill usage examples
├── src/                       # Core modules (unchanged)
├── AGENT_GUIDELINES.md        # Full agent documentation
└── skill_based_quickstart.md  # This file
```
