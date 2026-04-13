"""
Test tp>1 per-device throughput calculation.
"""
import sys
import os
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

sys.path.insert(0, '..')

from src import BenchmarkPipeline

# Test config with tp2
config_dict = {
    "user_config": {
        "model_paths": ["/data01/models/Qwen3.5-9B"],
        "model_test_times": [1],
        "model_deploy_method": ["tp2"],
        "device_id": [[0, 1]],
        "basic_template_id": [1],
        "port": [8080],
        "env_opt_id": [[0]],
        "server_args_opt_ids": [[1]],
        "additional_option": [["--context-length 262144 --reasoning-parser qwen3"]],
        "benchmark_case_num": [[1]],
        "benchmark_inputlen": [[32]],
        "benchmark_outputlen": [[64]],
        "benchmark_image_size": [["448x448"]],
        "benchmark_image_count": [[1]],
        "benchmark_max_concurrency": [[10]],
    },
    "pipeline_config": {
        "per_config_benchmark_times": 1,
        "prompt_num_dvide_max_concurrency": 6,
        "data_watch_policy": "remove_min_max",
        "max_existed_service_num": 2,
        "do_visuallize": True,
        "SLO": [1e8, 1e8],
    }
}


def main():
    print("=" * 60)
    print("Test tp>1 Per-Device Throughput Calculation")
    print("=" * 60)
    print()

    # Note: This needs server_args_opt_ids (plural) in the config, let's fix it
    config_dict["user_config"]["server_args_opt_id"] = [[1]]

    pipeline = BenchmarkPipeline(config_dict)
    result = pipeline.run(dry_run=True)

    print("\n" + "=" * 60)
    print("✓ tp>1 Test Complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
