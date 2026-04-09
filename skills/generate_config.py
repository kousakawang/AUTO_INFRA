#!/usr/bin/env python3
"""
Convenience wrapper for the config generator skill.
Usage:
    python skills/generate_config.py --file raw_folder/raw_test_case.sh
    python skills/generate_config.py  # interactive mode
"""
import sys
import os

# Add the skills directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config_generator.cli import main

if __name__ == "__main__":
    main()
