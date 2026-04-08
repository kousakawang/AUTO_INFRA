# Phase 1 Plan: Core Infrastructure & Configuration

## Overview
Phase 1 focuses on building the foundation of the benchmark framework: configuration handling, template management, and basic project structure.

**Simplification:** Only Python dict format will be supported for config input (matches the example workflow).

## Project Structure Setup

### Step 1: Create Directory Structure
```
/root/AUTO_TEST/
├── src/
│   ├── __init__.py
│   ├── config.py
│   ├── config_generator.py
│   └── templates.py
├── tests/
│   ├── __init__.py
│   ├── test_config.py
│   ├── test_config_generator.py
│   └── test_templates.py
├── examples/
│   └── example_config.py
├── outputs/               # For benchmark results
├── reports/               # For generated reports
└── requirements.txt
```

### Step 2: Create requirements.txt
```txt
# Core dependencies
python>=3.8

# Testing
pytest>=7.0.0
```

---

## Module 1: src/config.py - Configuration Handling

### Purpose
Load and validate user configuration (Python dict only).

### Key Classes/Functions

#### 1.1 Config Class
```python
class Config:
    def __init__(self, config_dict: dict):
        self.user_config = config_dict.get("user_config", {})
        self.pipeline_config = config_dict.get("pipeline_config", {})
    
    @classmethod
    def from_dict(cls, config_dict: dict) -> "Config":
        """Load config from Python dictionary."""
        pass
    
    def validate(self) -> list[str]:
        """Validate configuration structure and values, return list of errors."""
        pass
```

#### 1.2 Validation Functions
```python
def validate_user_config(config: dict) -> list[str]:
    """
    Validate user_config structure:
    - Check required keys exist
    - Check array lengths match (sum(model_test_times) == len(model_deploy_method))
    - Check ports are valid and unique
    - Check device IDs are valid
    - Return list of validation errors (empty if valid)
    """
    pass

def get_default_pipeline_config() -> dict:
    """Return default pipeline configuration."""
    return {
        "per_config_benchmark_times": 5,
        "prompt_num_dvide_max_concurrency": 6,
        "data_watch_policy": "remove_min_max",
        "max_existed_service_num": 2,
        "do_visuallize": True,
        "SLO": [1e8, 1e8],
    }
```

### File: src/config.py Implementation Outline
```python
"""
Configuration handling module.
Loads, validates, and provides access to benchmark configuration.
"""
from typing import Dict, List, Optional


def get_default_pipeline_config() -> Dict:
    return {
        "per_config_benchmark_times": 5,
        "prompt_num_dvide_max_concurrency": 6,
        "data_watch_policy": "remove_min_max",
        "max_existed_service_num": 2,
        "do_visuallize": True,
        "SLO": [1e8, 1e8],
    }


def validate_user_config(config: Dict) -> List[str]:
    errors = []
    
    # Check required keys
    required_keys = [
        "model_paths", "model_test_times", "model_deploy_method",
        "device_id", "basic_template_id", "port",
        "env_opt_id", "server_args_opt_id", "additional_option",
        "benchmark_case_num", "benchmark_inputlen", "benchmark_outputlen",
        "benchmark_image_size", "benchmark_image_count", "benchmark_max_concurrency"
    ]
    
    for key in required_keys:
        if key not in config:
            errors.append(f"Missing required key: {key}")
    
    if errors:
        return errors
    
    # Check that model_test_times and model_paths have same length
    if len(config["model_paths"]) != len(config["model_test_times"]):
        errors.append(f"model_paths length ({len(config['model_paths'])}) != model_test_times length ({len(config['model_test_times'])})")
        return errors
    
    # Check that total test times matches other arrays
    total_tests = sum(config["model_test_times"])
    
    array_fields = [
        "model_deploy_method", "device_id", "basic_template_id", "port",
        "env_opt_id", "server_args_opt_id", "additional_option", "benchmark_case_num",
        "benchmark_inputlen", "benchmark_outputlen", "benchmark_image_size",
        "benchmark_image_count", "benchmark_max_concurrency"
    ]
    
    for field_name in array_fields:
        arr = config.get(field_name, [])
        if len(arr) != total_tests:
            errors.append(f"{field_name} length ({len(arr)}) != total test times ({total_tests})")
    
    # Check ports are unique
    ports = config.get("port", [])
    if len(ports) != len(set(ports)):
        errors.append("Ports must be unique")
    
    return errors


class Config:
    def __init__(self, config_dict: Dict):
        self.user_config = config_dict.get("user_config", {})
        
        # Merge with default pipeline config
        default_pipeline = get_default_pipeline_config()
        user_pipeline = config_dict.get("pipeline_config", {})
        self.pipeline_config = {**default_pipeline, **user_pipeline}
    
    @classmethod
    def from_dict(cls, config_dict: Dict) -> "Config":
        return cls(config_dict)
    
    def validate(self) -> List[str]:
        return validate_user_config(self.user_config)
```

---

## Module 2: src/config_generator.py - Config Expansion

### Purpose
Expand simple user config into full, detailed config for execution.

### Key Classes/Functions

#### 2.1 ConfigExpander Class
```python
class ConfigExpander:
    def __init__(self, user_config: dict, pipeline_config: dict):
        self.user_config = user_config
        self.pipeline_config = pipeline_config
    
    def expand(self) -> "FullConfig":
        """Expand user config to full config."""
        pass
    
    def _expand_array(self, arr: List, target_length: int) -> List:
        """Expand array by repeating last element if needed."""
        pass
```

### File: src/config_generator.py Implementation Outline
```python
"""
Configuration expansion module.
Expands simple user config into detailed execution config.
"""
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class BenchmarkCase:
    case_id: int
    input_len: int
    output_len: int
    image_size: str
    image_count: int
    max_concurrency: int
    num_prompts: int


@dataclass
class ServiceConfig:
    global_id: int
    model_path: str
    model_index: int
    deploy_method: str
    device_id: List[int]
    template_id: int
    port: int
    env_opt_ids: List[int]
    server_args_opt_ids: List[int]
    additional_options: List[str]
    benchmark_cases: List[BenchmarkCase]


class FullConfig:
    def __init__(self):
        self.services: List[ServiceConfig] = []
        self.pipeline_config: Optional[Dict] = None


class ConfigExpander:
    def __init__(self, user_config: Dict, pipeline_config: Dict):
        self.user_config = user_config
        self.pipeline_config = pipeline_config
    
    def expand(self) -> FullConfig:
        """Expand user configuration to full execution configuration."""
        full_config = FullConfig()
        full_config.pipeline_config = self.pipeline_config
        
        global_id = 0
        cfg = self.user_config
        
        for model_idx, (model_path, test_times) in enumerate(
            zip(cfg["model_paths"], cfg["model_test_times"])
        ):
            for _ in range(test_times):
                service_config = self._create_service_config(global_id, model_idx, model_path)
                full_config.services.append(service_config)
                global_id += 1
        
        return full_config
    
    def _create_service_config(self, global_id: int, model_idx: int, model_path: str) -> ServiceConfig:
        """Create configuration for a single service."""
        cfg = self.user_config
        
        # Get benchmark case count for this service
        case_count_list = cfg["benchmark_case_num"][global_id]
        case_count = case_count_list[0] if case_count_list else 1
        
        # Expand benchmark arrays
        input_lens = self._expand_array(cfg["benchmark_inputlen"][global_id], case_count)
        output_lens = self._expand_array(cfg["benchmark_outputlen"][global_id], case_count)
        image_sizes = self._expand_array(cfg["benchmark_image_size"][global_id], case_count)
        image_counts = self._expand_array(cfg["benchmark_image_count"][global_id], case_count)
        max_concurrencies = self._expand_array(cfg["benchmark_max_concurrency"][global_id], case_count)
        
        # Create benchmark cases
        benchmark_cases = []
        for case_idx in range(case_count):
            num_prompts = self.pipeline_config["prompt_num_dvide_max_concurrency"] * max_concurrencies[case_idx]
            benchmark_cases.append(BenchmarkCase(
                case_id=case_idx,
                input_len=input_lens[case_idx],
                output_len=output_lens[case_idx],
                image_size=image_sizes[case_idx],
                image_count=image_counts[case_idx],
                max_concurrency=max_concurrencies[case_idx],
                num_prompts=num_prompts
            ))
        
        return ServiceConfig(
            global_id=global_id,
            model_path=model_path,
            model_index=model_idx,
            deploy_method=cfg["model_deploy_method"][global_id],
            device_id=cfg["device_id"][global_id],
            template_id=cfg["basic_template_id"][global_id],
            port=cfg["port"][global_id],
            env_opt_ids=cfg["env_opt_id"][global_id],
            server_args_opt_ids=cfg["server_args_opt_id"][global_id],
            additional_options=cfg["additional_option"][global_id],
            benchmark_cases=benchmark_cases
        )
    
    def _expand_array(self, arr: List, target_length: int) -> List:
        """Expand array by repeating last element if needed."""
        if not arr:
            return []
        if len(arr) >= target_length:
            return arr[:target_length]
        # Repeat last element
        last = arr[-1]
        return arr + [last] * (target_length - len(arr))
```

---

## Module 3: src/templates.py - Template Management

### Purpose
Load templates from files and substitute variables to generate actual commands.

### Key Classes/Functions

#### 3.1 TemplateLoader Class
```python
class TemplateLoader:
    def __init__(self, base_dir: str = "/root/AUTO_TEST"):
        self.base_dir = base_dir
        self.server_templates: Dict[int, str] = {}
        self.benchmark_templates: Dict[int, str] = {}
        self.env_opts: List[str] = []
        self.server_args_opts: List[str] = []
    
    def load_all(self):
        """Load all templates and optimization options."""
        pass
```

#### 3.2 CommandGenerator Class
```python
class CommandGenerator:
    def __init__(self, template_loader: TemplateLoader):
        self.template_loader = template_loader
    
    def generate_server_command(self, service_config: ServiceConfig) -> str:
        """Generate full server launch command."""
        pass
    
    def generate_benchmark_command(self, service_config: ServiceConfig, 
                                   benchmark_case: BenchmarkCase) -> str:
        """Generate benchmark command."""
        pass
```

### File: src/templates.py Implementation Outline
```python
"""
Template management module.
Loads templates and generates commands from them.
"""
import os
import re
from typing import Dict, List
from .config_generator import ServiceConfig, BenchmarkCase


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
        
        match = re.search(r"env_opt\s*=\s*\[(.*?)\]", content, re.DOTALL)
        if match:
            lines = match.group(1).strip().split('\n')
            for line in lines:
                line = line.strip()
                if line.startswith('"') or line.startswith("'"):
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
        
        match = re.search(r"server_args_opt\s*=\s*\{(.*?)\}", content, re.DOTALL)
        if match:
            lines = match.group(1).strip().split('\n')
            for line in lines:
                line = line.strip()
                if line.startswith('"') or line.startswith("'"):
                    opt = line.strip('",\'')
                    if opt:
                        self.server_args_opts.append(opt)


class CommandGenerator:
    def __init__(self, template_loader: TemplateLoader):
        self.template_loader = template_loader
    
    def generate_server_command(self, service_config: ServiceConfig) -> str:
        """Generate full server launch command."""
        template = self.template_loader.server_templates.get(service_config.template_id, "")
        if not template:
            raise ValueError(f"Server template {service_config.template_id} not found")
        
        # Build env opt string
        env_opts = []
        for opt_id in service_config.env_opt_ids:
            if opt_id >= 0 and opt_id < len(self.template_loader.env_opts):
                env_opts.append(self.template_loader.env_opts[opt_id])
        env_opt_str = " ".join(env_opts) if env_opts else ""
        
        # Build server args opt string
        server_opts = []
        for opt_id in service_config.server_args_opt_ids:
            if opt_id >= 0 and opt_id < len(self.template_loader.server_args_opts):
                server_opts.append(self.template_loader.server_args_opts[opt_id])
        server_opt_args = " ".join(server_opts) if server_opts else ""
        
        # Build additional options
        additional_opts = []
        for opt in service_config.additional_options:
            if opt and opt != "None" and opt is not None:
                additional_opts.append(opt)
        additional_opt_str = " ".join(additional_opts) if additional_opts else ""
        
        # Deploy method conversion
        deploy_method = service_config.deploy_method
        if deploy_method.startswith("tp"):
            tp_size = deploy_method[2:]
            deploy_arg = f"--tensor-parallel-size {tp_size}"
        else:
            deploy_arg = deploy_method
        
        # Build variables dict
        variables = {
            "ENV_OPT": env_opt_str,
            "MODEL_PATH": service_config.model_path,
            "PORT": str(service_config.port),
            "STATIC_MEM_USE": "0.7",
            "DEPLOY_METHOD": deploy_arg,
            "SERVER_OPT_ARGS": f"{server_opt_args} {additional_opt_str}".strip(),
        }
        
        return self._substitute_variables(template, variables)
    
    def generate_benchmark_command(self, service_config: ServiceConfig,
                                   benchmark_case: BenchmarkCase) -> str:
        """Generate benchmark command."""
        template = self.template_loader.benchmark_templates.get(0, "")
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
        result = re.sub(r'\s+', ' ', result).strip()
        return result
```

---

## Module 4: src/__init__.py

```python
"""
AI Model Serving Benchmark Framework - Phase 1
Core Infrastructure & Configuration
"""
from .config import Config, get_default_pipeline_config, validate_user_config
from .config_generator import ConfigExpander, FullConfig, ServiceConfig, BenchmarkCase
from .templates import TemplateLoader, CommandGenerator

__version__ = "0.1.0"
__all__ = [
    "Config", "get_default_pipeline_config", "validate_user_config",
    "ConfigExpander", "FullConfig", "ServiceConfig", "BenchmarkCase",
    "TemplateLoader", "CommandGenerator",
]
```

---

## Example: examples/example_config.py

```python
"""
Example configuration usage.
"""
import sys
sys.path.insert(0, '..')

from src import Config, ConfigExpander, TemplateLoader, CommandGenerator

# Example user config from the documentation
config_dict = {
    "user_config": {
        "model_paths": ["/data01/models/Qwen3.5-9B", "/data01/models/Qwen3-VL-8B"],
        "model_test_times": [3, 1],
        "model_deploy_method": ["tp1", "tp2", "tp1", "tp1"],
        "device_id": [[0], [1, 2], [3], [4]],
        "basic_template_id": [0, 0, 0, 1],
        "port": [8080, 8070, 8060, 8050],
        "env_opt_id": [[-1], [0], [-1], [-1]],
        "server_args_opt_id": [[0], [0], [1], [1]],
        "additional_option": [
            ["--context-length 262144 --reasoning-parser qwen3"],
            ["--context-length 262144 --reasoning-parser qwen3"],
            ["--context-length 262144 --reasoning-parser qwen3"],
            [None]
        ],
        "benchmark_case_num": [[3], [3], [3], [1]],
        "benchmark_inputlen": [[32, 32, 32], [32, 32, 32], [32, 64, 32], [32]],
        "benchmark_outputlen": [[64, 64, 64], [64, 64, 64], [64, 32, 32], [64]],
        "benchmark_image_size": [
            ["448x448", "448x448", "448x448"],
            ["448x448", "448x448", "448x448"],
            ["448x448", "448x448", "448x448"],
            ["1080x720"]
        ],
        "benchmark_image_count": [[1, 1, 1], [1, 1, 1], [1, 1, 1], [1]],
        "benchmark_max_concurrency": [[10, 20, 30], [10, 20, 30], [10, 20, 30], [10]],
    },
    "pipeline_config": {
        "per_config_benchmark_times": 5,
        "prompt_num_dvide_max_concurrency": 6,
        "data_watch_policy": "remove_min_max",
        "max_existed_service_num": 2,
        "do_visuallize": True,
        "SLO": [1e8, 1e8],
    }
}


def main():
    print("=== Phase 1 Demo ===\n")
    
    # 1. Load and validate config
    print("1. Loading configuration...")
    config = Config.from_dict(config_dict)
    
    errors = config.validate()
    if errors:
        print("Validation errors:")
        for err in errors:
            print(f"  - {err}")
        return
    print("   ✓ Config valid!\n")
    
    # 2. Expand config
    print("2. Expanding configuration...")
    expander = ConfigExpander(config.user_config, config.pipeline_config)
    full_config = expander.expand()
    print(f"   ✓ Expanded to {len(full_config.services)} services\n")
    
    # 3. Load templates
    print("3. Loading templates...")
    loader = TemplateLoader()
    loader.load_all()
    print(f"   ✓ Loaded {len(loader.server_templates)} server templates")
    print(f"   ✓ Loaded {len(loader.benchmark_templates)} benchmark templates")
    print(f"   ✓ Loaded {len(loader.env_opts)} env opts")
    print(f"   ✓ Loaded {len(loader.server_args_opts)} server args opts\n")
    
    # 4. Generate commands
    print("4. Generating commands...")
    generator = CommandGenerator(loader)
    
    for service in full_config.services:
        print(f"\n   Service {service.global_id} (port {service.port}):")
        cmd = generator.generate_server_command(service)
        print(f"      Launch: {cmd[:80]}...")
        
        for case in service.benchmark_cases:
            bench_cmd = generator.generate_benchmark_command(service, case)
            print(f"      Benchmark case {case.case_id}: {bench_cmd[:60]}...")
    
    print("\n=== Phase 1 Demo Complete ===")


if __name__ == "__main__":
    main()
```

---

## Tests: tests/test_config.py

```python
"""
Tests for config module.
"""
import sys
sys.path.insert(0, '..')

from src import Config, get_default_pipeline_config, validate_user_config


def test_default_pipeline_config():
    """Test getting default pipeline config."""
    default = get_default_pipeline_config()
    assert "per_config_benchmark_times" in default
    assert default["max_existed_service_num"] == 2


def test_config_validation_valid():
    """Test validation with valid config."""
    user_config = {
        "model_paths": ["/model/1"],
        "model_test_times": [1],
        "model_deploy_method": ["tp1"],
        "device_id": [[0]],
        "basic_template_id": [0],
        "port": [8080],
        "env_opt_id": [[-1]],
        "server_args_opt_id": [[0]],
        "additional_option": [[""]],
        "benchmark_case_num": [[1]],
        "benchmark_inputlen": [[32]],
        "benchmark_outputlen": [[64]],
        "benchmark_image_size": [["448x448"]],
        "benchmark_image_count": [[1]],
        "benchmark_max_concurrency": [[10]],
    }
    
    errors = validate_user_config(user_config)
    assert len(errors) == 0


def test_config_validation_invalid_ports():
    """Test validation with duplicate ports."""
    user_config = {
        "model_paths": ["/model/1", "/model/2"],
        "model_test_times": [1, 1],
        "model_deploy_method": ["tp1", "tp1"],
        "device_id": [[0], [1]],
        "basic_template_id": [0, 0],
        "port": [8080, 8080],  # Duplicate
        "env_opt_id": [[-1], [-1]],
        "server_args_opt_id": [[0], [0]],
        "additional_option": [[""], [""]],
        "benchmark_case_num": [[1], [1]],
        "benchmark_inputlen": [[32], [32]],
        "benchmark_outputlen": [[64], [64]],
        "benchmark_image_size": [["448x448"], ["448x448"]],
        "benchmark_image_count": [[1], [1]],
        "benchmark_max_concurrency": [[10], [10]],
    }
    
    errors = validate_user_config(user_config)
    assert len(errors) > 0
    assert "unique" in str(errors).lower()
```

---

## Implementation Order

1. Create directory structure (mkdir -p src tests examples outputs reports)
2. Create `requirements.txt`
3. Implement `src/config.py`
4. Implement `src/config_generator.py`
5. Implement `src/templates.py`
6. Create `src/__init__.py`
7. Create `examples/example_config.py`
8. Create test files in `tests/`

## Verification Steps

After implementation:
1. Run `python examples/example_config.py` - should load, expand, and generate commands without errors
2. Run `pytest tests/` - all tests should pass
3. Verify generated commands match the format in `launch_server_basic.sh` and `benchmark_cmd_basic.sh`
