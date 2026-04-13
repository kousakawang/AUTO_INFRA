"""
Pipeline Orchestrator Skill - Main implementation.
Runs the complete end-to-end benchmark pipeline using all skills together.
"""
import os
import sys
import time

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from src.result_types import BenchmarkSuiteResult, ServiceResult
from src.result_store import ResultStore
from skills.config_validator import load_and_validate_config, load_config_from_file, validate_config, expand_config
from skills.service_manager import ServiceManagerSkill
from skills.benchmark_runner import BenchmarkRunnerSkill
from skills.report_generator import ReportGeneratorSkill


class PipelineOrchestratorSkill:
    """
    Skill that orchestrates the complete benchmark pipeline
    using individual skills (config_validator, service_manager,
    benchmark_runner, report_generator).
    """
    def __init__(self, config_dict: dict):
        self.config_dict = config_dict

    def run(self, dry_run: bool = False) -> BenchmarkSuiteResult:
        print("=" * 70)
        print("AI Model Serving Benchmark Pipeline (Skill-Based)")
        print("=" * 70)
        print()

        is_valid, errors = validate_config(self.config_dict)
        if not is_valid:
            print("Validation errors:")
            for err in errors:
                print(f"   - {err}")
            raise ValueError("Invalid configuration")

        full_config = expand_config(self.config_dict)

        from src.templates import TemplateLoader
        template_loader = TemplateLoader(project_root)
        template_loader.load_all()

        service_skill = ServiceManagerSkill(template_loader, full_config)
        benchmark_skill = BenchmarkRunnerSkill(template_loader, full_config)
        report_skill = ReportGeneratorSkill(template_loader=template_loader)
        result_store = ResultStore()

        suite_result = BenchmarkSuiteResult(config=self.config_dict, start_time=time.time())

        try:
            max_concurrent = full_config.pipeline_config.get("max_existed_service_num", 2)
            pending_services = list(full_config.services)
            active_instances = {}

            mode = "DRY RUN" if dry_run else "REAL EXECUTION"
            print(f"Running {len(pending_services)} services (max concurrent: {max_concurrent}) [{mode}]")
            print()

            while pending_services or active_instances:
                while pending_services and len(active_instances) < max_concurrent:
                    service_config = pending_services.pop(0)
                    print(f"--- Launching service {service_config.global_id} "
                          f"(pending: {len(pending_services)}, active: {len(active_instances)}/{max_concurrent}) ---")

                    instance = service_skill.launch_service(service_config, dry_run=dry_run)
                    print(f"   Launched service {instance.global_id} (port {instance.port})")
                    if dry_run:
                        print(f"   Command: {instance.launch_command[:100]}...")

                    ready = service_skill.wait_for_ready(instance, dry_run=dry_run)
                    if ready:
                        print(f"   Service {instance.global_id} is ready!")
                        active_instances[instance.global_id] = instance
                    else:
                        print(f"   Service {instance.global_id} failed to become ready")
                        service_skill.kill_service(instance, dry_run=dry_run)

                if active_instances:
                    global_id, instance = next(iter(active_instances.items()))
                    service_config = full_config.services[global_id]

                    print(f"\n--- Running benchmarks for service {global_id} ---")
                    service_result = ServiceResult(
                        service_global_id=instance.global_id,
                        model_path=instance.model_path,
                        port=instance.port,
                        start_time=time.time()
                    )

                    for case in service_config.benchmark_cases:
                        per_config_times = full_config.pipeline_config.get("per_config_benchmark_times", 5)
                        for run_idx in range(per_config_times):
                            result = benchmark_skill.run_benchmark(
                                instance._core_instance, case, run_idx, dry_run=dry_run
                            )
                            service_result.results.append(result)
                            status = "✓" if result.success else "✗"
                            print(f"     Run {run_idx+1}: {status} {result.total_token_throughput:.2f} tok/s")

                    service_result.end_time = time.time()
                    suite_result.service_results.append(service_result)

                    print(f"\n   Killing service {global_id}...")
                    service_skill.kill_service(instance, dry_run=dry_run)
                    del active_instances[global_id]
                    print(f"   Service {global_id} completed\n")

                if not dry_run:
                    time.sleep(0.1)

        finally:
            print("\n--- Cleaning up all services ---")
            service_skill.cleanup_all(dry_run=dry_run)

        suite_result.end_time = time.time()
        result_path = result_store.save_suite_result(suite_result)
        print(f"   Results saved to: {result_path}")

        report_path = report_skill.generate_report(suite_result)
        print(f"   Report generated at: {report_path}")

        print("\n" + "=" * 70)
        print("Pipeline complete!")
        print("=" * 70)

        return suite_result


def run_pipeline(config_dict: dict, dry_run: bool = False) -> BenchmarkSuiteResult:
    orchestrator = PipelineOrchestratorSkill(config_dict)
    return orchestrator.run(dry_run=dry_run)


def run_pipeline_from_file(filepath: str, dry_run: bool = False) -> BenchmarkSuiteResult:
    config_dict = load_config_from_file(filepath)
    return run_pipeline(config_dict, dry_run=dry_run)
