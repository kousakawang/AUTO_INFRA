# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AUTO_INFRA is a **skill-based automated benchmarking framework for AI model serving** built on the SGLang framework. It automates service launching, performance benchmarking, and report generation for LLMs and VLMs through a modular, composable skills architecture.

## Repository Structure

```
AUTO_INFRA/
├── AGENT_GUIDE.md              # Combined agent guide (usage + config reference)
├── CLAUDE.md                   # This file
├── requirements.txt
├── configs/
│   ├── templates/              # Server launch + benchmark command templates
│   │   ├── launch_server_template_1.md
│   │   ├── launch_server_template_2.md
│   │   └── benchmark_template_1.md
│   └── OPT/                   # Optimization options
│       ├── ENV_OPT.md
│       └── SERVER_ARG_OPT.md
├── examples/
│   ├── demo_config.py          # Example configuration
│   ├── skill_based_pipeline.py # Reference example (not the only entry point)
│   └── README.md
├── workflows/                  # Agent-created custom workflow scripts
├── skills/                     # Modular skills (7 total)
│   ├── config_generator/       # Generate configs from raw commands
│   ├── config_validator/       # Validate and expand configs
│   ├── service_manager/        # Launch/monitor/kill services
│   ├── benchmark_runner/       # Run benchmarks
│   ├── result_processor/       # Process and filter results
│   ├── report_generator/       # Generate reports + visualizations
│   ├── pipeline_orchestrator/  # End-to-end pipeline orchestration
│   └── README.md
├── src/                        # Core library code
│   ├── config.py
│   ├── config_generator.py
│   ├── templates.py            # Template loading (from configs/templates/ and configs/OPT/)
│   ├── service_manager.py
│   ├── benchmark_orchestrator.py
│   ├── benchmark_functions.py
│   ├── result_types.py
│   ├── result_store.py
│   ├── data_processor.py
│   ├── report_generator.py
│   └── visualization.py
├── request_case/               # User input cases
├── test_cases/                 # Generated config files
├── tests/                      # Unit tests
├── outputs/                    # Runtime outputs (JSON)
├── reports/                    # Generated reports (MD + PNG)
└── backup/                     # Archived files from pre-refactor
```

## Running the Pipeline

The **only** entry point is `examples/skill_based_pipeline.py`. The old `run_benchmark.py` has been removed.

```bash
python3 examples/skill_based_pipeline.py --config test_cases/your_config.py --example full
```

For manual skill composition:

```bash
python3 examples/skill_based_pipeline.py --config test_cases/your_config.py --example manual
```

A **dry-run mode** is available for testing without GPU access.

## Skills Architecture

The framework is built around 7 composable skills:

| Skill | Purpose |
|---|---|
| `config_generator` | Generate configs from raw server/benchmark commands |
| `config_validator` | Validate and expand user configurations |
| `service_manager` | Launch, monitor, and kill SGLang serving instances |
| `benchmark_runner` | Execute benchmark test suites |
| `result_processor` | Process results with outlier removal and filtering |
| `report_generator` | Generate markdown reports and PNG visualizations |
| `pipeline_orchestrator` | Compose skills into an end-to-end pipeline |

Each skill lives under `skills/` with its own `main.py` and `README.md`. Core library implementations are in `src/`.

## Configuration

- **Templates**: `configs/templates/` contains server launch and benchmark command templates with variable placeholders
- **Optimization options**: `configs/OPT/` contains environment variable and server argument options (`ENV_OPT.md`, `SERVER_ARG_OPT.md`)
- **Example config**: `examples/demo_config.py` shows the full configuration structure
- **Generated configs**: Placed in `test_cases/` with timestamped filenames

## Prerequisites

- Python 3.8+
- SGLang framework
- NVIDIA GPU with CUDA (not required for dry-run mode)
- Dependencies listed in `requirements.txt`

## Key References

- **AGENT_GUIDE.md** — Detailed usage instructions, skill descriptions, and full configuration reference
- **examples/README.md** — Examples and entry point documentation
- **skills/README.md** — Overview of the skills architecture
- **backup/** — Archived pre-refactor files (for reference only)
