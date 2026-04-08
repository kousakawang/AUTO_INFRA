"""
Configuration expansion module.
Expands simple user config into detailed execution config.
"""
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class BenchmarkCase:
    case_id: int
    input_len: int
    output_len: int
    image_size: str
    image_count: int
    max_concurrency: int
    num_prompts: int


@dataclass
class ServiceConfig:
    global_id: int
    model_path: str
    model_index: int
    deploy_method: str
    device_id: List[int]
    template_id: int
    port: int
    env_opt_ids: List[int]
    server_args_opt_ids: List[int]
    additional_options: List[str]
    benchmark_cases: List[BenchmarkCase]


class FullConfig:
    def __init__(self):
        self.services: List[ServiceConfig] = []
        self.pipeline_config: Optional[Dict] = None


class ConfigExpander:
    def __init__(self, user_config: Dict, pipeline_config: Dict):
        self.user_config = user_config
        self.pipeline_config = pipeline_config

    def expand(self) -> FullConfig:
        """Expand user configuration to full execution configuration."""
        full_config = FullConfig()
        full_config.pipeline_config = self.pipeline_config

        global_id = 0
        cfg = self.user_config

        for model_idx, (model_path, test_times) in enumerate(
            zip(cfg["model_paths"], cfg["model_test_times"])
        ):
            for _ in range(test_times):
                service_config = self._create_service_config(global_id, model_idx, model_path)
                full_config.services.append(service_config)
                global_id += 1

        return full_config

    def _create_service_config(self, global_id: int, model_idx: int, model_path: str) -> ServiceConfig:
        """Create configuration for a single service."""
        cfg = self.user_config

        # Get benchmark case count for this service
        case_count_list = cfg["benchmark_case_num"][global_id]
        case_count = case_count_list[0] if case_count_list else 1

        # Expand benchmark arrays
        input_lens = self._expand_array(cfg["benchmark_inputlen"][global_id], case_count)
        output_lens = self._expand_array(cfg["benchmark_outputlen"][global_id], case_count)
        image_sizes = self._expand_array(cfg["benchmark_image_size"][global_id], case_count)
        image_counts = self._expand_array(cfg["benchmark_image_count"][global_id], case_count)
        max_concurrencies = self._expand_array(cfg["benchmark_max_concurrency"][global_id], case_count)

        # Create benchmark cases
        benchmark_cases = []
        for case_idx in range(case_count):
            num_prompts = self.pipeline_config["prompt_num_dvide_max_concurrency"] * max_concurrencies[case_idx]
            benchmark_cases.append(BenchmarkCase(
                case_id=case_idx,
                input_len=input_lens[case_idx],
                output_len=output_lens[case_idx],
                image_size=image_sizes[case_idx],
                image_count=image_counts[case_idx],
                max_concurrency=max_concurrencies[case_idx],
                num_prompts=num_prompts
            ))

        return ServiceConfig(
            global_id=global_id,
            model_path=model_path,
            model_index=model_idx,
            deploy_method=cfg["model_deploy_method"][global_id],
            device_id=cfg["device_id"][global_id],
            template_id=cfg["basic_template_id"][global_id],
            port=cfg["port"][global_id],
            env_opt_ids=cfg["env_opt_id"][global_id],
            server_args_opt_ids=cfg["server_args_opt_id"][global_id],
            additional_options=cfg["additional_option"][global_id],
            benchmark_cases=benchmark_cases
        )

    def _expand_array(self, arr: List, target_length: int) -> List:
        """Expand array by repeating last element if needed."""
        if not arr:
            return []
        if len(arr) >= target_length:
            return arr[:target_length]
        # Repeat last element
        last = arr[-1]
        return arr + [last] * (target_length - len(arr))
