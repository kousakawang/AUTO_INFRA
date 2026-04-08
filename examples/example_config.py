"""
Example configuration usage.
"""
import sys
sys.path.insert(0, '..')

from src import Config, ConfigExpander, TemplateLoader, CommandGenerator

# Example user config from the documentation
config_dict = {
    "user_config": {
        "model_paths": ["/data01/models/Qwen3.5-9B", "/data01/models/Qwen3-VL-8B-Instruct"],
        "model_test_times": [2, 1],
        "model_deploy_method": ["tp1", "tp1", "tp1"],
        "device_id": [[0], [1], [2]],
        "basic_template_id": [2, 2, 1],
        "port": [8080, 8070, 8060],
        "env_opt_id": [[-1], [-1], [-1]],
        "server_args_opt_id": [[-1], [-1], [-1]],
        "additional_option": [
            ["--context-length 262144 --reasoning-parser qwen3"],
            ["--context-length 262144 --reasoning-parser qwen3"],
            [""],
        ],
        "benchmark_case_num": [[2], [2], [1]],
        "benchmark_inputlen": [[32, 64], [32, 64], [32],],
        "benchmark_outputlen": [[64,128], [64, 128], [64],],
        "benchmark_image_size": [
            ["448x448", "448x448",],
            ["448x448", "448x448",],
            ["448x448", ],
        ],
        "benchmark_image_count": [[1, 1, ], [1, 1, ], [1, 1, ],],
        "benchmark_max_concurrency": [[20, 20,], [20, 20, ], [10,],],
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


def main():
    print("=== Phase 1 Demo ===\n")

    # 1. Load and validate config
    print("1. Loading configuration...")
    config = Config.from_dict(config_dict)

    errors = config.validate()
    if errors:
        print("Validation errors:")
        for err in errors:
            print(f"  - {err}")
        return
    print("   ✓ Config valid!\n")

    # 2. Expand config
    print("2. Expanding configuration...")
    expander = ConfigExpander(config.user_config, config.pipeline_config)
    full_config = expander.expand()
    print(f"   ✓ Expanded to {len(full_config.services)} services\n")

    # 3. Load templates
    print("3. Loading templates...")
    loader = TemplateLoader()
    loader.load_all()
    print(f"   ✓ Loaded {len(loader.server_templates)} server templates")
    print(f"   ✓ Loaded {len(loader.benchmark_templates)} benchmark templates")
    print(f"   ✓ Loaded {len(loader.env_opts)} env opts")
    print(f"   ✓ Loaded {len(loader.server_args_opts)} server args opts\n")

    # 4. Generate commands
    print("4. Generating commands...")
    generator = CommandGenerator(loader)

    for service in full_config.services:
        print(f"\n   Service {service.global_id} (port {service.port}):")
        cmd = generator.generate_server_command(service)
        print(f"      Launch: {cmd}")

        for case in service.benchmark_cases:
            bench_cmd = generator.generate_benchmark_command(service, case)
            print(f"      Benchmark case {case.case_id}: {bench_cmd}")

    print("\n=== Phase 1 Demo Complete ===")


if __name__ == "__main__":
    main()
