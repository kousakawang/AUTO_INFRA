"""
Tests for config_generator module.
"""
import sys
sys.path.insert(0, '..')

from src import ConfigExpander, get_default_pipeline_config


def test_config_expander():
    """Test basic config expansion."""
    user_config = {
        "model_paths": ["/model/1"],
        "model_test_times": [1],
        "model_deploy_method": ["tp1"],
        "device_id": [[0]],
        "basic_template_id": [1],
        "port": [8080],
        "env_opt_id": [[-1]],
        "server_args_opt_id": [[0]],
        "additional_option": [[""]],
        "benchmark_case_num": [[1]],
        "benchmark_inputlen": [[32]],
        "benchmark_outputlen": [[64]],
        "benchmark_image_size": [["448x448"]],
        "benchmark_image_count": [[1]],
        "benchmark_max_concurrency": [[10]],
    }

    pipeline_config = get_default_pipeline_config()
    expander = ConfigExpander(user_config, pipeline_config)
    full_config = expander.expand()

    assert len(full_config.services) == 1
    service = full_config.services[0]
    assert service.global_id == 0
    assert service.model_path == "/model/1"
    assert len(service.benchmark_cases) == 1
    assert service.benchmark_cases[0].num_prompts == 6 * 10  # prompt_num_dvide_max_concurrency * max_concurrency


def test_array_expansion():
    """Test that arrays are expanded correctly by repeating last element."""
    user_config = {
        "model_paths": ["/model/1"],
        "model_test_times": [1],
        "model_deploy_method": ["tp1"],
        "device_id": [[0]],
        "basic_template_id": [1],
        "port": [8080],
        "env_opt_id": [[-1]],
        "server_args_opt_id": [[0]],
        "additional_option": [[""]],
        "benchmark_case_num": [[3]],
        "benchmark_inputlen": [[32]],  # Only 1 element, should expand to 3
        "benchmark_outputlen": [[64, 128]],  # 2 elements, should expand to 3
        "benchmark_image_size": [["448x448", "224x224", "1080x720"]],
        "benchmark_image_count": [[1, 2]],
        "benchmark_max_concurrency": [[10, 20, 30]],
    }

    pipeline_config = get_default_pipeline_config()
    expander = ConfigExpander(user_config, pipeline_config)
    full_config = expander.expand()

    service = full_config.services[0]
    assert len(service.benchmark_cases) == 3

    # Check input len expansion - should be [32, 32, 32]
    assert service.benchmark_cases[0].input_len == 32
    assert service.benchmark_cases[1].input_len == 32
    assert service.benchmark_cases[2].input_len == 32

    # Check output len expansion - should be [64, 128, 128]
    assert service.benchmark_cases[0].output_len == 64
    assert service.benchmark_cases[1].output_len == 128
    assert service.benchmark_cases[2].output_len == 128

    # Check image count expansion - should be [1, 2, 2]
    assert service.benchmark_cases[0].image_count == 1
    assert service.benchmark_cases[1].image_count == 2
    assert service.benchmark_cases[2].image_count == 2


def test_multiple_models():
    """Test with multiple models and multiple test times."""
    user_config = {
        "model_paths": ["/model/A", "/model/B"],
        "model_test_times": [2, 1],  # Model A tested 2x, model B tested 1x
        "model_deploy_method": ["tp1", "tp2", "tp1"],
        "device_id": [[0], [1, 2], [3]],
        "basic_template_id": [1, 1, 2],
        "port": [8080, 8070, 8060],
        "env_opt_id": [[-1], [0], [-1]],
        "server_args_opt_id": [[0], [1], [2]],
        "additional_option": [[""], [""], [""]],
        "benchmark_case_num": [[1], [1], [1]],
        "benchmark_inputlen": [[32], [32], [64]],
        "benchmark_outputlen": [[64], [64], [128]],
        "benchmark_image_size": [["448x448"], ["448x448"], ["1080x720"]],
        "benchmark_image_count": [[1], [1], [1]],
        "benchmark_max_concurrency": [[10], [20], [30]],
    }

    pipeline_config = get_default_pipeline_config()
    expander = ConfigExpander(user_config, pipeline_config)
    full_config = expander.expand()

    assert len(full_config.services) == 3

    # First service (model A)
    assert full_config.services[0].global_id == 0
    assert full_config.services[0].model_path == "/model/A"
    assert full_config.services[0].model_index == 0
    assert full_config.services[0].port == 8080

    # Second service (model A)
    assert full_config.services[1].global_id == 1
    assert full_config.services[1].model_path == "/model/A"
    assert full_config.services[1].model_index == 0
    assert full_config.services[1].port == 8070

    # Third service (model B)
    assert full_config.services[2].global_id == 2
    assert full_config.services[2].model_path == "/model/B"
    assert full_config.services[2].model_index == 1
    assert full_config.services[2].port == 8060
