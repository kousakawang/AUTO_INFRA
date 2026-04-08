"""
Template management module.
Loads templates and generates commands from them.
"""
import os
import re
from typing import Dict, List, Tuple
from .config_generator import ServiceConfig, BenchmarkCase


def parse_env_var(env_str: str) -> Tuple[str, str]:
    """Parse an environment variable string like 'KEY=value' into (key, value)."""
    if '=' not in env_str:
        return (env_str, '')
    key, value = env_str.split('=', 1)
    return (key.strip(), value.strip())


def tokenize_command(cmd_str: str) -> List[str]:
    """Split a command string into tokens, handling quotes properly."""
    tokens = []
    current = []
    in_quote = None

    for char in cmd_str:
        if char in ('"', "'"):
            if in_quote == char:
                in_quote = None
            elif in_quote is None:
                in_quote = char
            current.append(char)
        elif char.isspace() and in_quote is None:
            if current:
                tokens.append(''.join(current))
                current = []
        else:
            current.append(char)

    if current:
        tokens.append(''.join(current))

    return tokens


def build_command_from_tokens(tokens: List[str]) -> str:
    """Build a command string from tokens."""
    return ' '.join(tokens)


def find_option_in_tokens(tokens: List[str], opt_key: str) -> Tuple[int, bool]:
    """
    Find an option in tokens.
    Returns (index, has_inline_value) where:
    - index is the position of the option key
    - has_inline_value is True if option is like --key=value, False if like --key value
    """
    for i, token in enumerate(tokens):
        if token == opt_key:
            return (i, False)
        if token.startswith(opt_key + '='):
            return (i, True)
    return (-1, False)


def merge_options(base_tokens: List[str], override_opts: List[str]) -> List[str]:
    """
    Merge override options into base tokens.
    Handles both formats: --key value and --key=value
    """
    result = list(base_tokens)

    for opt in override_opts:
        opt = opt.strip()
        if not opt:
            continue

        # Tokenize the override option in case it has multiple parts
        opt_tokens = tokenize_command(opt)

        if not opt_tokens:
            continue

        first_token = opt_tokens[0]

        # Check if it's an env var (key=value and not starting with -)
        if '=' in first_token and not first_token.startswith('-'):
            key, _ = parse_env_var(first_token)
            # Find and replace existing env var
            replaced = False
            for i, token in enumerate(result):
                if '=' in token and not token.startswith('-'):
                    token_key, _ = parse_env_var(token)
                    if token_key == key:
                        result[i] = first_token
                        replaced = True
                        break
            if not replaced:
                result.append(first_token)
            continue

        # It's a command line option
        if first_token.startswith('-'):
            # Extract the option key without value
            if '=' in first_token:
                opt_key = first_token.split('=', 1)[0]
            else:
                opt_key = first_token

            # Find existing option in result
            idx, has_inline = find_option_in_tokens(result, opt_key)

            if idx != -1:
                # Remove the existing option and its value (if any)
                if has_inline:
                    # Remove just the single token
                    result.pop(idx)
                else:
                    # Remove the option and its value (next token)
                    result.pop(idx)
                    if idx < len(result):
                        result.pop(idx)

            # Add the new option
            result.extend(opt_tokens)
            continue

        # It's a regular argument, just add it
        result.append(first_token)

    return result


class TemplateLoader:
    def __init__(self, base_dir: str = "/root/AUTO_TEST"):
        self.base_dir = base_dir
        self.server_templates: Dict[int, str] = {}
        self.benchmark_templates: Dict[int, str] = {}
        self.env_opts: List[str] = []
        self.server_args_opts: List[str] = []

    def load_all(self):
        """Load all templates and optimization options."""
        self.load_server_templates()
        self.load_benchmark_templates()
        self.load_env_opts()
        self.load_server_args_opts()

    def load_server_templates(self):
        """Load launch server templates from launch_server_template/."""
        template_dir = os.path.join(self.base_dir, "launch_server_template")
        if not os.path.exists(template_dir):
            return

        for filename in os.listdir(template_dir):
            match = re.match(r"launch_server_template_(\d+)\.md", filename)
            if match:
                template_id = int(match.group(1))
                filepath = os.path.join(template_dir, filename)
                with open(filepath, 'r') as f:
                    content = f.read().strip()
                self.server_templates[template_id] = content

    def load_benchmark_templates(self):
        """Load benchmark templates from benchmark_template/."""
        template_dir = os.path.join(self.base_dir, "benchmark_template")
        if not os.path.exists(template_dir):
            return

        for filename in os.listdir(template_dir):
            match = re.match(r"benchmark_template_(\d+)\.md", filename)
            if match:
                template_id = int(match.group(1))
                filepath = os.path.join(template_dir, filename)
                with open(filepath, 'r') as f:
                    content = f.read().strip()
                self.benchmark_templates[template_id] = content

    def load_env_opts(self):
        """Load environment options from OPT/ENV_OPT.md."""
        filepath = os.path.join(self.base_dir, "OPT", "ENV_OPT.md")
        if not os.path.exists(filepath):
            return

        with open(filepath, 'r') as f:
            content = f.read()

        # Parse env_opt = [ ... ] format
        match = re.search(r"env_opt\s*=\s*\[(.*?)\]", content, re.DOTALL)
        if match:
            lines = match.group(1).strip().split('\n')
            for line in lines:
                line = line.strip()
                if line.startswith('"') or line.startswith("'"):
                    # Extract the value between quotes, removing trailing comma if present
                    opt = line.strip('",\'')
                    if opt:
                        self.env_opts.append(opt)

    def load_server_args_opts(self):
        """Load server args options from OPT/SERVER_ARG_OPT.md."""
        filepath = os.path.join(self.base_dir, "OPT", "SERVER_ARG_OPT.md")
        if not os.path.exists(filepath):
            return

        with open(filepath, 'r') as f:
            content = f.read()

        # Parse server_args_opt = { ... } format
        match = re.search(r"server_args_opt\s*=\s*\{(.*?)\}", content, re.DOTALL)
        if match:
            lines = match.group(1).strip().split('\n')
            for line in lines:
                line = line.strip()
                if line.startswith('"') or line.startswith("'"):
                    # Extract the value between quotes, removing trailing comma if present
                    opt = line.strip('",\'')
                    if opt:
                        self.server_args_opts.append(opt)


class CommandGenerator:
    def __init__(self, template_loader: TemplateLoader):
        self.template_loader = template_loader

    def generate_server_command(self, service_config: ServiceConfig) -> str:
        """Generate full server launch command with option replacement priority."""
        template = self.template_loader.server_templates.get(service_config.template_id, "")
        if not template:
            raise ValueError(f"Server template {service_config.template_id} not found")

        # Build env opts from all sources with proper priority
        env_opts = []

        # Add CUDA_VISIBLE_DEVICES from device_id
        if service_config.device_id:
            device_str = ",".join(str(d) for d in service_config.device_id)
            env_opts.append(f"CUDA_VISIBLE_DEVICES={device_str}")

        # Add env opts from env_opt_id
        env_opts_from_file = []
        for opt_id in service_config.env_opt_ids:
            if opt_id >= 0 and opt_id < len(self.template_loader.env_opts):
                env_opts_from_file.append(self.template_loader.env_opts[opt_id])

        # Build server args from all sources
        server_opts_from_file = []
        for opt_id in service_config.server_args_opt_ids:
            if opt_id >= 0 and opt_id < len(self.template_loader.server_args_opts):
                server_opts_from_file.append(self.template_loader.server_args_opts[opt_id])

        # Build additional options
        additional_opts_list = []
        for opt in service_config.additional_options:
            if opt and opt != "None" and opt is not None:
                additional_opts_list.append(opt)

        # Deploy method conversion
        deploy_method = service_config.deploy_method
        if deploy_method.startswith("tp"):
            tp_size = deploy_method[2:]
            deploy_arg = f"--tensor-parallel-size {tp_size}"
        else:
            deploy_arg = deploy_method

        # First substitute variables to get the base command with template options
        variables = {
            "ENV_OPT": "",  # We'll handle env opts separately for merging
            "MODEL_PATH": service_config.model_path,
            "PORT": str(service_config.port),
            "STATIC_MEM_USE": "0.7",
            "DEPLOY_METHOD": deploy_arg,
            "SERVER_OPT_ARGS": "",  # We'll handle server args separately for merging
        }

        base_command = self._substitute_variables(template, variables)

        # Now apply merging with priority using token-based approach
        return self._merge_all_options_tokenized(
            base_command,
            env_opts,
            env_opts_from_file,
            server_opts_from_file,
            additional_opts_list
        )

    def _merge_all_options_tokenized(self, base_command: str, device_env_opts: List[str],
                                  env_opts_from_file: List[str], server_opts_from_file: List[str],
                                  additional_opts: List[str]) -> str:
        """
        Merge all options with priority: additional_opts > (env_opts_from_file, server_opts_from_file) > template.

        This uses token-based merging which properly handles --key value format.
        Environment variables are placed at the BEGINNING.
        """
        # Tokenize the base command
        tokens = tokenize_command(base_command)

        # Apply env_opts_from_file (override template env opts)
        tokens = merge_options(tokens, env_opts_from_file)

        # Apply server_opts_from_file (override template args)
        tokens = merge_options(tokens, server_opts_from_file)

        # Apply additional_opts (override everything)
        tokens = merge_options(tokens, additional_opts)

        # Make sure device_env_opts (CUDA_VISIBLE_DEVICES) are included and take highest priority
        tokens = merge_options(tokens, device_env_opts)

        # Now separate env vars and non-env tokens - put env vars FIRST
        env_vars = []
        non_env = []
        for token in tokens:
            if '=' in token and not token.startswith('-'):
                env_vars.append(token)
            else:
                non_env.append(token)

        # Reconstruct: env vars FIRST, then the rest
        final_tokens = env_vars + non_env

        # Reconstruct the full command
        return build_command_from_tokens(final_tokens)

    def generate_benchmark_command(self, service_config: ServiceConfig,
                                   benchmark_case: BenchmarkCase) -> str:
        """Generate benchmark command."""
        template = self.template_loader.benchmark_templates.get(1, "")
        if not template:
            template = "python3 -m sglang.bench_serving --backend sglang-oai-chat --dataset-name image --num-prompts ${NUM_PROMPT} --apply-chat-template --random-output-len ${OUT_LEN} --random-input-len ${IN_LEN} --image-resolution ${IMAGE_SIZE} --image-format jpeg --image-count ${IMAGE_COUNT} --image-content random --random-range-ratio 1 --max-concurrency ${MAX_CONCURRENCY} --host=127.0.0.1 --port=${PORT}"

        variables = {
            "NUM_PROMPT": str(benchmark_case.num_prompts),
            "OUT_LEN": str(benchmark_case.output_len),
            "IN_LEN": str(benchmark_case.input_len),
            "IMAGE_SIZE": benchmark_case.image_size,
            "IMAGE_COUNT": str(benchmark_case.image_count),
            "MAX_CONCURRENCY": str(benchmark_case.max_concurrency),
            "PORT": str(service_config.port),
        }

        return self._substitute_variables(template, variables)

    def _substitute_variables(self, template: str, variables: Dict[str, str]) -> str:
        """Substitute ${VAR} in template with values."""
        result = template
        for var_name, var_value in variables.items():
            result = result.replace(f"${{{var_name}}}", var_value)
        # Clean up extra whitespace
        result = re.sub(r'\s+', ' ', result).strip()
        return result
