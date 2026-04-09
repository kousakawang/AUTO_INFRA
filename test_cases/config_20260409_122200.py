"""
Auto-generated configuration file.
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

config_dict = {
    "user_config": {
        "model_paths": ["/data01/models/Qwen3.5-9B"],
        "model_test_times": [4],
        "model_deploy_method": ["tp1", "tp1", "tp1", "tp1"],
        "device_id": [[0], [1], [2], [3]],
        "basic_template_id": [1, 1, 1, 1],
        "port": [8080, 8070, 8060, 8050],
        "env_opt_id": [[-1], [-1], [-1], [2]],
        "server_args_opt_id": [[-1], [3], [-1], [-1]],
        "additional_option": [
            ["--context-length 262144 --reasoning-parser qwen3"],
            ["--context-length 262144 --reasoning-parser qwen3"],
            ["--context-length 262144 --reasoning-parser qwen3"],
            ["--context-length 262144 --reasoning-parser qwen3"],
        ],
        "benchmark_case_num": [[3], [3], [2], [2]],
        "benchmark_inputlen": [[64, 64, 64], [64, 64, 64], [128, 128], [128, 128]],
        "benchmark_outputlen": [[32, 32, 32], [32, 32, 32], [64, 64], [64, 64]],
        "benchmark_image_size": [
            ["448x448", "448x448", "448x448"],
            ["448x448", "448x448", "448x448"],
            ["1280x1280", "1280x1280"],
            ["1280x1280", "1280x1280"],
        ],
        "benchmark_image_count": [[1, 1, 1], [1, 1, 1], [1, 1], [1, 1]],
        "benchmark_max_concurrency": [[16, 32, 64], [16, 32, 64], [8, 16], [8, 16]],
    },
    "pipeline_config": {
        "per_config_benchmark_times": 5,
        "prompt_num_dvide_max_concurrency": 6,
        "data_watch_policy": "remove_min_max",
        "max_existed_service_num": 2,
        "do_visuallize": True,
        "SLO": [100000000.0, 100000000.0],
    },
}
