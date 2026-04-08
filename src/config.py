"""
Configuration handling module.
Loads, validates, and provides access to benchmark configuration.
"""
from typing import Dict, List


def get_default_pipeline_config() -> Dict:
    return {
        "per_config_benchmark_times": 5,
        "prompt_num_dvide_max_concurrency": 6,
        "data_watch_policy": "remove_min_max",
        "max_existed_service_num": 2,
        "do_visuallize": True,
        "SLO": [1e8, 1e8],
    }


def validate_user_config(config: Dict) -> List[str]:
    errors = []

    # Check required keys
    required_keys = [
        "model_paths", "model_test_times", "model_deploy_method",
        "device_id", "basic_template_id", "port",
        "env_opt_id", "server_args_opt_id", "additional_option",
        "benchmark_case_num", "benchmark_inputlen", "benchmark_outputlen",
        "benchmark_image_size", "benchmark_image_count", "benchmark_max_concurrency"
    ]

    for key in required_keys:
        if key not in config:
            errors.append(f"Missing required key: {key}")

    if errors:
        return errors

    # Check that model_test_times and model_paths have same length
    if len(config["model_paths"]) != len(config["model_test_times"]):
        errors.append(f"model_paths length ({len(config['model_paths'])}) != model_test_times length ({len(config['model_test_times'])})")
        return errors

    # Check that total test times matches other arrays
    total_tests = sum(config["model_test_times"])

    array_fields = [
        "model_deploy_method", "device_id", "basic_template_id", "port",
        "env_opt_id", "server_args_opt_id", "additional_option", "benchmark_case_num",
        "benchmark_inputlen", "benchmark_outputlen", "benchmark_image_size",
        "benchmark_image_count", "benchmark_max_concurrency"
    ]

    for field_name in array_fields:
        arr = config.get(field_name, [])
        if len(arr) != total_tests:
            errors.append(f"{field_name} length ({len(arr)}) != total test times ({total_tests})")

    # Check ports are unique
    ports = config.get("port", [])
    if len(ports) != len(set(ports)):
        errors.append("Ports must be unique")

    return errors


class Config:
    def __init__(self, config_dict: Dict):
        self.user_config = config_dict.get("user_config", {})

        # Merge with default pipeline config
        default_pipeline = get_default_pipeline_config()
        user_pipeline = config_dict.get("pipeline_config", {})
        self.pipeline_config = {**default_pipeline, **user_pipeline}

    @classmethod
    def from_dict(cls, config_dict: Dict) -> "Config":
        return cls(config_dict)

    def validate(self) -> List[str]:
        return validate_user_config(self.user_config)
