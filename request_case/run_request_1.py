#!/usr/bin/env python3
"""
Execution script for Qwen3.5-9B Preliminary Performance Optimization Test.
Uses individual skills instead of pipeline_orchestrator.
"""
import os
import sys
import time

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from skills.config_validator import load_and_validate_config
from skills.service_manager import ServiceManagerSkill
from skills.benchmark_runner import BenchmarkRunnerSkill
from skills.result_processor import ResultProcessorSkill
from skills.report_generator import ReportGeneratorSkill
from src.result_types import BenchmarkSuiteResult, ServiceResult


def main():
    print("=" * 60)
    print("Qwen3.5-9B Preliminary Performance Optimization Test")
    print("=" * 60)

    # -------------------------------------------------------------------------
    # Step 1: Load and validate configuration
    # -------------------------------------------------------------------------
    print("\n[1/5] Loading and validating configuration...")
    config_path = os.path.join(project_root, "request_case", "config_request_1.py")
    full_config, template_loader, config_dict = load_and_validate_config(config_path)
    print(f"   ✓ Loaded {len(full_config.services)} services")

    # Verify additional options are present
    for i, service in enumerate(full_config.services):
        opts = " ".join(service.additional_options)
        if "--context-length 262144" in opts and "--reasoning-parser qwen3" in opts:
            print(f"   ✓ Service {i}: has required additional options")
        else:
            print(f"   ✗ Service {i}: missing required options!")

    # -------------------------------------------------------------------------
    # Step 2: Initialize skills
    # -------------------------------------------------------------------------
    print("\n[2/5] Initializing skills...")
    service_skill = ServiceManagerSkill(template_loader, full_config)
    benchmark_skill = BenchmarkRunnerSkill(template_loader, full_config)
    result_processor = ResultProcessorSkill(
        data_watch_policy=full_config.pipeline_config.get("data_watch_policy", "remove_min_max"),
        slo_ttft_max=full_config.pipeline_config.get("SLO", [1e8, 1e8])[0],
        slo_tpot_max=full_config.pipeline_config.get("SLO", [1e8, 1e8])[1]
    )
    report_skill = ReportGeneratorSkill(
        reports_dir=os.path.join(project_root, "reports"),
        do_visualize=full_config.pipeline_config.get("do_visuallize", True),
        slo_ttft_max=full_config.pipeline_config.get("SLO", [1e8, 1e8])[0],
        slo_tpot_max=full_config.pipeline_config.get("SLO", [1e8, 1e8])[1],
        data_watch_policy=full_config.pipeline_config.get("data_watch_policy", "remove_min_max"),
        template_loader=template_loader
    )
    print("   ✓ Skills initialized")

    # -------------------------------------------------------------------------
    # Step 3: Run benchmarks in batches
    # -------------------------------------------------------------------------
    print("\n[3/5] Running benchmarks...")
    suite_result = BenchmarkSuiteResult(config=config_dict)
    suite_start_time = time.time()

    # Get services grouped by batch (max 2 concurrent)
    services = full_config.services
    max_concurrent = full_config.pipeline_config.get("max_existed_service_num", 2)
    per_config_benchmark_times = full_config.pipeline_config.get("per_config_benchmark_times", 3)

    # Batch 1: Services 0 and 1 (small image tests)
    print("\n--- Batch 1: Services 0 (Baseline-Small) and 1 (Optimized-Small) ---")
    batch1_instances = []
    batch1_service_results = {}

    try:
        # Launch both services
        for service_idx in [0, 1]:
            service_config = services[service_idx]
            print(f"\nLaunching Service {service_idx} (port {service_config.port})...")
            instance = service_skill.launch_service(service_config, dry_run=False)
            print(f"   Command: {instance.launch_command[:100]}...")
            batch1_instances.append(instance)
            batch1_service_results[service_idx] = ServiceResult(
                service_global_id=service_config.global_id,
                model_path=service_config.model_path,
                port=service_config.port,
                start_time=time.time()
            )

        # Wait for both services to be ready
        print("\nWaiting for services to be ready...")
        for instance in batch1_instances:
            if service_skill.wait_for_ready(instance, timeout=300, dry_run=False):
                print(f"   ✓ Service {instance.global_id} is ready")
            else:
                print(f"   ✗ Service {instance.global_id} failed to become ready!")

        # Run benchmarks for both services
        print("\nRunning benchmarks...")
        for instance in batch1_instances:
            service_config = services[instance.global_id]
            service_result = batch1_service_results[instance.global_id]

            print(f"\nService {instance.global_id}: Running {len(service_config.benchmark_cases)} cases "
                  f"({per_config_benchmark_times} runs each)...")

            for case in service_config.benchmark_cases:
                print(f"  Case {case.case_id}: in={case.input_len}, out={case.output_len}, "
                      f"img={case.image_size}, concurrency={case.max_concurrency}")

                for run_idx in range(per_config_benchmark_times):
                    print(f"    Run {run_idx + 1}/{per_config_benchmark_times}...", end="", flush=True)
                    result = benchmark_skill.run_benchmark(
                        instance._core_instance, case, run_idx, dry_run=False
                    )
                    if result.success:
                        print(f" ✓ ({result.total_token_throughput:.2f} tok/s)")
                    else:
                        print(f" ✗ ({result.error_message})")
                    service_result.results.append(result)

            service_result.end_time = time.time()

    finally:
        # Clean up services
        print("\nCleaning up batch 1 services...")
        for instance in batch1_instances:
            service_skill.kill_service(instance, dry_run=False)
            print(f"   ✓ Killed Service {instance.global_id}")

    # Add batch 1 results to suite
    for service_idx in [0, 1]:
        suite_result.service_results.append(batch1_service_results[service_idx])

    # Batch 2: Services 2 and 3 (large image tests)
    print("\n--- Batch 2: Services 2 (Baseline-Large) and 3 (Optimized-Large) ---")
    batch2_instances = []
    batch2_service_results = {}

    try:
        # Launch both services
        for service_idx in [2, 3]:
            service_config = services[service_idx]
            print(f"\nLaunching Service {service_idx} (port {service_config.port})...")
            instance = service_skill.launch_service(service_config, dry_run=False)
            print(f"   Command: {instance.launch_command[:100]}...")
            batch2_instances.append(instance)
            batch2_service_results[service_idx] = ServiceResult(
                service_global_id=service_config.global_id,
                model_path=service_config.model_path,
                port=service_config.port,
                start_time=time.time()
            )

        # Wait for both services to be ready
        print("\nWaiting for services to be ready...")
        for instance in batch2_instances:
            if service_skill.wait_for_ready(instance, timeout=300, dry_run=False):
                print(f"   ✓ Service {instance.global_id} is ready")
            else:
                print(f"   ✗ Service {instance.global_id} failed to become ready!")

        # Run benchmarks for both services
        print("\nRunning benchmarks...")
        for instance in batch2_instances:
            service_config = services[instance.global_id]
            service_result = batch2_service_results[instance.global_id]

            print(f"\nService {instance.global_id}: Running {len(service_config.benchmark_cases)} cases "
                  f"({per_config_benchmark_times} runs each)...")

            for case in service_config.benchmark_cases:
                print(f"  Case {case.case_id}: in={case.input_len}, out={case.output_len}, "
                      f"img={case.image_size}, concurrency={case.max_concurrency}")

                for run_idx in range(per_config_benchmark_times):
                    print(f"    Run {run_idx + 1}/{per_config_benchmark_times}...", end="", flush=True)
                    result = benchmark_skill.run_benchmark(
                        instance._core_instance, case, run_idx, dry_run=False
                    )
                    if result.success:
                        print(f" ✓ ({result.total_token_throughput:.2f} tok/s)")
                    else:
                        print(f" ✗ ({result.error_message})")
                    service_result.results.append(result)

            service_result.end_time = time.time()

    finally:
        # Clean up services
        print("\nCleaning up batch 2 services...")
        for instance in batch2_instances:
            service_skill.kill_service(instance, dry_run=False)
            print(f"   ✓ Killed Service {instance.global_id}")

    # Add batch 2 results to suite
    for service_idx in [2, 3]:
        suite_result.service_results.append(batch2_service_results[service_idx])

    suite_result.end_time = time.time()

    # -------------------------------------------------------------------------
    # Step 4: Process results
    # -------------------------------------------------------------------------
    print("\n[4/5] Processing results...")
    aggregated = result_processor.aggregate_per_service_case(suite_result)
    groups = result_processor.group_results(aggregated)
    print(f"   ✓ Aggregated {len(aggregated)} service-case results")
    print(f"   ✓ Grouped into {len(groups)} comparison groups")

    # -------------------------------------------------------------------------
    # Step 5: Generate report
    # -------------------------------------------------------------------------
    print("\n[5/5] Generating report...")
    report_path = report_skill.generate_report(suite_result, report_name="request_1_results")
    print(f"   ✓ Report saved to: {report_path}")

    print("\n" + "=" * 60)
    print("Test completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
