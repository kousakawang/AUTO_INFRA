"""
Benchmark functions - result parsing and utility functions.
"""
import re
import logging
from typing import Optional, Dict, Any

from .result_types import BenchmarkResult

logger = logging.getLogger(__name__)


# Regex patterns for parsing benchmark output
PATTERNS = {
    "total_token_throughput": re.compile(r"Total token throughput \(tok/s\):\s+([\d.]+)"),
    "request_throughput": re.compile(r"Request throughput \(req/s\):\s+([\d.]+)"),
    "input_token_throughput": re.compile(r"Input token throughput \(tok/s\):\s+([\d.]+)"),
    "output_token_throughput": re.compile(r"Output token throughput \(tok/s\):\s+([\d.]+)"),
    "mean_e2e_latency": re.compile(r"Mean E2E Latency \(ms\):\s+([\d.]+)"),
    "median_e2e_latency": re.compile(r"Median E2E Latency \(ms\):\s+([\d.]+)"),
    "p90_e2e_latency": re.compile(r"P90 E2E Latency \(ms\):\s+([\d.]+)"),
    "p99_e2e_latency": re.compile(r"P99 E2E Latency \(ms\):\s+([\d.]+)"),
    "mean_ttft": re.compile(r"Mean TTFT \(ms\):\s+([\d.]+)"),
    "mean_tpot": re.compile(r"Mean TPOT \(ms\):\s+([\d.]+)"),
}


def parse_benchmark_output(output: str, result: BenchmarkResult) -> BenchmarkResult:
    """
    Parse benchmark output and populate the BenchmarkResult.

    Args:
        output: Raw output string from benchmark command
        result: BenchmarkResult object to populate

    Returns:
        Updated BenchmarkResult
    """
    result.raw_output = output

    # Parse each metric
    for key, pattern in PATTERNS.items():
        match = pattern.search(output)
        if match:
            try:
                value = float(match.group(1))
                if key == "total_token_throughput":
                    result.total_token_throughput = value
                elif key == "request_throughput":
                    result.request_throughput = value
                elif key == "input_token_throughput":
                    result.input_token_throughput = value
                elif key == "output_token_throughput":
                    result.output_token_throughput = value
                elif key == "mean_e2e_latency":
                    result.mean_e2e_latency_ms = value
                elif key == "median_e2e_latency":
                    result.median_e2e_latency_ms = value
                elif key == "p90_e2e_latency":
                    result.p90_e2e_latency_ms = value
                elif key == "p99_e2e_latency":
                    result.p99_e2e_latency_ms = value
                elif key == "mean_ttft":
                    result.mean_ttft_ms = value
                elif key == "mean_tpot":
                    result.mean_tpot_ms = value
            except (ValueError, IndexError) as e:
                logger.debug(f"Failed to parse {key}: {e}")

    # Check if parsing was successful (look for the header line)
    if "============ Serving Benchmark Result ============" in output:
        result.success = True
    else:
        result.success = False
        result.error_message = "Benchmark result header not found in output"

    return result


def generate_mock_benchmark_output(
    total_token_throughput: float = 3771.11,
    request_throughput: float = 12.38,
    input_token_throughput: float = 2979.08,
    output_token_throughput: float = 792.02,
    mean_ttft_ms: float = 0.0,
    mean_tpot_ms: float = 24.16,
    mean_e2e_ms: float = 1522.09,
) -> str:
    """
    Generate mock benchmark output for testing.

    Returns a string matching the format in benchmark_result_example.md
    """
    return f"""============ Serving Benchmark Result ============
Backend:                                 sglang-oai-chat
Traffic request rate:                    inf
Max request concurrency:                 20
Successful requests:                     128
Benchmark duration (s):                  10.34
Total input tokens:                      30813
Total input text tokens:                 5530
Total input vision tokens:               25283
Total generated tokens:                  8192
Total generated tokens (retokenized):    0
Request throughput (req/s):              {request_throughput:.2f}
Input token throughput (tok/s):          {input_token_throughput:.2f}
Output token throughput (tok/s):         {output_token_throughput:.2f}
Peak output token throughput (tok/s):    20.00
Peak concurrent requests:                40
Total token throughput (tok/s):          {total_token_throughput:.2f}
Concurrency:                             18.84
----------------End-to-End Latency----------------
Mean E2E Latency (ms):                   {mean_e2e_ms:.2f}
Median E2E Latency (ms):                 1480.75
P90 E2E Latency (ms):                    1727.45
P99 E2E Latency (ms):                    1729.23
---------------Time to First Token----------------
Mean TTFT (ms):                          {mean_ttft_ms:.2f}
Median TTFT (ms):                        0.00
P99 TTFT (ms):                           0.00
-----Time per Output Token (excl. 1st token)------
Mean TPOT (ms):                          {mean_tpot_ms:.2f}
Median TPOT (ms):                        23.50
P99 TPOT (ms):                           27.45
---------------Inter-Token Latency----------------
Mean ITL (ms):                           0.00
Median ITL (ms):                         0.00
P95 ITL (ms):                            0.00
P99 ITL (ms):                            0.00
Max ITL (ms):                            0.00
=================================================="""
