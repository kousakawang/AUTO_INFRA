#!/usr/bin/env python3
"""
Example: Skill-based pipeline usage.

This script demonstrates how to use the reconstructed skills to run
a complete benchmark pipeline. It also shows how individual skills
can be used independently for more flexible workflows.
"""
import os
import sys
import argparse

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


def example_full_pipeline(config_file: str, dry_run: bool = True):
    """
    Example 1: Run the complete pipeline using the pipeline_orchestrator skill.

    This is equivalent to the original run_benchmark.py but uses the
    skill-based architecture internally.
    """
    print("=" * 70)
    print("Example 1: Full Pipeline Orchestration")
    print("=" * 70)

    from skills.pipeline_orchestrator import run_pipeline_from_file

    result = run_pipeline_from_file(config_file, dry_run=dry_run)
    return result


def example_skill_composition(config_file: str, dry_run: bool = True):
    """
    Example 2: Compose skills manually for more control.

    This demonstrates how to call each skill individually, which
    enables flexible workflows like SLO-based optimization,
    parameter search, etc.
    """
    print("\n" + "=" * 70)
    print("Example 2: Manual Skill Composition")
    print("=" * 70)

    # Import individual skills
    from skills.config_validator import load_and_validate_config
    from skills.service_manager import ServiceManagerSkill
    from skills.benchmark_runner import BenchmarkRunnerSkill, create_benchmark_case
    from skills.result_processor import ResultProcessorSkill
    from skills.report_generator import ReportGeneratorSkill
    from src.result_store import ResultStore
    from src.result_types import BenchmarkSuiteResult, ServiceResult
    import time

    # Step 1: Load and validate config
    print("\nStep 1: Loading and validating config...")
    full_config, template_loader, config_dict = load_and_validate_config(config_file)
    print(f"   ✓ Loaded {len(full_config.services)} services")

    # Initialize skills
    service_skill = ServiceManagerSkill(template_loader, full_config)
    benchmark_skill = BenchmarkRunnerSkill(template_loader, full_config)
    result_processor = ResultProcessorSkill()
    report_skill = ReportGeneratorSkill(template_loader=template_loader)
    result_store = ResultStore()

    # Create suite result
    suite_result = BenchmarkSuiteResult(config=config_dict, start_time=time.time())

    try:
        # Get max concurrent services from config
        max_concurrent = full_config.pipeline_config.get("max_existed_service_num", 2)
        pending_services = list(full_config.services)
        active_instances = {}  # global_id -> instance

        print(f"\nStep 2: Running {len(pending_services)} services (max concurrent: {max_concurrent})...")

        while pending_services or active_instances:
            # Launch new services if we have capacity
            while pending_services and len(active_instances) < max_concurrent:
                service_config = pending_services.pop(0)
                print(f"\n--- Launching service {service_config.global_id} (pending: {len(pending_services)}, active: {len(active_instances)}/{max_concurrent}) ---")

                # Launch service
                print("   Launching service...")
                instance = service_skill.launch_service(service_config, dry_run=dry_run)
                print(f"   → Launched service {instance.global_id} (port {instance.port})")
                if dry_run:
                    print(f"   → Command: {instance.launch_command[:100]}...")

                # Wait for ready
                print(f"   → Waiting for service to be ready...")
                ready = service_skill.wait_for_ready(instance, dry_run=dry_run)
                if ready:
                    print(f"   ✓ Service {instance.global_id} is ready!")
                    active_instances[instance.global_id] = instance
                else:
                    print(f"   ✗ Service {instance.global_id} failed to become ready")
                    service_skill.kill_service(instance, dry_run=dry_run)

            # Process active services (run benchmarks on one at a time)
            if active_instances:
                # Pick first active service to run benchmarks on
                global_id, instance = next(iter(active_instances.items()))
                service_config = full_config.services[global_id]

                print(f"\n--- Running benchmarks for service {global_id} ---")
                service_result = ServiceResult(
                    service_global_id=instance.global_id,
                    model_path=instance.model_path,
                    port=instance.port,
                    start_time=time.time()
                )

                # Run each benchmark case
                for case in service_config.benchmark_cases:
                    print(f"   Running case {case.case_id}: concurrency={case.max_concurrency}")
                    # Run multiple times per config (as specified in pipeline config)
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

                # Display results summary
                print(f"\n   Results for service {global_id}:")
                for result in service_result.results:
                    status = "✓" if result.success else "✗"
                    print(f"     {status} Case {result.case_id}, Run {result.run_id}: "
                          f"{result.total_token_throughput:.2f} tok/s")

                # Mark service as completed
                print(f"\n   → Killing service {global_id}...")
                service_skill.kill_service(instance, dry_run=dry_run)
                del active_instances[global_id]
                print(f"   ✓ Service {global_id} completed\n")

            # Small delay to prevent tight loop
            if not dry_run:
                time.sleep(0.1)

    finally:
        # Always cleanup
        print("\n--- Cleaning up all services ---")
        service_skill.cleanup_all(dry_run=dry_run)

    # Step 6: Save results
    print("\nStep 5: Saving results...")
    suite_result.end_time = time.time()
    result_path = result_store.save_suite_result(suite_result)
    print(f"   ✓ Results saved to: {result_path}")

    # Step 7: Generate report
    print("\nStep 6: Generating report...")
    report_path = report_skill.generate_report(suite_result)
    print(f"   ✓ Report generated at: {report_path}")

    print("\n" + "=" * 70)
    print("✓ Manual skill composition complete!")
    print("=" * 70)

    return suite_result


def example_slo_optimization_sketch(config_file: str):
    """
    Example 3: Sketch of SLO-based throughput optimization.

    This is a conceptual example showing how the skills could be
    composed to find the maximum throughput under SLO constraints.
    """
    print("\n" + "=" * 70)
    print("Example 3: SLO Optimization Sketch (Conceptual)")
    print("=" * 70)
    print("""
This is a sketch of how you could implement SLO-based optimization:

1. Load config and launch service once
2. For concurrency in [10, 20, 30, 40, 50, ...]:
   a. Create benchmark case with current concurrency
   b. Run benchmark
   c. Check if TTFT and TPOT are within SLO
   d. If yes, keep track of throughput; else, break
3. Report the maximum throughput achieved under SLO
4. Cleanup service

See AGENT_GUIDELINES.md for more details on this pattern.
""")


def main():
    parser = argparse.ArgumentParser(
        description="Skill-Based Pipeline Examples",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Run full pipeline (dry-run) with example config
    python examples/skill_based_pipeline.py --config examples/demo_config.py

    # Run manual skill composition
    python examples/skill_based_pipeline.py --config examples/demo_config.py --example manual

    # Real execution (not dry-run)
    python examples/skill_based_pipeline.py --config examples/demo_config.py --no-dry-run
        """
    )

    parser.add_argument(
        "--config", "-c",
        default=os.path.join(project_root, "examples", "demo_config.py"),
        help="Path to configuration file"
    )

    parser.add_argument(
        "--example", "-e",
        choices=["full", "manual", "slo-sketch"],
        default="full",
        help="Which example to run (default: full)"
    )

    parser.add_argument(
        "--no-dry-run",
        action="store_false",
        dest="dry_run",
        help="Run real benchmarks (not dry-run)"
    )

    args = parser.parse_args()

    if not os.path.exists(args.config):
        print(f"Error: Config file not found: {args.config}")
        sys.exit(1)

    if args.example == "full":
        example_full_pipeline(args.config, dry_run=args.dry_run)
    elif args.example == "manual":
        example_skill_composition(args.config, dry_run=args.dry_run)
    elif args.example == "slo-sketch":
        example_slo_optimization_sketch(args.config)


if __name__ == "__main__":
    main()
