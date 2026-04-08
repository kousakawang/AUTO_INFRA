"""
Result type definitions for benchmark framework.
"""
from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class BenchmarkResult:
    """Result from a single benchmark run."""
    service_global_id: int
    case_id: int
    run_id: int
    total_token_throughput: float = 0.0
    request_throughput: float = 0.0
    input_token_throughput: float = 0.0
    output_token_throughput: float = 0.0
    mean_ttft_ms: float = 0.0
    mean_tpot_ms: float = 0.0
    mean_e2e_latency_ms: float = 0.0
    median_e2e_latency_ms: float = 0.0
    p90_e2e_latency_ms: float = 0.0
    p99_e2e_latency_ms: float = 0.0
    raw_output: str = ""
    success: bool = False
    error_message: Optional[str] = None

    # Additional metadata
    model_path: Optional[str] = None
    input_len: Optional[int] = None
    output_len: Optional[int] = None
    image_size: Optional[str] = None
    image_count: Optional[int] = None
    max_concurrency: Optional[int] = None

    # Service configuration info
    template_id: Optional[int] = None
    env_opt_ids: Optional[List[int]] = None
    server_args_opt_ids: Optional[List[int]] = None
    additional_options: Optional[List[str]] = None
    deploy_method: Optional[str] = None


@dataclass
class ServiceResult:
    """All results for a single service."""
    service_global_id: int
    model_path: str
    port: int
    results: List[BenchmarkResult] = field(default_factory=list)
    start_time: Optional[float] = None
    end_time: Optional[float] = None


@dataclass
class BenchmarkSuiteResult:
    """Complete results from a full benchmark suite."""
    service_results: List[ServiceResult] = field(default_factory=list)
    config: Optional[dict] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
