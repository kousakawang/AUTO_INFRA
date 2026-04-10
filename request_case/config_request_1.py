"""
Configuration for Qwen3.5-9B Preliminary Performance Optimization Test.
"""
import sys
sys.path.insert(0, '..')


config_dict = {
    "user_config": {
        "model_paths": ["/data01/models/Qwen3.5-9B"],
        "model_test_times": [4],  # 4 services total for this model
        "model_deploy_method": ["tp1", "tp1", "tp1", "tp1"],
        "device_id": [[0], [1], [2], [3]],
        "basic_template_id": [2, 2, 2, 2],  # All use template 2 (with --disable-radix-cache)
        "port": [8080, 8070, 8060, 8050],
        "env_opt_id": [
            [-1],              # Service 0: Baseline - no env opt
            [-1],              # Service 1: flashinfer - no env opt
            [-1],              # Service 2: Baseline - no env opt
            [2],               # Service 3: FP8 - SGLANG_VISION_ATTN_FP8=1
        ],
        "server_args_opt_id": [
            [-1],              # Service 0: Baseline - no server opt
            [3],               # Service 1: flashinfer - --decode-attention-backend flashinfer
            [-1],              # Service 2: Baseline - no server opt
            [-1],              # Service 3: FP8 - no server opt
        ],
        "additional_option": [
            ["--context-length 262144 --reasoning-parser qwen3"],
            ["--context-length 262144 --reasoning-parser qwen3"],
            ["--context-length 262144 --reasoning-parser qwen3"],
            ["--context-length 262144 --reasoning-parser qwen3"],
        ],
        "benchmark_case_num": [
            [3],  # Service 0: 3 cases (small image: concurrency 2, 4, 8)
            [3],  # Service 1: 3 cases (small image: concurrency 2, 4, 8)
            [2],  # Service 2: 2 cases (large image: concurrency 2, 4)
            [2],  # Service 3: 2 cases (large image: concurrency 2, 4)
        ],
        "benchmark_inputlen": [
            [64, 64, 64],      # Service 0: input len 64 for all cases
            [64, 64, 64],      # Service 1: input len 64 for all cases
            [128, 128],         # Service 2: input len 128 for all cases
            [128, 128],         # Service 3: input len 128 for all cases
        ],
        "benchmark_outputlen": [
            [32, 32, 32],      # Service 0: output len 32 for all cases
            [32, 32, 32],      # Service 1: output len 32 for all cases
            [64, 64],           # Service 2: output len 64 for all cases
            [64, 64],           # Service 3: output len 64 for all cases
        ],
        "benchmark_image_size": [
            ["448x448", "448x448", "448x448"],    # Service 0: small image
            ["448x448", "448x448", "448x448"],    # Service 1: small image
            ["1280x1280", "1280x1280"],            # Service 2: large image
            ["1280x1280", "1280x1280"],            # Service 3: large image
        ],
        "benchmark_image_count": [
            [1, 1, 1],    # Service 0: 1 image per request
            [1, 1, 1],    # Service 1: 1 image per request
            [1, 1],       # Service 2: 1 image per request
            [1, 1],       # Service 3: 1 image per request
        ],
        "benchmark_max_concurrency": [
            [2, 4, 8],    # Service 0: concurrency 2, 4, 8
            [2, 4, 8],    # Service 1: concurrency 2, 4, 8
            [2, 4],       # Service 2: concurrency 2, 4
            [2, 4],       # Service 3: concurrency 2, 4
        ],
    },
    "pipeline_config": {
        "per_config_benchmark_times": 3,
        "prompt_num_dvide_max_concurrency": 6,
        "data_watch_policy": "remove_min_max",
        "max_existed_service_num": 2,
        "do_visuallize": True,
        "SLO": [1e8, 1e8],
    }
}
