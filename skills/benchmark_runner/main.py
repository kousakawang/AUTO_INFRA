"""
Benchmark Runner Skill - Main implementation.
Runs benchmarks on active services and parses results.
"""
import os
import sys
import time
from typing import List, Optional

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from src.config_generator import ServiceConfig, BenchmarkCase, FullConfig
from src.templates import TemplateLoader, CommandGenerator
from src.benchmark_orchestrator import BenchmarkOrchestrator as CoreBenchmarkOrchestrator
from src.result_types import BenchmarkResult, ServiceResult
from src.service_manager import ServiceInstance as CoreServiceInstance


def create_benchmark_case(case_id: int, input_len: int, output_len: int,
                          image_size: str, image_count: int, max_concurrency: int,
                          num_prompts: Optional[int] = None) -> BenchmarkCase:
    """
    Create a BenchmarkCase with automatic num_prompts calculation.

    Args:
        case_id: Case identifier
        input_len: Input token length
        output_len: Output token length
        image_size: Image resolution (e.g., "448x448")
        image_count: Number of images per prompt
        max_concurrency: Maximum concurrency
        num_prompts: Number of prompts (default: max_concurrency * 6)

    Returns:
        BenchmarkCase object
    """
    if num_prompts is None:
        num_prompts = max_concurrency * 6

    return BenchmarkCase(
        case_id=case_id,
        input_len=input_len,
        output_len=output_len,
        image_size=image_size,
        image_count=image_count,
        max_concurrency=max_concurrency,
        num_prompts=num_prompts
    )


class BenchmarkRunnerSkill:
    """
    Skill wrapper for benchmark runner operations.
    """
    def __init__(self, template_loader: TemplateLoader, full_config: Optional[FullConfig] = None):
        self.template_loader = template_loader
        self.command_generator = CommandGenerator(template_loader)

        if full_config is None:
            from src.config_generator import FullConfig
            full_config = FullConfig()
            full_config.pipeline_config = {"per_config_benchmark_times": 5}

        self.core_orchestrator = CoreBenchmarkOrchestrator(full_config, self.command_generator)

    def generate_benchmark_command(self, service_config: ServiceConfig,
                                    benchmark_case: BenchmarkCase) -> str:
        """Generate the benchmark command without running it."""
        return self.command_generator.generate_benchmark_command(service_config, benchmark_case)

    def run_benchmark(self, core_service_instance: CoreServiceInstance,
                      case: BenchmarkCase, run_index: int = 0,
                      dry_run: bool = False, mock_output: Optional[str] = None) -> BenchmarkResult:
        """
        Run a single benchmark on a service.

        Args:
            core_service_instance: Core ServiceInstance from service_manager
            case: BenchmarkCase to run
            run_index: Index of this run (for multiple runs per case)
            dry_run: If True, don't actually run
            mock_output: Mock output to use for dry-run

        Returns:
            BenchmarkResult with results
        """
        return self.core_orchestrator.run_benchmark(
            core_service_instance, case, run_index, dry_run=dry_run, mock_output=mock_output
        )

    def run_all_benchmarks_for_service(self, core_service_instance: CoreServiceInstance,
                                        dry_run: bool = False) -> ServiceResult:
        """
        Run all benchmarks for a service (as defined in its service_config).

        Args:
            core_service_instance: Core ServiceInstance
            dry_run: If True, don't actually run

        Returns:
            ServiceResult with all benchmark results
        """
        return self.core_orchestrator.run_all_benchmarks_for_service(
            core_service_instance, dry_run=dry_run
        )


# Global state for convenience functions
_global_runner: Optional[BenchmarkRunnerSkill] = None


def _get_runner(template_loader: Optional[TemplateLoader] = None) -> BenchmarkRunnerSkill:
    """Get or create global runner instance."""
    global _global_runner
    if _global_runner is None:
        if template_loader is None:
            template_loader = TemplateLoader(project_root)
            template_loader.load_all()
        _global_runner = BenchmarkRunnerSkill(template_loader)
    return _global_runner


def run_benchmark(core_service_instance: CoreServiceInstance, case: BenchmarkCase,
                  run_index: int = 0, template_loader: Optional[TemplateLoader] = None,
                  dry_run: bool = False) -> BenchmarkResult:
    """
    Run a single benchmark (convenience function).

    Args:
        core_service_instance: Core ServiceInstance
        case: BenchmarkCase to run
        run_index: Run index
        template_loader: Optional template loader
        dry_run: If True, don't actually run

    Returns:
        BenchmarkResult
    """
    runner = _get_runner(template_loader)
    return runner.run_benchmark(core_service_instance, case, run_index, dry_run=dry_run)


def run_all_benchmarks_for_service(core_service_instance: CoreServiceInstance,
                                    template_loader: Optional[TemplateLoader] = None,
                                    dry_run: bool = False) -> ServiceResult:
    """
    Run all benchmarks for a service (convenience function).

    Args:
        core_service_instance: Core ServiceInstance
        template_loader: Optional template loader
        dry_run: If True, don't actually run

    Returns:
        ServiceResult
    """
    runner = _get_runner(template_loader)
    return runner.run_all_benchmarks_for_service(core_service_instance, dry_run=dry_run)
