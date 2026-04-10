# pipeline_orchestrator Skill

Run the complete end-to-end benchmark pipeline (for backward compatibility).

## Purpose
This skill runs the complete benchmark pipeline, just like the original `run_benchmark.py`. Use this when you need to:
- Run the full standard pipeline with a single function call
- Maintain backward compatibility with existing config files
- Run everything in one go (launch services, run benchmarks, generate report)

## Key Functions

### `PipelineOrchestratorSkill(config_dict: dict)`
Main skill class that orchestrates the complete pipeline.

**Methods:**

#### `.run(dry_run: bool = False) -> BenchmarkSuiteResult`
Run the complete benchmark pipeline.

**Args:**
- `dry_run`: If True, don't actually launch services or run benchmarks

**Returns:**
- `BenchmarkSuiteResult` with all results

---

## Convenience Functions

### `run_pipeline(config_dict: dict, dry_run: bool = False) -> BenchmarkSuiteResult`
Run the complete benchmark pipeline from a config dict.

**Args:**
- `config_dict`: Configuration dictionary with user_config and pipeline_config
- `dry_run`: If True, don't actually execute

**Returns:**
- `BenchmarkSuiteResult`

**Example:**
```python
from skills.pipeline_orchestrator import run_pipeline
from skills.config_validator import load_config_from_file

config_dict = load_config_from_file("examples/demo_config.py")
result = run_pipeline(config_dict, dry_run=True)
```

---

### `run_pipeline_from_file(filepath: str, dry_run: bool = False) -> BenchmarkSuiteResult`
Run the complete benchmark pipeline from a config file.

**Args:**
- `filepath`: Path to config file
- `dry_run`: If True, don't actually execute

**Returns:**
- `BenchmarkSuiteResult`

**Example:**
```python
from skills.pipeline_orchestrator import run_pipeline_from_file

result = run_pipeline_from_file("examples/demo_config.py", dry_run=True)
```

## What This Skill Does

The pipeline orchestrator runs these steps in order:

1. **Validate configuration** - Check that all required fields are present
2. **Expand configuration** - Convert simple user config to full execution config
3. **Load templates** - Load server launch and benchmark templates
4. **Initialize components** - Set up service manager and benchmark orchestrator
5. **Run execution** - Launch services (max 2 at once), run benchmarks, clean up
6. **Save results** - Store raw results in JSON format
7. **Generate report** - Create markdown report with visualizations

## Example Usage

```python
from skills.pipeline_orchestrator import run_pipeline_from_file

# Run dry-run first to verify
print("Running dry-run...")
result = run_pipeline_from_file("examples/demo_config.py", dry_run=True)

# When ready, run for real
# print("Running real benchmark...")
# result = run_pipeline_from_file("examples/demo_config.py", dry_run=False)

print(f"Total services: {len(result.service_results)}")
print(f"Total benchmarks: {sum(len(sr.results) for sr in result.service_results)}")
```

## Backward Compatibility

This skill is fully backward compatible. You can use it exactly like the original `run_benchmark.py`:

**Original way:**
```bash
python3 run_benchmark.py --config examples/demo_config.py --dry-run
```

**New skill way (Python):**
```python
from skills.pipeline_orchestrator import run_pipeline_from_file
run_pipeline_from_file("examples/demo_config.py", dry_run=True)
```

## When to Use This Skill
1. **When you just want to run the standard pipeline** - No need for custom workflow
2. **For backward compatibility** - Works with existing config files
3. **When you don't need fine-grained control** - Let the orchestrator handle everything

## When NOT to Use This Skill

If you need flexibility, use the individual skills instead:
- **SLO optimization** - Use service_manager + benchmark_runner directly
- **Parameter search** - Use service_manager + benchmark_runner + result_processor
- **Custom workflows** - Compose skills as needed

## See Also
- `skills/config_validator/README.md` - First step: load configs
- `AGENT_GUIDELINES.md` - Complete guide with flexible workflow patterns
