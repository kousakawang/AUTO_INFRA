"""
Main Pipeline - End-to-end benchmark orchestration.
"""
import time
import logging
import sys
from typing import Dict, Optional

from .config import Config, get_default_pipeline_config
from .config_generator import ConfigExpander
from .templates import TemplateLoader, CommandGenerator
from .service_manager import ServiceManager
from .service_queue import ServiceQueue
from .benchmark_orchestrator import BenchmarkOrchestrator
from .result_types import BenchmarkSuiteResult, ServiceResult
from .result_store import ResultStore
from .report_generator import ReportGenerator

logger = logging.getLogger(__name__)


class BenchmarkPipeline:
    """
    End-to-end benchmark pipeline.

    Orchestrates the complete workflow:
    1. Load and validate configuration
    2. Expand user config to full config
    3. Launch services and run benchmarks
    4. Collect results
    5. Generate reports
    """

    def __init__(self, config_dict: Dict):
        """
        Initialize the benchmark pipeline.

        Args:
            config_dict: Configuration dictionary with user_config and pipeline_config
        """
        self.config_dict = config_dict
        self.config = Config.from_dict(config_dict)
        self.result_store = ResultStore()
        self.suite_result: Optional[BenchmarkSuiteResult] = None

        # Extract pipeline config
        self.pipeline_config = self.config.pipeline_config
        self.do_visualize = self.pipeline_config.get("do_visuallize", True)
        self.data_watch_policy = self.pipeline_config.get("data_watch_policy", "remove_min_max")
        slo = self.pipeline_config.get("SLO", [1e8, 1e8])
        self.slo_ttft_max = slo[0]
        self.slo_tpot_max = slo[1]

        # report_generator will be initialized later after loading templates
        self.report_generator = None

    def run(self, dry_run: bool = False) -> BenchmarkSuiteResult:
        """
        Run the complete benchmark pipeline.

        Args:
            dry_run: If True, don't actually launch services or run benchmarks

        Returns:
            BenchmarkSuiteResult with all results
        """
        print("=" * 70)
        print("AI Model Serving Benchmark Pipeline")
        print("=" * 70)
        print()

        self.suite_result = BenchmarkSuiteResult(
            config=self.config_dict,
            start_time=time.time(),
        )

        try:
            # Step 1: Validate configuration
            print("Step 1: Validating configuration...")
            errors = self.config.validate()
            if errors:
                print("❌ Validation errors:")
                for err in errors:
                    print(f"   - {err}")
                raise ValueError("Invalid configuration")
            print("   ✓ Configuration validated\n")

            # Step 2: Expand configuration
            print("Step 2: Expanding configuration...")
            expander = ConfigExpander(self.config.user_config, self.config.pipeline_config)
            full_config = expander.expand()
            print(f"   ✓ Expanded to {len(full_config.services)} services\n")

            # Step 3: Load templates
            print("Step 3: Loading templates...")
            loader = TemplateLoader()
            loader.load_all()
            generator = CommandGenerator(loader)
            print("   ✓ Templates loaded\n")

            # Step 4: Initialize components
            print("Step 4: Initializing components...")
            service_manager = ServiceManager(full_config, generator)
            service_queue = ServiceQueue(full_config, service_manager)
            service_queue.add_all_pending(full_config.services)
            orchestrator = BenchmarkOrchestrator(full_config, generator)

            # Initialize report generator with template loader for OPT explanations
            self.report_generator = ReportGenerator(
                do_visualize=self.do_visualize,
                slo_ttft_max=self.slo_ttft_max,
                slo_tpot_max=self.slo_tpot_max,
                data_watch_policy=self.data_watch_policy,
                template_loader=loader,
            )

            print(f"   ✓ Components initialized (max concurrent services: {service_manager.max_concurrent})\n")

            # Step 5: Run execution
            print("=" * 70)
            mode = "DRY RUN" if dry_run else "REAL EXECUTION"
            print(f"Step 5: {mode}")
            print("=" * 70)
            print()

            all_service_results = self._run_execution_loop(
                service_queue,
                service_manager,
                orchestrator,
                dry_run=dry_run,
            )

            self.suite_result.service_results = all_service_results

            # Step 6: Save results
            print("\nStep 6: Saving results...")
            result_path = self.result_store.save_suite_result(self.suite_result)
            print(f"   ✓ Results saved to: {result_path}\n")

            # Step 7: Generate report
            print("Step 7: Generating report...")
            report_path = self.report_generator.generate_report(self.suite_result)
            print(f"   ✓ Report generated at: {report_path}\n")

        except KeyboardInterrupt:
            print("\n\n⚠️  Received KeyboardInterrupt - cleaning up...")
            raise
        except Exception as e:
            print(f"\n\n❌ Error: {e}")
            logger.exception("Pipeline failed")
            raise
        finally:
            self.suite_result.end_time = time.time()

        # Summary
        self._print_summary()

        return self.suite_result

    def _run_execution_loop(
        self,
        service_queue: ServiceQueue,
        service_manager: ServiceManager,
        orchestrator: BenchmarkOrchestrator,
        dry_run: bool = False,
    ) -> list:
        """Run the main execution loop."""
        all_service_results = []

        try:
            while service_queue.has_pending() or service_queue.has_active():
                # Launch new services if we have capacity
                while service_queue.has_pending() and service_queue.has_capacity():
                    print(f"--- Launching next service (pending: {service_queue.get_pending_count()}, "
                          f"active: {service_queue.get_active_count()}/{service_queue.max_concurrent}) ---")
                    instance = service_queue.launch_next(dry_run=dry_run)
                    if instance:
                        print(f"   → Launched service {instance.global_id} (port {instance.port})")
                        if dry_run:
                            print(f"   → Command: {instance.launch_command[:100]}...")

                        # Wait for ready
                        print(f"   → Waiting for service to be ready...")
                        ready = service_manager.wait_for_ready(instance, dry_run=dry_run)
                        if ready:
                            print(f"   ✓ Service {instance.global_id} is ready!")
                            instance.state = "running"
                        else:
                            print(f"   ✗ Service {instance.global_id} failed to become ready")
                            service_manager.kill_service(instance, dry_run=dry_run)
                            service_queue.mark_completed(instance)

                # Process active services
                for instance in list(service_queue.get_active_services()):
                    if instance.state == "running":
                        print(f"\n--- Running benchmarks for service {instance.global_id} ---")
                        service_result = orchestrator.run_all_benchmarks_for_service(
                            instance, dry_run=dry_run
                        )
                        all_service_results.append(service_result)

                        # Display results summary
                        print(f"\n   Results for service {instance.global_id}:")
                        for result in service_result.results:
                            status = "✓" if result.success else "✗"
                            print(f"     {status} Case {result.case_id}, Run {result.run_id}: "
                                  f"{result.total_token_throughput:.2f} tok/s")

                        # Mark service as completed
                        print(f"\n   → Killing service {instance.global_id}...")
                        service_manager.kill_service(instance, dry_run=dry_run)
                        service_queue.mark_completed(instance)
                        print(f"   ✓ Service {instance.global_id} completed\n")

                # Small delay to prevent tight loop
                if not dry_run:
                    time.sleep(0.1)

        except Exception as e:
            print(f"\n⚠️  Error during execution: {e}")
            raise
        finally:
            # Always clean up
            print("\n--- Cleaning up all services ---")
            service_manager.cleanup_all(dry_run=dry_run)

        return all_service_results

    def _print_summary(self):
        """Print a summary of the benchmark run."""
        print("=" * 70)
        print("Pipeline Summary")
        print("=" * 70)

        if not self.suite_result:
            print("No results available")
            return

        total_services = len(self.suite_result.service_results)
        total_benchmarks = sum(len(sr.results) for sr in self.suite_result.service_results)
        successful_benchmarks = sum(
            sum(1 for r in sr.results if r.success)
            for sr in self.suite_result.service_results
        )

        print(f"Total services: {total_services}")
        print(f"Total benchmarks: {total_benchmarks}")
        print(f"Successful benchmarks: {successful_benchmarks}")

        if self.suite_result.start_time and self.suite_result.end_time:
            duration = self.suite_result.end_time - self.suite_result.start_time
            print(f"Total duration: {duration:.1f} seconds")

        # Show throughput summary
        throughputs = []
        for sr in self.suite_result.service_results:
            for r in sr.results:
                if r.success:
                    throughputs.append(r.total_token_throughput)

        if throughputs:
            print(f"\nThroughput summary:")
            print(f"  Min: {min(throughputs):.2f} tok/s")
            print(f"  Max: {max(throughputs):.2f} tok/s")
            print(f"  Avg: {sum(throughputs) / len(throughputs):.2f} tok/s")

        print("\n" + "=" * 70)
        print("✓ Pipeline complete!")
        print("=" * 70)


def run_pipeline_from_config(config_dict: Dict, dry_run: bool = False) -> BenchmarkSuiteResult:
    """
    Convenience function to run the benchmark pipeline from a config dict.

    Args:
        config_dict: Configuration dictionary
        dry_run: If True, don't actually execute

    Returns:
        BenchmarkSuiteResult
    """
    pipeline = BenchmarkPipeline(config_dict)
    return pipeline.run(dry_run=dry_run)
