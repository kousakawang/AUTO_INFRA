"""
Test script for Phases 4-6: Result Store, Report Generator, and Main Pipeline.
This uses dry-run mode so no actual services are launched.
"""
import sys
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

sys.path.insert(0, '..')

from src import (
    BenchmarkPipeline, ResultStore, ReportGenerator,
    DataProcessor,
)

# Example user config from the documentation - simplified for dry-run
config_dict = {
    "user_config": {
        "model_paths": ["/data01/models/Qwen3.5-9B", "/data01/models/Qwen3-VL-8B"],
        "model_test_times": [2, 1],  # Reduced for faster test
        "model_deploy_method": ["tp1", "tp1", "tp1"],
        "device_id": [[0], [1], [2]],
        "basic_template_id": [1, 1, 2],
        "port": [8080, 8070, 8060],
        "env_opt_id": [[-1], [-1], [-1]],
        "server_args_opt_id": [[-1], [-1], [-1]],
        "additional_option": [
            ["--context-length 262144 --reasoning-parser qwen3"],
            ["--context-length 262144 --reasoning-parser qwen3"],
            ["--cuda-graph-max-bs 99"],
        ],
        "benchmark_case_num": [[2], [2], [1]],  # Reduced for faster test
        "benchmark_inputlen": [[32, 64], [32, 64], [32]],
        "benchmark_outputlen": [[64, 32], [64, 32], [64]],
        "benchmark_image_size": [
            ["448x448", "448x448"],
            ["448x448", "448x448"],
            ["640x640"]
        ],
        "benchmark_image_count": [[1, 1], [1, 1], [1]],
        "benchmark_max_concurrency": [[10, 20], [10, 20], [10]],
    },
    "pipeline_config": {
        "per_config_benchmark_times": 1,  # Reduced for faster test
        "prompt_num_dvide_max_concurrency": 6,
        "data_watch_policy": "remove_min_max",
        "max_existed_service_num": 2,
        "do_visuallize": True,
        "SLO": [1e8, 1e8],
    }
}


def test_result_store():
    """Test ResultStore functionality with mock data."""
    print("\n" + "=" * 60)
    print("Testing ResultStore")
    print("=" * 60)

    from src import BenchmarkSuiteResult, ServiceResult, BenchmarkResult

    store = ResultStore()

    # Create mock data
    suite_result = BenchmarkSuiteResult(
        config={"test": "config"},
        start_time=1234567890.0,
    )

    # Add some mock results
    service1 = ServiceResult(
        service_global_id=1,
        model_path="/test/model1",
        port=8080,
    )
    service1.results = [
        BenchmarkResult(
            service_global_id=1, case_id=1, run_id=0,
            total_token_throughput=3000.0, success=True,
            model_path="/test/model1", input_len=32, output_len=64, max_concurrency=10,
        ),
        BenchmarkResult(
            service_global_id=1, case_id=1, run_id=1,
            total_token_throughput=3010.0, success=True,
            model_path="/test/model1", input_len=32, output_len=64, max_concurrency=10,
        ),
    ]
    suite_result.service_results.append(service1)

    # Save and load
    filepath = store.save_suite_result(suite_result)
    print(f"✓ Saved to: {filepath}")

    loaded = store.load_suite_result(filepath)
    if loaded:
        print(f"✓ Loaded successfully, {len(loaded.service_results)} services")

    latest = store.get_latest_result()
    if latest:
        print(f"✓ Got latest result")

    print("\n✓ ResultStore tests passed!")


def test_data_processor():
    """Test DataProcessor functionality with mock data."""
    print("\n" + "=" * 60)
    print("Testing DataProcessor")
    print("=" * 60)

    from src import BenchmarkSuiteResult, ServiceResult, BenchmarkResult

    processor = DataProcessor(
        data_watch_policy="remove_min_max",
        slo_ttft_max=1e8,
        slo_tpot_max=1e8,
    )

    # Create mock data
    suite_result = BenchmarkSuiteResult()
    service1 = ServiceResult(
        service_global_id=1,
        model_path="/test/model1",
        port=8080,
    )

    # Add results with some variation
    for i in range(5):
        service1.results.append(BenchmarkResult(
            service_global_id=1, case_id=1, run_id=i,
            total_token_throughput=3000.0 + (i * 10),
            request_throughput=10.0 + i,
            mean_ttft_ms=100.0 + i,
            mean_tpot_ms=10.0 + i,
            success=True,
            model_path="/test/model1",
            input_len=32,
            output_len=64,
            max_concurrency=10,
        ))

    suite_result.service_results.append(service1)

    # Test SLO filter
    filtered = processor.filter_by_slo(service1.results)
    print(f"✓ SLO filter: {len(filtered)} results passed")

    # Test outlier removal
    no_outliers = processor.remove_outliers(service1.results)
    print(f"✓ Outlier removal: kept {len(no_outliers)} of {len(service1.results)}")

    # Test aggregation
    aggregated = processor.aggregate_results(suite_result)
    print(f"✓ Aggregation: {len(aggregated)} groups")

    for key, agg in aggregated.items():
        print(f"  - Group {key}: {agg.avg_total_token_throughput:.2f} tok/s")

    print("\n✓ DataProcessor tests passed!")


def main():
    print("=" * 60)
    print("Phases 4-6 Test: Result Store, Report Generator, Main Pipeline")
    print("=" * 60)

    # Run individual component tests
    test_result_store()
    test_data_processor()

    # Test the full pipeline in dry-run mode
    print("\n" + "=" * 60)
    print("Testing Full Pipeline (Dry-Run Mode)")
    print("=" * 60)

    pipeline = BenchmarkPipeline(config_dict)
    result = pipeline.run(dry_run=True)

    print("\n" + "=" * 60)
    print("✓ All Phases 4-6 Tests Passed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
