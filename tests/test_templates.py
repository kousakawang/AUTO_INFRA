"""
Tests for templates module.
"""
import sys
import os
sys.path.insert(0, '..')

from src import TemplateLoader, CommandGenerator, ServiceConfig, BenchmarkCase


def count_env_opts_from_file(filepath):
    """Count number of env options from ENV_OPT.md file."""
    if not os.path.exists(filepath):
        return 0
    with open(filepath, 'r') as f:
        content = f.read()
    lines = content.split('\n')
    # Count non-empty, non-header lines that look like options
    count = 0
    in_list = False
    for line in lines:
        line = line.strip()
        if 'env_opt' in line and '=' in line:
            in_list = True
            continue
        if in_list:
            if ']' in line:
                break
            if line and (line.startswith('"') or line.startswith("'")):
                count += 1
    return count


def count_server_args_opts_from_file(filepath):
    """Count number of server args options from SERVER_ARG_OPT.md file."""
    if not os.path.exists(filepath):
        return 0
    with open(filepath, 'r') as f:
        content = f.read()
    lines = content.split('\n')
    # Count non-empty, non-header lines that look like options
    count = 0
    in_list = False
    for line in lines:
        line = line.strip()
        if 'server_args_opt' in line and '=' in line:
            in_list = True
            continue
        if in_list:
            if '}' in line:
                break
            if line and (line.startswith('"') or line.startswith("'")):
                count += 1
    return count


def test_template_loader():
    """Test that templates are loaded correctly."""
    base_dir = "/root/AUTO_TEST"
    loader = TemplateLoader(base_dir=base_dir)
    loader.load_all()

    # Should have server templates 1 and 2
    assert 1 in loader.server_templates
    assert 2 in loader.server_templates
    assert len(loader.server_templates) == 2

    # Should have benchmark template 1
    assert 1 in loader.benchmark_templates
    assert len(loader.benchmark_templates) >= 1

    # Should have env opts (count from actual file)
    env_opt_file = os.path.join(base_dir, "OPT", "ENV_OPT.md")
    expected_env_opts = count_env_opts_from_file(env_opt_file)
    assert len(loader.env_opts) == expected_env_opts

    # Should have server args opts (count from actual file)
    server_opt_file = os.path.join(base_dir, "OPT", "SERVER_ARG_OPT.md")
    expected_server_opts = count_server_args_opts_from_file(server_opt_file)
    assert len(loader.server_args_opts) == expected_server_opts


def test_server_command_generation():
    """Test generating server launch command."""
    loader = TemplateLoader(base_dir="/root/AUTO_TEST")
    loader.load_all()

    generator = CommandGenerator(loader)

    # Create a test service config
    service = ServiceConfig(
        global_id=0,
        model_path="/test/model/path",
        model_index=0,
        deploy_method="tp1",
        device_id=[0],
        template_id=1,
        port=8888,
        env_opt_ids=[-1],
        server_args_opt_ids=[0],
        additional_options=["--test-opt"],
        benchmark_cases=[]
    )

    cmd = generator.generate_server_command(service)

    # Check that key parts are in the command
    assert "CUDA_VISIBLE_DEVICES=0" in cmd
    assert "/test/model/path" in cmd
    assert "--port 8888" in cmd
    assert "--tensor-parallel-size 1" in cmd
    assert "--test-opt" in cmd


def test_benchmark_command_generation():
    """Test generating benchmark command."""
    loader = TemplateLoader(base_dir="/root/AUTO_TEST")
    loader.load_all()

    generator = CommandGenerator(loader)

    # Create a test service config
    service = ServiceConfig(
        global_id=0,
        model_path="/test/model/path",
        model_index=0,
        deploy_method="tp1",
        device_id=[0],
        template_id=1,
        port=8888,
        env_opt_ids=[-1],
        server_args_opt_ids=[0],
        additional_options=[""],
        benchmark_cases=[]
    )

    # Create a test benchmark case
    case = BenchmarkCase(
        case_id=0,
        input_len=32,
        output_len=64,
        image_size="448x448",
        image_count=1,
        max_concurrency=20,
        num_prompts=120
    )

    cmd = generator.generate_benchmark_command(service, case)

    # Check that key parts are in the command
    assert "--num-prompts 120" in cmd
    assert "--random-input-len 32" in cmd
    assert "--random-output-len 64" in cmd
    assert "--image-resolution 448x448" in cmd
    assert "--image-count 1" in cmd
    assert "--max-concurrency 20" in cmd
    assert "--port=8888" in cmd


def test_variable_substitution():
    """Test that variable substitution works correctly."""
    loader = TemplateLoader(base_dir="/root/AUTO_TEST")
    loader.load_all()

    generator = CommandGenerator(loader)

    # Test with template 1 which has --disable-radix-cache
    service = ServiceConfig(
        global_id=0,
        model_path="/test/model",
        model_index=0,
        deploy_method="tp2",
        device_id=[1, 2],
        template_id=1,
        port=9999,
        env_opt_ids=[0],  # Use first env opt
        server_args_opt_ids=[1],  # Use second server arg opt
        additional_options=[],
        benchmark_cases=[]
    )

    cmd = generator.generate_server_command(service)

    # Check template 2 has the disable radix cache flag
    assert "--disable-radix-cache" in cmd
    # Check tensor parallel size 2
    assert "--tensor-parallel-size 2" in cmd
    # Check CUDA devices 1,2
    assert "CUDA_VISIBLE_DEVICES=1,2" in cmd
    # Check env opt is included
    assert loader.env_opts[0] in cmd
    # Check server arg opt is included
    assert loader.server_args_opts[1] in cmd
