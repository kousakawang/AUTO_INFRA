#!/usr/bin/env python3
"""
Convenience wrapper for the config generator skill.
Usage:
    python -m skills.config_generator.generate_config --file raw_folder/raw_test_case.sh
    python -m skills.config_generator.generate_config  # interactive mode
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from skills.config_generator.cli import main

if __name__ == "__main__":
    main()
