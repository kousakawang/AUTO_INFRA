"""
Auto-generated configuration file.
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

config_dict = {   'pipeline_config': {   'SLO': [100000000.0, 100000000.0],
                           'data_watch_policy': 'remove_min_max',
                           'do_visuallize': True,
                           'max_existed_service_num': 2,
                           'per_config_benchmark_times': 5,
                           'prompt_num_dvide_max_concurrency': 6},
    'user_config': {   'additional_option': [   [   'SGLANG_VLM_CACHE_SIZE_MB=0 --context-length '
                                                    '262144 --reasoning-parser qwen3'],
                                                [   'SGLANG_VLM_CACHE_SIZE_MB=256 --cuda-graph-bs '
                                                    '64 56 48 40 32 24 16 8 4 2 1 --context-length '
                                                    '262144 --reasoning-parser qwen3'],
                                                [   'SGLANG_VLM_CACHE_SIZE_MB=512 --context-length '
                                                    '262144 --reasoning-parser qwen3']],
                       'basic_template_id': [1, 1, 1],
                       'benchmark_case_num': [[1], [1], [2]],
                       'benchmark_image_count': [[1], [1], [1, 1]],
                       'benchmark_image_size': [['448x448'], ['448x448'], ['448x448', '448x448']],
                       'benchmark_inputlen': [[32], [32], [32, 128]],
                       'benchmark_max_concurrency': [[20], [20], [20, 20]],
                       'benchmark_outputlen': [[64], [64], [64, 128]],
                       'device_id': [[0], [3, 4], [2]],
                       'env_opt_id': [[-1], [-1], [-1]],
                       'model_deploy_method': ['tp1', 'tp2', 'tp1'],
                       'model_paths': ['/data01/models/Qwen3.5-9B'],
                       'model_test_times': [3],
                       'port': [8080, 8090, 8060],
                       'server_args_opt_id': [[-1], [-1], [-1]]}}
