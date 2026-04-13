"""
Core components for config file generation.
"""
import re
import os
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Any
from datetime import datetime


@dataclass
class ParsedCommand:
    """Data class for parsed raw command."""
    env_vars: Dict[str, str] = field(default_factory=dict)
    cuda_visible_devices: List[int] = field(default_factory=list)
    model_path: str = ""
    port: int = 0
    tensor_parallel_size: int = 1
    mem_fraction_static: float = 0.7
    disable_radix_cache: bool = False
    server_args: Dict[str, Any] = field(default_factory=dict)
    raw_args: List[str] = field(default_factory=list)


@dataclass
class ParsedBenchmark:
    """Data class for parsed benchmark command."""
    input_len: int = 32
    output_len: int = 64
    image_size: str = "448x448"
    image_count: int = 1
    max_concurrency: int = 20
    num_prompts: int = 120
    port: int = 0


class RawCommandParser:
    """Parses raw launch server and benchmark commands."""

    def __init__(self):
        pass

    def parse_launch_command(self, cmd: str) -> ParsedCommand:
        """Parse a raw launch server command."""
        result = ParsedCommand()
        cmd = cmd.strip()

        # Split into tokens, handling quotes properly
        tokens = self._tokenize(cmd)
        result.raw_args = tokens.copy()

        i = 0
        while i < len(tokens):
            token = tokens[i]

            # Environment variables (KEY=VALUE)
            if "=" in token and not token.startswith("-"):
                if "CUDA_VISIBLE_DEVICES" in token:
                    val = token.split("=", 1)[1]
                    result.cuda_visible_devices = [int(x) for x in val.split(",") if x.strip()]
                else:
                    key, val = token.split("=", 1)
                    result.env_vars[key] = val
                i += 1
                continue

            # Parse python -m sglang.launch_server and its args
            if token == "--model-path" and i + 1 < len(tokens):
                result.model_path = tokens[i + 1]
                i += 2
            elif token == "--port" and i + 1 < len(tokens):
                result.port = int(tokens[i + 1])
                i += 2
            elif token == "--tensor-parallel-size" and i + 1 < len(tokens):
                result.tensor_parallel_size = int(tokens[i + 1])
                i += 2
            elif token == "--mem-fraction-static" and i + 1 < len(tokens):
                result.mem_fraction_static = float(tokens[i + 1])
                i += 2
            elif token == "--disable-radix-cache":
                result.disable_radix_cache = True
                i += 1
            elif token.startswith("-"):
                # Store all other args
                key = token
                if i + 1 < len(tokens) and not tokens[i + 1].startswith("-"):
                    # Argument with value
                    val = tokens[i + 1]
                    # Handle cuda-graph-bs which has multiple values
                    if key == "--cuda-graph-bs":
                        vals = []
                        j = i + 1
                        while j < len(tokens) and not tokens[j].startswith("-"):
                            vals.append(tokens[j])
                            j += 1
                        result.server_args[key] = " ".join(vals)
                        i = j
                    else:
                        result.server_args[key] = val
                        i += 2
                else:
                    # Flag without value
                    result.server_args[key] = True
                    i += 1
            else:
                i += 1

        return result

    def parse_benchmark_command(self, cmd: str) -> ParsedBenchmark:
        """Parse a raw benchmark command."""
        result = ParsedBenchmark()
        tokens = self._tokenize(cmd.strip())

        i = 0
        while i < len(tokens):
            token = tokens[i]

            if token == "--random-input-len" and i + 1 < len(tokens):
                result.input_len = int(tokens[i + 1])
                i += 2
            elif token == "--random-output-len" and i + 1 < len(tokens):
                result.output_len = int(tokens[i + 1])
                i += 2
            elif token == "--image-resolution" and i + 1 < len(tokens):
                result.image_size = tokens[i + 1]
                i += 2
            elif token == "--image-count" and i + 1 < len(tokens):
                result.image_count = int(tokens[i + 1])
                i += 2
            elif token == "--max-concurrency" and i + 1 < len(tokens):
                result.max_concurrency = int(tokens[i + 1])
                i += 2
            elif token == "--num-prompts" and i + 1 < len(tokens):
                result.num_prompts = int(tokens[i + 1])
                i += 2
            elif token == "--port" and i + 1 < len(tokens):
                port_str = tokens[i + 1]
                if "=" in port_str:
                    port_str = port_str.split("=", 1)[1]
                result.port = int(port_str)
                i += 2
            elif token.startswith("--port="):
                result.port = int(token.split("=", 1)[1])
                i += 1
            else:
                i += 1

        return result

    def _tokenize(self, cmd: str) -> List[str]:
        """Tokenize a command string, handling quotes."""
        tokens = []
        current = []
        in_quote = None
        i = 0
        while i < len(cmd):
            c = cmd[i]
            if c in ('"', "'"):
                if in_quote == c:
                    in_quote = None
                elif in_quote is None:
                    in_quote = c
                else:
                    current.append(c)
            elif c.isspace() and in_quote is None:
                if current:
                    tokens.append("".join(current))
                    current = []
            else:
                current.append(c)
            i += 1
        if current:
            tokens.append("".join(current))
        return tokens


class TemplateMatcher:
    """Matches parsed commands to templates and identifies differences."""

    def __init__(self, template_dir: str):
        self.template_dir = template_dir
        self.server_templates = self._load_server_templates()

    def _load_server_templates(self) -> Dict[int, str]:
        """Load server templates from directory."""
        templates = {}
        template_files = [
            "launch_server_template_1.md",
            "launch_server_template_2.md"
        ]
        for filename in template_files:
            # Extract ID from filename: launch_server_template_N.md -> N
            import re
            match = re.match(r"launch_server_template_(\d+)\.md", filename)
            if match:
                template_id = int(match.group(1))
                filepath = os.path.join(self.template_dir, filename)
                if os.path.exists(filepath):
                    with open(filepath, "r") as f:
                        templates[template_id] = f.read().strip()
        return templates

    def determine_template_id(self, parsed: ParsedCommand) -> int:
        """Determine which template to use based on radix cache."""
        # Template 1 (launch_server_template_1.md) has --disable-radix-cache
        # Template 2 (launch_server_template_2.md) does not
        if parsed.disable_radix_cache:
            return 1
        return 2

    def get_template_args(self, template_id: int) -> List[str]:
        """Get the default args from a template."""
        if template_id not in self.server_templates:
            return []
        template = self.server_templates[template_id]
        parser = RawCommandParser()
        # Create a dummy command to extract args from template
        dummy_cmd = template.replace("${ENV_OPT}", "")
        dummy_cmd = dummy_cmd.replace("${MODEL_PATH}", "/dummy/path")
        dummy_cmd = dummy_cmd.replace("${PORT}", "8080")
        dummy_cmd = dummy_cmd.replace("${STATIC_MEM_USE}", "0.7")
        dummy_cmd = dummy_cmd.replace("${DEPLOY_METHOD}", "--tensor-parallel-size 1")
        dummy_cmd = dummy_cmd.replace("${SERVER_OPT_ARGS}", "")
        parsed = parser.parse_launch_command(dummy_cmd)
        return list(parsed.server_args.keys())

    def get_template_args_with_values(self, template_id: int) -> Dict[str, Any]:
        """Get the default args with their values from a template."""
        if template_id not in self.server_templates:
            return {}
        template = self.server_templates[template_id]
        parser = RawCommandParser()
        # Create a dummy command to extract args from template
        dummy_cmd = template.replace("${ENV_OPT}", "")
        dummy_cmd = dummy_cmd.replace("${MODEL_PATH}", "/dummy/path")
        dummy_cmd = dummy_cmd.replace("${PORT}", "8080")
        dummy_cmd = dummy_cmd.replace("${STATIC_MEM_USE}", "0.7")
        dummy_cmd = dummy_cmd.replace("${DEPLOY_METHOD}", "--tensor-parallel-size 1")
        dummy_cmd = dummy_cmd.replace("${SERVER_OPT_ARGS}", "")
        parsed = parser.parse_launch_command(dummy_cmd)
        return parsed.server_args


class OptMatcher:
    """Matches options against OPT files."""

    def __init__(self, opt_dir: str):
        self.opt_dir = opt_dir
        self.env_opts = self._load_env_opts()
        self.server_args_opts = self._load_server_args_opts()

    def _load_env_opts(self) -> List[str]:
        """Load environment options from ENV_OPT.md."""
        filepath = os.path.join(self.opt_dir, "ENV_OPT.md")
        opts = []
        if os.path.exists(filepath):
            with open(filepath, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and "=" in line and not line.startswith("#"):
                        # Clean up the line
                        line = line.rstrip(",")
                        line = line.strip('"')
                        opts.append(line)
        return opts

    def _load_server_args_opts(self) -> List[str]:
        """Load server args options from SERVER_ARG_OPT.md."""
        filepath = os.path.join(self.opt_dir, "SERVER_ARG_OPT.md")
        opts = []
        if os.path.exists(filepath):
            with open(filepath, "r") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("--"):
                        # Clean up the line
                        line = line.rstrip(",")
                        line = line.strip('"')
                        opts.append(line)
        return opts

    def match_env_opts(self, parsed: ParsedCommand) -> List[int]:
        """Match parsed env vars against ENV_OPT and return IDs."""
        matched = []
        for key, val in parsed.env_vars.items():
            opt_str = f"{key}={val}"
            if opt_str in self.env_opts:
                matched.append(self.env_opts.index(opt_str))
        return matched if matched else [-1]

    def match_server_args_opts(self, parsed: ParsedCommand) -> List[int]:
        """Match parsed server args against SERVER_ARG_OPT and return IDs."""
        matched = []
        for opt_str in self.server_args_opts:
            parts = opt_str.split(maxsplit=1)
            key = parts[0]
            if key in parsed.server_args:
                if len(parts) == 1:
                    # Flag without value
                    if parsed.server_args.get(key) is True:
                        matched.append(self.server_args_opts.index(opt_str))
                else:
                    # Argument with value
                    val = parts[1]
                    if str(parsed.server_args.get(key, "")) == val:
                        matched.append(self.server_args_opts.index(opt_str))
        return matched if matched else [-1]


class ConflictResolver:
    """
    Resolves conflicts between raw command and template/OPT defaults.
    Puts overrides into additional_option.
    """

    def __init__(self, template_matcher: TemplateMatcher, opt_matcher: OptMatcher):
        self.template_matcher = template_matcher
        self.opt_matcher = opt_matcher

    def resolve(self, parsed: ParsedCommand, template_id: int,
                env_opt_ids: List[int], server_opt_ids: List[int]) -> str:
        """
        Resolve conflicts and return additional_option string.
        Returns empty string if no overrides needed.
        NOTE: additional_option can include both env vars and server args!
        """
        overrides = []

        # Get template defaults and OPT options
        template_args = self.template_matcher.get_template_args(template_id)
        template_args_with_values = self.template_matcher.get_template_args_with_values(template_id)
        applied_env_opts = set()
        applied_server_opts = set()

        for idx in env_opt_ids:
            if idx >= 0 and idx < len(self.opt_matcher.env_opts):
                applied_env_opts.add(self.opt_matcher.env_opts[idx])

        for idx in server_opt_ids:
            if idx >= 0 and idx < len(self.opt_matcher.server_args_opts):
                opt = self.opt_matcher.server_args_opts[idx]
                key = opt.split(maxsplit=1)[0]
                applied_server_opts.add(key)

        # Add env vars not in OPT (like SGLANG_VLM_CACHE_SIZE_MB)
        for key, val in parsed.env_vars.items():
            opt_str = f"{key}={val}"
            if opt_str not in applied_env_opts and key != "CUDA_VISIBLE_DEVICES":
                overrides.append(opt_str)

        # Check for mem-fraction-static (not in OPT but in template)
        if parsed.mem_fraction_static != 0.7:
            overrides.append(f"--mem-fraction-static {parsed.mem_fraction_static}")

        # Check all server args from raw command
        for key, val in parsed.server_args.items():
            # Skip if it's in OPT
            if key in applied_server_opts:
                continue
            # Always add special args that are typically in additional_option
            if key in ("--context-length", "--reasoning-parser"):
                if val is True:
                    overrides.append(key)
                else:
                    overrides.append(f"{key} {val}")
                continue
            # Check if this arg is in the template - if so, compare values!
            if key in template_args:
                template_val = template_args_with_values.get(key)
                # If values are different, add to overrides!
                if str(val) != str(template_val):
                    if val is True:
                        overrides.append(key)
                    else:
                        overrides.append(f"{key} {val}")
            else:
                # Not in template at all - add it
                if val is True:
                    overrides.append(key)
                else:
                    overrides.append(f"{key} {val}")

        return " ".join(overrides)


class SmartDefaultGenerator:
    """Generates smart defaults for device_id, port, etc."""

    def __init__(self):
        self.next_port = 8080
        self.used_devices = set()
        self.services = []

    def prepare_global_allocation(self, services: List[ParsedCommand]):
        """Prepare for global device allocation by collecting all explicit assignments first."""
        self.services = services
        self.used_devices = set()
        # First register all explicit devices
        for service in services:
            if service.cuda_visible_devices:
                for d in service.cuda_visible_devices:
                    self.used_devices.add(d)

    def generate_port(self, parsed: Optional[ParsedCommand] = None) -> int:
        """Generate a port number, using parsed value if available."""
        if parsed and parsed.port > 0:
            self.next_port = parsed.port + 10
            return parsed.port
        port = self.next_port
        self.next_port += 10
        return port

    def generate_device_id(self, parsed: Optional[ParsedCommand] = None,
                           tp_size: int = 1, service_idx: int = 0) -> List[int]:
        """Generate device ID list with global view, using parsed value if available."""
        if parsed and parsed.cuda_visible_devices:
            return parsed.cuda_visible_devices

        # Simple brute-force allocation with global view
        # Try all possible starting points from 0 upwards
        for start in range(32):
            # Check if this range is available
            available = True
            candidate_devices = []
            for i in range(tp_size):
                d = start + i
                if d in self.used_devices:
                    available = False
                    break
                candidate_devices.append(d)

            if available:
                # Found a good range!
                for d in candidate_devices:
                    self.used_devices.add(d)
                return candidate_devices

        # Fallback: just pick any available devices
        devices = []
        d = 0
        while len(devices) < tp_size and d < 64:
            if d not in self.used_devices:
                devices.append(d)
                self.used_devices.add(d)
            d += 1
        return devices


class ConfigBuilder:
    """
    Main class for building config files from raw commands.
    """

    def __init__(self, project_root: str):
        self.project_root = project_root
        self.template_dir = os.path.join(project_root, "configs", "templates")
        self.opt_dir = os.path.join(project_root, "configs", "OPT")

        self.template_matcher = TemplateMatcher(self.template_dir)
        self.opt_matcher = OptMatcher(self.opt_dir)
        self.conflict_resolver = ConflictResolver(self.template_matcher, self.opt_matcher)
        self.default_generator = SmartDefaultGenerator()

        self.services = []
        self.benchmarks_by_port = {}

    def add_launch_command(self, cmd: str):
        """Add a raw launch server command."""
        parser = RawCommandParser()
        parsed = parser.parse_launch_command(cmd)
        self.services.append(parsed)

    def add_benchmark_command(self, cmd: str):
        """Add a raw benchmark command."""
        parser = RawCommandParser()
        parsed = parser.parse_benchmark_command(cmd)
        if parsed.port not in self.benchmarks_by_port:
            self.benchmarks_by_port[parsed.port] = []
        self.benchmarks_by_port[parsed.port].append(parsed)

    def build_config(self) -> Dict:
        """Build the complete config dict."""
        # Group services by model path
        model_paths = []
        model_to_services = {}
        for service in self.services:
            if service.model_path not in model_to_services:
                model_paths.append(service.model_path)
                model_to_services[service.model_path] = []
            model_to_services[service.model_path].append(service)

        model_test_times = [len(model_to_services[mp]) for mp in model_paths]

        # Build service-level configs
        all_services = []
        for mp in model_paths:
            all_services.extend(model_to_services[mp])

        user_config = {
            "model_paths": model_paths,
            "model_test_times": model_test_times,
            "model_deploy_method": [],
            "device_id": [],
            "basic_template_id": [],
            "port": [],
            "env_opt_id": [],
            "server_args_opt_id": [],
            "additional_option": [],
            "benchmark_case_num": [],
            "benchmark_inputlen": [],
            "benchmark_outputlen": [],
            "benchmark_image_size": [],
            "benchmark_image_count": [],
            "benchmark_max_concurrency": [],
        }

        # FIRST PASS: Prepare global device allocation (register explicit devices)
        self.default_generator.prepare_global_allocation(all_services)

        # Build config for each service
        for idx, service in enumerate(all_services):
            # Basic fields
            tp_size = service.tensor_parallel_size
            user_config["model_deploy_method"].append(f"tp{tp_size}")
            user_config["device_id"].append(
                self.default_generator.generate_device_id(service, tp_size, idx)
            )
            user_config["port"].append(
                self.default_generator.generate_port(service)
            )

            # Template ID
            template_id = self.template_matcher.determine_template_id(service)
            user_config["basic_template_id"].append(template_id)

            # OPT matching
            env_opt_ids = self.opt_matcher.match_env_opts(service)
            server_opt_ids = self.opt_matcher.match_server_args_opts(service)
            user_config["env_opt_id"].append(env_opt_ids)
            user_config["server_args_opt_id"].append(server_opt_ids)

            # Additional option (conflict resolution)
            additional_opt = self.conflict_resolver.resolve(
                service, template_id, env_opt_ids, server_opt_ids
            )
            user_config["additional_option"].append([additional_opt])

            # Benchmark config
            benchmarks = self.benchmarks_by_port.get(service.port, [])
            if not benchmarks:
                # Add default benchmark
                user_config["benchmark_case_num"].append([1])
                user_config["benchmark_inputlen"].append([32])
                user_config["benchmark_outputlen"].append([64])
                user_config["benchmark_image_size"].append(["448x448"])
                user_config["benchmark_image_count"].append([1])
                user_config["benchmark_max_concurrency"].append([20])
            else:
                user_config["benchmark_case_num"].append([len(benchmarks)])
                user_config["benchmark_inputlen"].append([b.input_len for b in benchmarks])
                user_config["benchmark_outputlen"].append([b.output_len for b in benchmarks])
                user_config["benchmark_image_size"].append([b.image_size for b in benchmarks])
                user_config["benchmark_image_count"].append([b.image_count for b in benchmarks])
                user_config["benchmark_max_concurrency"].append([b.max_concurrency for b in benchmarks])

        pipeline_config = {
            "per_config_benchmark_times": 5,
            "prompt_num_dvide_max_concurrency": 6,
            "data_watch_policy": "remove_min_max",
            "max_existed_service_num": 2,
            "do_visuallize": True,
            "SLO": [100000000.0, 100000000.0],
        }

        return {
            "user_config": user_config,
            "pipeline_config": pipeline_config,
        }

    def generate_config_file(self, output_dir: str = "test_cases") -> str:
        """Generate and write config file to output directory."""
        config_dict = self.build_config()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        filepath = os.path.join(output_dir, f"config_{timestamp}.py")

        # Use pprint for nicer formatting
        import pprint

        content = '''"""
Auto-generated configuration file.
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

config_dict = '''
        content += pprint.pformat(config_dict, indent=4, width=100)
        content += "\n"

        with open(filepath, "w") as f:
            f.write(content)

        return filepath
