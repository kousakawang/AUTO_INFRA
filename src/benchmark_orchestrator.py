"""
Benchmark Orchestrator - Manages benchmark execution on running services.
"""
import subprocess
import logging
import time
from typing import List, Optional

from .config_generator import ServiceConfig, BenchmarkCase, FullConfig
from .templates import CommandGenerator
from .service_manager import ServiceInstance
from .result_types import BenchmarkResult, ServiceResult
from .benchmark_functions import parse_benchmark_output, generate_mock_benchmark_output

logger = logging.getLogger(__name__)


class BenchmarkOrchestrator:
    """
    Orchestrates benchmark execution on running services.

    Generates benchmark commands, runs them, and parses the results.
    """

    def __init__(self, full_config: FullConfig, command_generator: CommandGenerator):
        self.full_config = full_config
        self.command_generator = command_generator
        self.results: List[BenchmarkResult] = []
        self.per_config_benchmark_times = full_config.pipeline_config.get(
            "per_config_benchmark_times", 5
        )

    def run_benchmark(
        self,
        service: ServiceInstance,
        case: BenchmarkCase,
        run_index: int,
        dry_run: bool = False,
        mock_output: Optional[str] = None,
    ) -> BenchmarkResult:
        """
        Run a single benchmark on a service.

        Args:
            service: Service instance to benchmark
            case: Benchmark case configuration
            run_index: Index of this run (for multiple runs per case)
            dry_run: If True, don't actually run the benchmark
            mock_output: Mock output to use for testing (dry_run only)

        Returns:
            BenchmarkResult with the results
        """
        result = BenchmarkResult(
            service_global_id=service.global_id,
            case_id=case.case_id,
            run_id=run_index,
            model_path=service.model_path,
            input_len=case.input_len,
            output_len=case.output_len,
            image_size=case.image_size,
            image_count=case.image_count,
            max_concurrency=case.max_concurrency,
        )

        # Set service configuration info if available
        if service.service_config:
            result.template_id = service.service_config.template_id
            result.env_opt_ids = service.service_config.env_opt_ids
            result.server_args_opt_ids = service.service_config.server_args_opt_ids
            result.additional_options = service.service_config.additional_options
            result.deploy_method = service.service_config.deploy_method

        logger.info(
            f"Service {service.global_id}: Running benchmark case {case.case_id}, "
            f"run {run_index + 1}/{self.per_config_benchmark_times}"
        )

        # Generate benchmark command
        command = self.command_generator.generate_benchmark_command(
            service.service_config, case
        )
        logger.info(f"Service {service.global_id}: Benchmark command: {command}")

        if dry_run:
            logger.info(f"Service {service.global_id}: Dry run - not executing benchmark")
            if mock_output is None:
                # Generate deterministic mock output based on parameters
                base_throughput = 3000 + (case.max_concurrency * 10)
                mock_output = generate_mock_benchmark_output(
                    total_token_throughput=base_throughput + (run_index * 5),
                    request_throughput=10 + (case.max_concurrency * 0.1),
                )
            parse_benchmark_output(mock_output, result)
            result.success = True
            self.results.append(result)
            return result

        # Actually run the benchmark
        try:
            logger.info(f"Service {service.global_id}: Executing benchmark...")
            start_time = time.time()

            print(f"run this command in subprocess {command}")
            # Use simple subprocess without line buffering to avoid blocking
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )

            output, _ = process.communicate()
            print(f"command executed finished {command}")
            elapsed = time.time() - start_time

            logger.info(f"Service {service.global_id}: Benchmark completed in {elapsed:.1f}s")

            # Parse the output
            parse_benchmark_output(output, result)

            if result.success:
                logger.info(
                    f"Service {service.global_id}: Total token throughput: "
                    f"{result.total_token_throughput:.2f} tok/s"
                )
            else:
                logger.warning(f"Service {service.global_id}: Benchmark may have failed")

        except Exception as e:
            logger.error(f"Service {service.global_id}: Benchmark failed - {e}")
            result.success = False
            result.error_message = str(e)

        self.results.append(result)
        return result

    def run_all_benchmarks_for_service(
        self,
        service: ServiceInstance,
        dry_run: bool = False,
    ) -> ServiceResult:
        """
        Run all benchmarks for a single service.

        Args:
            service: Service instance to benchmark
            dry_run: If True, don't actually run benchmarks

        Returns:
            ServiceResult with all benchmark results for this service
        """
        service_result = ServiceResult(
            service_global_id=service.global_id,
            model_path=service.model_path,
            port=service.port,
            start_time=time.time(),
        )

        if not service.service_config:
            logger.error(f"Service {service.global_id}: No service_config available")
            service_result.end_time = time.time()
            return service_result

        logger.info(f"Service {service.global_id}: Starting benchmarks")

        for case in service.service_config.benchmark_cases:
            for run_idx in range(self.per_config_benchmark_times):
                result = self.run_benchmark(
                    service=service,
                    case=case,
                    run_index=run_idx,
                    dry_run=dry_run,
                )
                service_result.results.append(result)

                # Small delay between runs to let things settle
                if not dry_run and run_idx < self.per_config_benchmark_times - 1:
                    time.sleep(1.0)

        service_result.end_time = time.time()
        total_duration = service_result.end_time - service_result.start_time
        logger.info(
            f"Service {service.global_id}: All benchmarks completed in {total_duration:.1f}s"
        )

        return service_result

    def get_results_for_service(self, service_global_id: int) -> List[BenchmarkResult]:
        """Get all benchmark results for a specific service."""
        return [r for r in self.results if r.service_global_id == service_global_id]

    def clear_results(self):
        """Clear all stored results."""
        self.results.clear()
