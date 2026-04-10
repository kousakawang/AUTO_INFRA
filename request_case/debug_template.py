#!/usr/bin/env python3
"""Debug template loading."""
import os
import sys

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.templates import TemplateLoader, CommandGenerator
from skills.config_validator import load_and_validate_config


def main():
    config_path = os.path.join(project_root, "request_case", "config_request_1.py")
    full_config, template_loader, config_dict = load_and_validate_config(config_path)

    print("Template 2 content:")
    print(repr(template_loader.server_templates[2]))
    print()

    # Check what SERVER_ARG_OPT contains
    print("SERVER_ARG_OPTS:")
    for i, opt in enumerate(template_loader.server_args_opts):
        print(f"  [{i}]: {repr(opt)}")

    print()
    print("ENV_OPTS:")
    for i, opt in enumerate(template_loader.env_opts):
        print(f"  [{i}]: {repr(opt)}")

    # Test command generation for service 0
    print()
    print("Testing command generation for service 0:")
    service = full_config.services[0]
    cmd_gen = CommandGenerator(template_loader)

    # First do the variable substitution manually
    template = template_loader.server_templates[2]
    deploy_arg = "--tensor-parallel-size 1"

    variables = {
        "ENV_OPT": "",
        "MODEL_PATH": service.model_path,
        "PORT": str(service.port),
        "STATIC_MEM_USE": "0.7",
        "DEPLOY_METHOD": deploy_arg,
        "SERVER_OPT_ARGS": "",
    }

    result = template
    for var_name, var_value in variables.items():
        result = result.replace(f"${{{var_name}}}", var_value)

    print(f"After substitution: {repr(result)}")


if __name__ == "__main__":
    main()
