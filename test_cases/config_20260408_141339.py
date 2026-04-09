"""
Auto-generated configuration file.
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

config_dict = {
        "user_config": {
            "model_paths": ['/data01/models/Qwen3.5-9B'],
            "model_test_times": [3],
            "model_deploy_method": ['tp1', 'tp1', 'tp1'],
            "device_id": [
                [0],
                [1],
                [2],
            ],
            "basic_template_id": [0, 0, 0],
            "port": [8080, 8070, 8060],
            "env_opt_id": [
                [-1],
                [-1],
                [-1],
            ],
            "server_args_opt_id": [
                [-1],
                [-1],
                [-1],
            ],
            "additional_option": [
                ['--context-length 262144 --reasoning-parser qwen3'],
                ['--context-length 262144 --reasoning-parser qwen3'],
                ['--context-length 262144 --reasoning-parser qwen3'],
            ],
            "benchmark_case_num": [
                [1],
                [1],
                [2],
            ],
            "benchmark_inputlen": [
                [32],
                [32],
                [32, 128],
            ],
            "benchmark_outputlen": [
                [64],
                [64],
                [64, 128],
            ],
            "benchmark_image_size": [
                ['448x448'],
                ['448x448'],
                ['448x448', '448x448'],
            ],
            "benchmark_image_count": [
                [1],
                [1],
                [1, 1],
            ],
            "benchmark_max_concurrency": [
                [20],
                [20],
                [20, 20],
            ],
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
