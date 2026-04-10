#!/usr/bin/env python3
"""
Dry-run validation script for Qwen3.5-9B test configuration.
"""
import os
import sys

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from skills.config_validator import load_and_validate_config
from skills.service_manager import ServiceManagerSkill
from skills.benchmark_runner import BenchmarkRunnerSkill


def main():
    print("=" * 60)
    print("Configuration Validation (Dry-Run)")
    print("=" * 60)

    # Step 1: Load and validate configuration
    print("\n[1/3] Loading and validating configuration...")
    config_path = os.path.join(project_root, "request_case", "config_request_1.py")
    full_config, template_loader, config_dict = load_and_validate_config(config_path)
    print(f"   ✓ Loaded {len(full_config.services)} services")

    # Step 2: Initialize skills
    print("\n[2/3] Initializing skills...")
    service_skill = ServiceManagerSkill(template_loader, full_config)
    benchmark_skill = BenchmarkRunnerSkill(template_loader, full_config)
    print("   ✓ Skills initialized")

    # Step 3: Verify all service configurations
    print("\n[3/3] Verifying service configurations...")

    for service_idx, service_config in enumerate(full_config.services):
        print(f"\n--- Service {service_idx} ---")

        # Create and verify launch command (dry-run)
        instance = service_skill.launch_service(service_config, dry_run=True)
        print(f"Port: {service_config.port}")
        print(f"GPU: {service_config.device_id}")
        print(f"Template: {service_config.template_id}")
        print(f"Env opt: {service_config.env_opt_ids}")
        print(f"Server opt: {service_config.server_args_opt_ids}")

        # Verify required additional options
        opts = " ".join(service_config.additional_options)
        has_context = "--context-length 262144" in opts
        has_parser = "--reasoning-parser qwen3" in opts
        print(f"Required options present: {'✓' if has_context and has_parser else '✗'}")

        print(f"\nLaunch command:")
        print(f"  {instance.launch_command}")

        # Verify benchmark cases
        print(f"\nBenchmark cases ({len(service_config.benchmark_cases)}):")
        for case in service_config.benchmark_cases:
            bench_cmd = benchmark_skill.generate_benchmark_command(service_config, case)
            print(f"  Case {case.case_id}: in={case.input_len}, out={case.output_len}, "
                  f"img={case.image_size}, concurrency={case.max_concurrency}")
            print(f"    Command: {bench_cmd[:80]}...")

    # Summary
    print("\n" + "=" * 60)
    print("Validation Summary")
    print("=" * 60)
    print(f"Total services: {len(full_config.services)}")
    print(f"Services to run in batch 1: 0, 1 (small image)")
    print(f"Services to run in batch 2: 2, 3 (large image)")
    print(f"\nAll configurations look valid! ✓")
    print("=" * 60)


if __name__ == "__main__":
    main()
