"""
Tests for option replacement logic with priority:
additional_option > (env_opt_id, server_args_opt_id) > template

Updated for token-based merging.
"""
import sys
import os
sys.path.insert(0, '..')

from src import TemplateLoader, CommandGenerator, ServiceConfig
from src.templates import merge_options, tokenize_command, parse_env_var


def test_parse_env_var():
    """Test parsing environment variables."""
    assert parse_env_var("KEY=value") == ("KEY", "value")
    assert parse_env_var("CUDA_VISIBLE_DEVICES=0,1") == ("CUDA_VISIBLE_DEVICES", "0,1")
    assert parse_env_var("SGLANG_USE_CUDA_IPC_TRANSPORT=1") == ("SGLANG_USE_CUDA_IPC_TRANSPORT", "1")


def test_tokenize_command():
    """Test command tokenization."""
    cmd = "--key value --key2=value2"
    tokens = tokenize_command(cmd)
    assert tokens == ["--key", "value", "--key2=value2"]


def test_merge_options_env_vars():
    """Test merging environment variables with override."""
    base = ["KEY1=val1", "KEY2=val2"]
    override = ["KEY2=new_val", "KEY3=val3"]
    result = merge_options(base, override)
    # Check that KEY2 is overridden
    assert "KEY2=new_val" in result
    assert "KEY2=val2" not in result
    # Check that KEY1 and KEY3 are present
    assert "KEY1=val1" in result
    assert "KEY3=val3" in result


def test_merge_options_space_separated():
    """Test merging options with space-separated values."""
    base = ["--mm-attention-backend", "fa3"]
    override = ["--mm-attention-backend fa9"]
    result = merge_options(base, override)
    # Check that the new value is present
    assert "--mm-attention-backend" in result
    assert "fa9" in result
    assert "fa3" not in result


def test_case1_additional_replace_template_env():
    """Case 1: Use additional_option to replace template's env_var."""
    loader = TemplateLoader(base_dir="/root/AUTO_TEST")
    loader.server_templates[99] = "TEST_ENV=original python3 -m sglang.launch_server"

    generator = CommandGenerator(loader)
    service = ServiceConfig(
        global_id=0, model_path="/test/model", model_index=0,
        deploy_method="tp1", device_id=[0], template_id=99, port=8888,
        env_opt_ids=[-1], server_args_opt_ids=[-1],
        additional_options=["TEST_ENV=replaced"], benchmark_cases=[]
    )

    cmd = generator.generate_server_command(service)
    assert "TEST_ENV=replaced" in cmd


def test_case2_additional_replace_template_server_args():
    """Case 2: Use additional_option to replace template's server_args."""
    loader = TemplateLoader(base_dir="/root/AUTO_TEST")
    loader.server_templates[99] = "python3 -m sglang.launch_server --mem-fraction-static 0.7"

    generator = CommandGenerator(loader)
    service = ServiceConfig(
        global_id=0, model_path="/test/model", model_index=0,
        deploy_method="tp1", device_id=[0], template_id=99, port=8888,
        env_opt_ids=[-1], server_args_opt_ids=[-1],
        additional_options=["--mem-fraction-static 0.9"], benchmark_cases=[]
    )

    cmd = generator.generate_server_command(service)
    assert "--mem-fraction-static 0.9" in cmd


def test_case3_additional_replace_env_opt_id():
    """Case 3: Use additional_option to replace env_opt_id's option."""
    loader = TemplateLoader(base_dir="/root/AUTO_TEST")
    loader.env_opts = ["SGLANG_TEST=from_file"]
    loader.server_templates[99] = "python3 -m sglang.launch_server"

    generator = CommandGenerator(loader)
    service = ServiceConfig(
        global_id=0, model_path="/test/model", model_index=0,
        deploy_method="tp1", device_id=[0], template_id=99, port=8888,
        env_opt_ids=[0], server_args_opt_ids=[-1],
        additional_options=["SGLANG_TEST=from_additional"], benchmark_cases=[]
    )

    cmd = generator.generate_server_command(service)
    assert "SGLANG_TEST=from_additional" in cmd


def test_case4_additional_replace_server_args_opt_id():
    """Case 4: Use additional_option to replace server_args_opt_id's option."""
    loader = TemplateLoader(base_dir="/root/AUTO_TEST")
    loader.server_args_opts = ["--test-opt=from_file"]
    loader.server_templates[99] = "python3 -m sglang.launch_server"

    generator = CommandGenerator(loader)
    service = ServiceConfig(
        global_id=0, model_path="/test/model", model_index=0,
        deploy_method="tp1", device_id=[0], template_id=99, port=8888,
        env_opt_ids=[-1], server_args_opt_ids=[0],
        additional_options=["--test-opt=from_additional"], benchmark_cases=[]
    )

    cmd = generator.generate_server_command(service)
    assert "--test-opt=from_additional" in cmd #or "from_additional" in cmd


def test_case5_env_opt_id_replace_template():
    """Case 5: Use env_opt_id's option to replace template's option."""
    loader = TemplateLoader(base_dir="/root/AUTO_TEST")
    loader.env_opts = ["SGLANG_TEST=from_env_opt"]
    loader.server_templates[99] = "SGLANG_TEST=from_template python3 -m sglang.launch_server"

    generator = CommandGenerator(loader)
    service = ServiceConfig(
        global_id=0, model_path="/test/model", model_index=0,
        deploy_method="tp1", device_id=[0], template_id=99, port=8888,
        env_opt_ids=[0], server_args_opt_ids=[-1],
        additional_options=[], benchmark_cases=[]
    )

    cmd = generator.generate_server_command(service)
    # print(cmd)
    assert "SGLANG_TEST=from_env_opt" in cmd


def test_case6_server_args_opt_id_replace_template():
    """Case 6: Use server_args_opt_id to replace template's option."""
    loader = TemplateLoader(base_dir="/root/AUTO_TEST")
    loader.server_args_opts = ["--test-arg from_opt"]
    loader.server_templates[99] = "python3 -m sglang.launch_server --test-arg from_template"

    generator = CommandGenerator(loader)
    service = ServiceConfig(
        global_id=0, model_path="/test/model", model_index=0,
        deploy_method="tp1", device_id=[0], template_id=99, port=8888,
        env_opt_ids=[-1], server_args_opt_ids=[0],
        additional_options=[], benchmark_cases=[]
    )

    cmd = generator.generate_server_command(service)
    # print(cmd)
    assert "--test-arg from_opt" in cmd
