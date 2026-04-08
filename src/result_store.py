"""
Result Store - Handles saving and loading benchmark results.
"""
import json
import os
import time
import logging
from dataclasses import asdict
from typing import Dict, List, Optional

from .result_types import BenchmarkResult, ServiceResult, BenchmarkSuiteResult

logger = logging.getLogger(__name__)


class ResultStore:
    """
    Stores and retrieves benchmark results.

    Saves results to JSON files in the outputs/ directory.
    """

    def __init__(self, output_dir: str = "outputs"):
        self.output_dir = output_dir
        self._ensure_output_dir()

    def _ensure_output_dir(self):
        """Ensure the output directory exists."""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            logger.info(f"Created output directory: {self.output_dir}")

    def _generate_filename(self) -> str:
        """Generate a unique filename with timestamp."""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        return f"benchmark_results_{timestamp}.json"

    def _benchmark_result_to_dict(self, result: BenchmarkResult) -> Dict:
        """Convert BenchmarkResult to a serializable dictionary."""
        return asdict(result)

    def _service_result_to_dict(self, result: ServiceResult) -> Dict:
        """Convert ServiceResult to a serializable dictionary."""
        return {
            "service_global_id": result.service_global_id,
            "model_path": result.model_path,
            "port": result.port,
            "results": [self._benchmark_result_to_dict(r) for r in result.results],
            "start_time": result.start_time,
            "end_time": result.end_time,
        }

    def _benchmark_suite_result_to_dict(self, suite_result: BenchmarkSuiteResult) -> Dict:
        """Convert BenchmarkSuiteResult to a serializable dictionary."""
        return {
            "service_results": [self._service_result_to_dict(sr) for sr in suite_result.service_results],
            "config": suite_result.config,
            "start_time": suite_result.start_time,
            "end_time": suite_result.end_time,
        }

    def _dict_to_benchmark_result(self, data: Dict) -> BenchmarkResult:
        """Convert dictionary to BenchmarkResult."""
        return BenchmarkResult(**data)

    def _dict_to_service_result(self, data: Dict) -> ServiceResult:
        """Convert dictionary to ServiceResult."""
        benchmark_results = [self._dict_to_benchmark_result(br) for br in data.get("results", [])]
        return ServiceResult(
            service_global_id=data["service_global_id"],
            model_path=data["model_path"],
            port=data["port"],
            results=benchmark_results,
            start_time=data.get("start_time"),
            end_time=data.get("end_time"),
        )

    def _dict_to_benchmark_suite_result(self, data: Dict) -> BenchmarkSuiteResult:
        """Convert dictionary to BenchmarkSuiteResult."""
        service_results = [self._dict_to_service_result(sr) for sr in data.get("service_results", [])]
        return BenchmarkSuiteResult(
            service_results=service_results,
            config=data.get("config"),
            start_time=data.get("start_time"),
            end_time=data.get("end_time"),
        )

    def save_suite_result(self, suite_result: BenchmarkSuiteResult) -> str:
        """
        Save a BenchmarkSuiteResult to a JSON file.

        Args:
            suite_result: The benchmark suite result to save

        Returns:
            The path to the saved file
        """
        filename = self._generate_filename()
        filepath = os.path.join(self.output_dir, filename)

        data = self._benchmark_suite_result_to_dict(suite_result)

        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

        logger.info(f"Saved benchmark suite results to: {filepath}")
        return filepath

    def load_suite_result(self, filepath: str) -> Optional[BenchmarkSuiteResult]:
        """
        Load a BenchmarkSuiteResult from a JSON file.

        Args:
            filepath: Path to the JSON file

        Returns:
            The loaded BenchmarkSuiteResult, or None if loading fails
        """
        if not os.path.exists(filepath):
            logger.error(f"Result file not found: {filepath}")
            return None

        try:
            with open(filepath, "r") as f:
                data = json.load(f)

            suite_result = self._dict_to_benchmark_suite_result(data)
            logger.info(f"Loaded benchmark suite results from: {filepath}")
            return suite_result
        except Exception as e:
            logger.error(f"Failed to load result file {filepath}: {e}")
            return None

    def list_result_files(self) -> List[str]:
        """
        List all result files in the output directory.

        Returns:
            List of file paths sorted by modification time (newest first)
        """
        if not os.path.exists(self.output_dir):
            return []

        files = [
            os.path.join(self.output_dir, f)
            for f in os.listdir(self.output_dir)
            if f.startswith("benchmark_results_") and f.endswith(".json")
        ]

        # Sort by modification time, newest first
        files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        return files

    def get_latest_result(self) -> Optional[BenchmarkSuiteResult]:
        """
        Load the most recent result file.

        Returns:
            The latest BenchmarkSuiteResult, or None if no results exist
        """
        files = self.list_result_files()
        if not files:
            logger.warning("No result files found")
            return None

        return self.load_suite_result(files[0])

    def get_results_by_model(self, suite_result: BenchmarkSuiteResult, model_path: str) -> List[BenchmarkResult]:
        """
        Get all benchmark results for a specific model.

        Args:
            suite_result: The benchmark suite result to search
            model_path: The model path to filter by

        Returns:
            List of BenchmarkResult for the specified model
        """
        results = []
        for service_result in suite_result.service_results:
            if service_result.model_path == model_path:
                results.extend(service_result.results)
        return results

    def get_results_by_service(self, suite_result: BenchmarkSuiteResult, service_global_id: int) -> Optional[ServiceResult]:
        """
        Get the service result for a specific service ID.

        Args:
            suite_result: The benchmark suite result to search
            service_global_id: The service global ID to filter by

        Returns:
            ServiceResult for the specified service, or None if not found
        """
        for service_result in suite_result.service_results:
            if service_result.service_global_id == service_global_id:
                return service_result
        return None
