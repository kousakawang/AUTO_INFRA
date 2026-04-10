"""
Pipeline Orchestrator Skill - Main implementation.
Runs the complete end-to-end benchmark pipeline using all skills together.
"""
import os
import sys

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from src.result_types import BenchmarkSuiteResult
from src.main import BenchmarkPipeline as CoreBenchmarkPipeline


class PipelineOrchestratorSkill:
    """
    Skill that orchestrates the complete benchmark pipeline.

    Note: This currently delegates to the original core pipeline for
    backward compatibility while we verify the individual skills work.
    """
    def __init__(self, config_dict: dict):
        self._core_pipeline = CoreBenchmarkPipeline(config_dict)

    def run(self, dry_run: bool = False) -> BenchmarkSuiteResult:
        """
        Run the complete benchmark pipeline.

        Args:
            dry_run: If True, don't actually launch services or run benchmarks

        Returns:
            BenchmarkSuiteResult with all results
        """
        return self._core_pipeline.run(dry_run=dry_run)


# Convenience functions
def run_pipeline(config_dict: dict, dry_run: bool = False) -> BenchmarkSuiteResult:
    """
    Run the complete benchmark pipeline from a config dict.

    Args:
        config_dict: Configuration dictionary
        dry_run: If True, don't actually execute

    Returns:
        BenchmarkSuiteResult
    """
    orchestrator = PipelineOrchestratorSkill(config_dict)
    return orchestrator.run(dry_run=dry_run)


def run_pipeline_from_file(filepath: str, dry_run: bool = False) -> BenchmarkSuiteResult:
    """
    Run the complete benchmark pipeline from a config file.

    Args:
        filepath: Path to config file
        dry_run: If True, don't actually execute

    Returns:
        BenchmarkSuiteResult
    """
    from skills.config_validator import load_config_from_file
    config_dict = load_config_from_file(filepath)
    return run_pipeline(config_dict, dry_run=dry_run)
