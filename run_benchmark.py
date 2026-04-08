#!/usr/bin/env python3
"""
Entry point for the AI Model Serving Benchmark Framework.

Usage:
    python run_benchmark.py --config examples/example_config.py [--dry-run]
    python run_benchmark.py --help
"""
import sys
import os
import argparse
import logging
import importlib.util

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.main import BenchmarkPipeline, run_pipeline_from_config


def load_config_from_file(filepath: str) -> dict:
    """
    Load configuration from a Python file.

    The file should define a 'config_dict' variable.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Config file not found: {filepath}")

    # Import the module
    spec = importlib.util.spec_from_file_location("config_module", filepath)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load config from: {filepath}")

    config_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(config_module)

    if not hasattr(config_module, "config_dict"):
        raise AttributeError("Config file must define 'config_dict' variable")

    return config_module.config_dict


def main():
    parser = argparse.ArgumentParser(
        description="AI Model Serving Benchmark Framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Dry run with example config
    python run_benchmark.py --config examples/example_config.py --dry-run

    # Real benchmark run
    python run_benchmark.py --config examples/example_config.py
        """,
    )

    parser.add_argument(
        "--config",
        "-c",
        type=str,
        required=True,
        help="Path to configuration Python file (defines 'config_dict')",
    )

    parser.add_argument(
        "--dry-run",
        "-d",
        action="store_true",
        help="Dry run mode - don't actually launch services or run benchmarks",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Load config
    try:
        print(f"Loading configuration from: {args.config}")
        config_dict = load_config_from_file(args.config)
    except Exception as e:
        print(f"❌ Failed to load config: {e}", file=sys.stderr)
        sys.exit(1)

    # Run pipeline
    try:
        result = run_pipeline_from_config(config_dict, dry_run=args.dry_run)
        return 0
    except KeyboardInterrupt:
        print("\n\nBenchmark pipeline cancelled by user.", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"\n❌ Benchmark pipeline failed: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
