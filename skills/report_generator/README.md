# report_generator Skill

Generate visualizations and comprehensive reports from benchmark results.

## Purpose
This skill generates markdown reports with visualizations from benchmark results. Use this when you need to:
- Create comprehensive markdown reports
- Generate throughput and latency visualizations
- Document benchmark findings
- Compare different configurations

## Key Class: `ReportGeneratorSkill`

### `ReportGeneratorSkill(reports_dir: str = "reports", do_visualize: bool = True, slo_ttft_max: float = 1e8, slo_tpot_max: float = 1e8, data_watch_policy: str = "remove_min_max", template_loader: Optional[TemplateLoader] = None)`
Main skill class for report generation.

**Args:**
- `reports_dir`: Directory to save reports (default: "reports")
- `do_visualize`: Whether to generate visualizations (default: True)
- `slo_ttft_max`: Maximum TTFT for SLO filtering in report
- `slo_tpot_max`: Maximum TPOT for SLO filtering in report
- `data_watch_policy`: Policy for outlier removal
- `template_loader`: Template loader for OPT explanations

**Methods:**

---

#### `.generate_report(suite_result: BenchmarkSuiteResult, report_name: Optional[str] = None) -> str`
Generate a complete report from benchmark results.

**Args:**
- `suite_result`: The benchmark suite result to report on
- `report_name`: Optional name for the report (without extension)

**Returns:**
- Path to the generated markdown report

**Example:**
```python
from skills.report_generator import ReportGeneratorSkill

report_skill = ReportGeneratorSkill(
    reports_dir="reports",
    do_visualize=True,
    slo_ttft_max=100.0,
    slo_tpot_max=20.0,
    template_loader=template_loader
)

report_path = report_skill.generate_report(suite_result)
print(f"Report generated at: {report_path}")
```

---

## Convenience Function

### `generate_report(suite_result: BenchmarkSuiteResult, reports_dir: str = "reports", do_visualize: bool = True, slo_ttft_max: float = 1e8, slo_tpot_max: float = 1e8, data_watch_policy: str = "remove_min_max", template_loader: Optional[TemplateLoader] = None, report_name: Optional[str] = None) -> str`
Generate a report from benchmark results (convenience function).

## What the Report Includes

The generated markdown report contains:

1. **SLO Criteria** - What TTFT/TPOT thresholds were applied
2. **Group Results** - Results grouped by model, config, and parameters:
   - Throughput comparison table
   - TTFT and TPOT latency metrics
   - Visualization plot (if do_visualize=True)
   - Configuration details with OPT explanations
3. **Configuration Details** - What env_opt, server_args_opt, and additional options were used for each configuration

## Example Usage: End-to-End

```python
from skills.config_validator import load_and_validate_config
from skills.pipeline_orchestrator import run_pipeline_from_file
from skills.report_generator import generate_report

# Option 1: Use pipeline orchestrator to get suite_result
suite_result = run_pipeline_from_file("examples/demo_config.py", dry_run=True)

# Option 2: Or load existing result from ResultStore
# from src.result_store import ResultStore
# store = ResultStore()
# suite_result = store.load_latest_suite_result()

# Generate report
full_config, template_loader, config_dict = load_and_validate_config("examples/demo_config.py")

report_path = generate_report(
    suite_result,
    reports_dir="reports",
    do_visualize=True,
    slo_ttft_max=100.0,
    slo_tpot_max=20.0,
    template_loader=template_loader
)

print(f"Report saved to: {report_path}")
```

## When to Use This Skill
1. **At the end of a benchmark run** - Document the findings
2. **After an optimization search** - Show the best configuration found
3. **When comparing multiple options** - Create visual comparisons
4. **For documentation** - Save results for future reference

## See Also
- `skills/result_processor/README.md` - Process results before reporting
- `skills/pipeline_orchestrator/README.md` - Full pipeline includes report generation
- `AGENT_GUIDELINES.md` - Complete usage guide
