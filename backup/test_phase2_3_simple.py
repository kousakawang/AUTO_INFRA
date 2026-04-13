"""
Real test script for Phase 2 and 3 - Service Manager and Benchmark Orchestrator.
This version actually runs the services and benchmarks (not dry-run).
"""
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

sys.path.insert(0, '..')

from src import (
    Config, ConfigExpander, TemplateLoader, CommandGenerator,
    ServiceManager, ServiceQueue, BenchmarkOrchestrator,
    BenchmarkResult, ServiceResult,
)

# Example user config from the documentation
config_dict = {
    "user_config": {
        "model_paths": ["/data01/models/Qwen3.5-9B"],
        "model_test_times": [1],
        "model_deploy_method": ["tp1"],
        "device_id": [[0]],
        "basic_template_id": [1],
        "port": [8080],
        "env_opt_id": [[-1], ],
        "server_args_opt_id": [[-1], ],
        "additional_option": [
            ["--context-length 262144 --reasoning-parser qwen3"],
        ],
        "benchmark_case_num": [[3],],
        "benchmark_inputlen": [[32, 32, 32], ],
        "benchmark_outputlen": [[64, 64, 64],],
        "benchmark_image_size": [
            ["448x448", "448x448", "448x448"],
        ],
        "benchmark_image_count": [[1, 1, 1]],
        "benchmark_max_concurrency": [[10, 20, 5]],
    },
    "pipeline_config": {
        "per_config_benchmark_times": 2,  # Reduced for faster test
        "prompt_num_dvide_max_concurrency": 6,
        "data_watch_policy": "remove_min_max",
        "max_existed_service_num": 2,
        "do_visuallize": True,
        "SLO": [1e8, 1e8],
    }
}


def main():
    print("=" * 60)
    print("Phase 2 & 3 REAL Test: Service Manager + Benchmark Orchestrator")
    print("=" * 60)
    print()

    # ========== Step 1: Setup (same as Phase 1) ==========
    print("Step 1: Loading and expanding configuration...")
    config = Config.from_dict(config_dict)
    errors = config.validate()
    if errors:
        print("Validation errors:")
        for err in errors:
            print(f"  - {err}")
        return

    expander = ConfigExpander(config.user_config, config.pipeline_config)
    full_config = expander.expand()

    loader = TemplateLoader()
    loader.load_all()

    generator = CommandGenerator(loader)
    print("   ✓ Configuration ready\n")

    # ========== Step 2: Initialize Service Manager ==========
    print("Step 2: Initializing Service Manager...")
    service_manager = ServiceManager(full_config, generator)
    print(f"   ✓ Service Manager created (max concurrent: {service_manager.max_concurrent})\n")

    # ========== Step 3: Initialize Service Queue ==========
    print("Step 3: Initializing Service Queue...")
    service_queue = ServiceQueue(full_config, service_manager)
    service_queue.add_all_pending(full_config.services)
    print(f"   ✓ Service Queue created with {service_queue.get_pending_count()} pending services\n")

    # ========== Step 4: Initialize Benchmark Orchestrator ==========
    print("Step 4: Initializing Benchmark Orchestrator...")
    orchestrator = BenchmarkOrchestrator(full_config, generator)
    print(f"   ✓ Benchmark Orchestrator created (runs per config: {orchestrator.per_config_benchmark_times})\n")

    # ========== Step 5: Real execution ==========
    print("=" * 60)
    print("Step 5: REAL execution (will launch actual services)")
    print("=" * 60)
    print()

    dry_run = False  # REAL MODE!
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
                    print(f"   → Command: {instance.launch_command}")

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
                        print(f"     Case {result.case_id}, Run {result.run_id}: "
                              f"{result.total_token_throughput:.2f} tok/s "
                              f"(success: {result.success})")

                    # Mark service as completed
                    print(f"\n   → Killing service {instance.global_id}...")
                    service_manager.kill_service(instance, dry_run=dry_run)
                    service_queue.mark_completed(instance)
                    print(f"   ✓ Service {instance.global_id} completed")

            # Small delay to prevent tight loop
            import time
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\n\n!!! Received KeyboardInterrupt - cleaning up !!!")
    except Exception as e:
        print(f"\n\n!!! Error: {e} !!!")
    finally:
        # Always clean up
        print("\n--- Cleaning up all services ---")
        service_manager.cleanup_all(dry_run=dry_run)

    # ========== Summary ==========
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"Total services processed: {service_queue.get_completed_count()}")
    print(f"Total benchmarks run: {len(orchestrator.results)}")

    # Calculate average throughput per service
    print("\nAverage Total Token Throughput per Service:")
    for service_result in all_service_results:
        if service_result.results:
            avg_throughput = sum(r.total_token_throughput for r in service_result.results) / len(service_result.results)
            print(f"  Service {service_result.service_global_id}: {avg_throughput:.2f} tok/s")

    print("\n" + "=" * 60)
    print("✓ Phase 2 & 3 REAL Test Complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
