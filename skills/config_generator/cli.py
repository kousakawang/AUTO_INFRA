"""
Interactive CLI for config file generation.
"""
import os
import sys
import argparse
from typing import Optional, List, Dict, Any

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from skills.config_generator.config_builder import ConfigBuilder


def parse_raw_file(filepath: str, builder: ConfigBuilder):
    """Parse a raw test case file with launch and benchmark commands."""
    with open(filepath, "r") as f:
        lines = f.readlines()

    current_cmd = []
    in_launch = False
    in_benchmark = False

    for line in lines:
        line = line.strip()

        # Skip comments and empty lines
        if not line or line.startswith("#"):
            if "#launch" in line.lower() or "#lauch" in line.lower():
                in_launch = True
                in_benchmark = False
            elif "#benchmark" in line.lower():
                in_benchmark = True
                in_launch = False
            continue

        # Continue building command
        if in_launch or line.startswith("SGLANG_") or "sglang.launch_server" in line:
            current_cmd.append(line)
            in_launch = True
            # Check if this is a complete command (simple heuristic)
            if "sglang.launch_server" in line:
                full_cmd = " ".join(current_cmd)
                builder.add_launch_command(full_cmd)
                current_cmd = []
                in_launch = False
        elif in_benchmark or "sglang.bench_serving" in line:
            current_cmd.append(line)
            in_benchmark = True
            if "sglang.bench_serving" in line:
                full_cmd = " ".join(current_cmd)
                builder.add_benchmark_command(full_cmd)
                current_cmd = []
                in_benchmark = False


def print_preview(config_dict: Dict[str, Any]):
    """Print a preview of the generated config."""
    print("\n" + "="*60)
    print("CONFIG PREVIEW")
    print("="*60)

    user_config = config_dict["user_config"]
    pipeline_config = config_dict["pipeline_config"]

    print(f"\nModel paths: {user_config['model_paths']}")
    print(f"Model test times: {user_config['model_test_times']}")
    print(f"Total services: {sum(user_config['model_test_times'])}")

    print(f"\nServices:")
    for i in range(sum(user_config['model_test_times'])):
        print(f"  Service {i+1}:")
        print(f"    Deploy method: {user_config['model_deploy_method'][i]}")
        print(f"    Device ID: {user_config['device_id'][i]}")
        print(f"    Port: {user_config['port'][i]}")
        print(f"    Template ID: {user_config['basic_template_id'][i]}")
        print(f"    Env opt IDs: {user_config['env_opt_id'][i]}")
        print(f"    Server opt IDs: {user_config['server_args_opt_id'][i]}")
        add_opt = user_config['additional_option'][i][0]
        if add_opt:
            print(f"    Additional opt: {add_opt}")
        print(f"    Benchmark cases: {user_config['benchmark_case_num'][i]}")


def interactive_mode():
    """Run the interactive CLI mode."""
    print("="*60)
    print("  Config File Generator")
    print("="*60)

    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    builder = ConfigBuilder(project_root)

    print("\nOptions:")
    print("1. Parse from raw_test_case.sh file")
    print("2. Enter commands manually")
    print("3. Exit")

    choice = input("\nEnter your choice (1-3): ").strip()

    if choice == "1":
        default_path = os.path.join(project_root, "raw_folder", "raw_test_case.sh")
        filepath = input(f"Enter path to raw file [{default_path}]: ").strip()
        if not filepath:
            filepath = default_path

        if not os.path.exists(filepath):
            print(f"Error: File not found: {filepath}")
            return

        print(f"\nParsing {filepath}...")
        parse_raw_file(filepath, builder)

    elif choice == "2":
        print("\nEnter launch server commands (one per line, empty line when done):")
        while True:
            cmd = input("> ").strip()
            if not cmd:
                break
            builder.add_launch_command(cmd)

        print("\nEnter benchmark commands (one per line, empty line when done):")
        while True:
            cmd = input("> ").strip()
            if not cmd:
                break
            builder.add_benchmark_command(cmd)

    else:
        print("Exiting.")
        return

    # Build and preview
    config_dict = builder.build_config()
    print_preview(config_dict)

    # Ask to save
    output_dir = os.path.join(project_root, "test_cases")
    save = input(f"\nSave config to {output_dir}/? (y/n): ").strip().lower()
    if save == "y":
        filepath = builder.generate_config_file(output_dir)
        print(f"\nConfig saved to: {filepath}")

        # Also create a simple runner script
        runner_path = os.path.join(output_dir, "run_last_config.sh")
        config_filename = os.path.basename(filepath)
        with open(runner_path, "w") as f:
            f.write(f'''#!/bin/bash
# Auto-generated runner script
python3 run_benchmark.py --config test_cases/{config_filename} --dry-run
''')
        os.chmod(runner_path, 0o755)
        print(f"Runner script created: {runner_path}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Config File Generator - Makes config creation easier"
    )
    parser.add_argument(
        "--file", "-f",
        help="Path to raw test case file (e.g., raw_folder/raw_test_case.sh)"
    )
    parser.add_argument(
        "--output", "-o",
        default="test_cases",
        help="Output directory for generated config"
    )
    parser.add_argument(
        "--non-interactive", "-n",
        action="store_true",
        help="Run in non-interactive mode (just parse and save)"
    )

    args = parser.parse_args()

    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    builder = ConfigBuilder(project_root)

    if args.file:
        if not os.path.exists(args.file):
            print(f"Error: File not found: {args.file}")
            sys.exit(1)

        parse_raw_file(args.file, builder)

        config_dict = builder.build_config()

        if not args.non_interactive:
            print_preview(config_dict)

        output_dir = args.output if os.path.isabs(args.output) else os.path.join(project_root, args.output)
        filepath = builder.generate_config_file(output_dir)
        print(f"Config saved to: {filepath}")

    else:
        interactive_mode()


if __name__ == "__main__":
    main()
