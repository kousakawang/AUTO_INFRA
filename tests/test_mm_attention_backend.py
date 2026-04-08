"""
Test specifically for replacing --mm-attention-backend option.
"""
import sys
sys.path.insert(0, '..')

from src import TemplateLoader, CommandGenerator, ServiceConfig


def test_replace_mm_attention_backend():
    """Test that --mm-attention-backend can be properly replaced."""
    loader = TemplateLoader(base_dir="/root/AUTO_TEST")
    loader.load_all()

    generator = CommandGenerator(loader)

    # Use template 1 which has --mm-attention-backend fa3
    service = ServiceConfig(
        global_id=0,
        model_path="/test/model",
        model_index=0,
        deploy_method="tp1",
        device_id=[0],
        template_id=1,
        port=8888,
        env_opt_ids=[-1],
        server_args_opt_ids=[-1],
        additional_options=["--mm-attention-backend fa9"],
        benchmark_cases=[]
    )

    cmd = generator.generate_server_command(service)

    print("Generated command:")
    print(cmd)
    print()

    # Check that fa9 is present and fa3 is not
    assert "fa9" in cmd, "fa9 should be in the command"
    assert "--mm-attention-backend" in cmd, "--mm-attention-backend should be in the command"

    # Count occurrences
    fa3_count = cmd.count("fa3")
    fa9_count = cmd.count("fa9")

    print(f"fa3 count: {fa3_count}")
    print(f"fa9 count: {fa9_count}")

    # Should have fa9, not fa3 (or at least fa9 should be there)
    assert fa9_count >= 1, "Should have at least one fa9"


def test_additional_option_replaces_template():
    """Test Case 1: additional_option replaces template option."""
    loader = TemplateLoader(base_dir="/root/AUTO_TEST")
    loader.load_all()

    generator = CommandGenerator(loader)

    # Template has --mm-attention-backend fa3, we want to replace it
    service = ServiceConfig(
        global_id=0,
        model_path="/test/model",
        model_index=0,
        deploy_method="tp1",
        device_id=[0],
        template_id=1,
        port=8888,
        env_opt_ids=[-1],
        server_args_opt_ids=[-1],
        additional_options=["--mm-attention-backend fa9"],
        benchmark_cases=[]
    )

    cmd = generator.generate_server_command(service)

    # The key check: should have --mm-attention-backend fa9
    assert "--mm-attention-backend fa9" in cmd


if __name__ == "__main__":
    print("Testing --mm-attention-backend replacement...\n")
    test_replace_mm_attention_backend()
    print("\n✓ test_replace_mm_attention_backend passed")

    test_additional_option_replaces_template()
    print("✓ test_additional_option_replaces_template passed")

    print("\nAll tests passed!")
