"""
Tests for config module.
"""
import sys
sys.path.insert(0, '..')

from src import Config, get_default_pipeline_config, validate_user_config


def test_default_pipeline_config():
    """Test getting default pipeline config."""
    default = get_default_pipeline_config()
    assert "per_config_benchmark_times" in default
    assert default["max_existed_service_num"] == 2


def test_config_validation_valid():
    """Test validation with valid config."""
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

    errors = validate_user_config(user_config)
    assert len(errors) == 0


def test_config_validation_invalid_ports():
    """Test validation with duplicate ports."""
    user_config = {
        "model_paths": ["/model/1", "/model/2"],
        "model_test_times": [1, 1],
        "model_deploy_method": ["tp1", "tp1"],
        "device_id": [[0], [1]],
        "basic_template_id": [0, 0],
        "port": [8080, 8080],  # Duplicate
        "env_opt_id": [[-1], [-1]],
        "server_args_opt_id": [[0], [0]],
        "additional_option": [[""], [""]],
        "benchmark_case_num": [[1], [1]],
        "benchmark_inputlen": [[32], [32]],
        "benchmark_outputlen": [[64], [64]],
        "benchmark_image_size": [["448x448"], ["448x448"]],
        "benchmark_image_count": [[1], [1]],
        "benchmark_max_concurrency": [[10], [10]],
    }

    errors = validate_user_config(user_config)
    assert len(errors) > 0
    assert "unique" in str(errors).lower()


def test_config_from_dict():
    """Test creating config from dict."""
    config_dict = {
        "user_config": {
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
        },
        "pipeline_config": {
            "max_existed_service_num": 3
        }
    }

    config = Config.from_dict(config_dict)
    assert config is not None
    assert config.pipeline_config["max_existed_service_num"] == 3
    # Should have default values for other pipeline configs
    assert "per_config_benchmark_times" in config.pipeline_config
