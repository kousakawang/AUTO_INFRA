"""
AI Model Serving Benchmark Framework
Core library modules for config, templates, service management,
result processing, reporting, and visualization.
"""
from .config import Config, get_default_pipeline_config, validate_user_config
from .config_generator import ConfigExpander, FullConfig, ServiceConfig, BenchmarkCase
from .templates import TemplateLoader, CommandGenerator
from .result_types import BenchmarkResult, ServiceResult, BenchmarkSuiteResult
from .service_manager import ServiceManager, ServiceInstance
from .benchmark_functions import parse_benchmark_output, generate_mock_benchmark_output
from .result_store import ResultStore
from .data_processor import DataProcessor, ServiceCaseAggregatedResult, GroupResult, GroupKey
from .report_generator import ReportGenerator
from .visualization import Visualizer

__version__ = "1.0.0"
__all__ = [
    "Config", "get_default_pipeline_config", "validate_user_config",
    "ConfigExpander", "FullConfig", "ServiceConfig", "BenchmarkCase",
    "TemplateLoader", "CommandGenerator",
    "BenchmarkResult", "ServiceResult", "BenchmarkSuiteResult",
    "ServiceManager", "ServiceInstance",
    "parse_benchmark_output", "generate_mock_benchmark_output",
    "ResultStore",
    "DataProcessor", "ServiceCaseAggregatedResult", "GroupResult", "GroupKey",
    "ReportGenerator",
    "Visualizer",
]
