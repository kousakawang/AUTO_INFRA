# config_validator Skill

Load, validate, and expand benchmark configuration files.

## Purpose
This skill handles configuration loading, validation, and expansion. Use this when you need to:
- Load a config file from disk
- Validate that a config has all required fields
- Expand a simple user config to a full execution config with ServiceConfig objects
- Load template files

## Key Functions

### `load_config_from_file(filepath: str) -> Dict`
Load a config dictionary from a Python file. The file must define a `config_dict` variable.

**Args:**
- `filepath`: Path to the config Python file

**Returns:**
- The config_dict loaded from the file

**Example:**
```python
from skills.config_validator import load_config_from_file
config_dict = load_config_from_file("examples/demo_config.py")
```

---

### `validate_config(config_dict: Dict) -> Tuple[bool, List[str]]`
Validate a configuration dictionary.

**Args:**
- `config_dict`: Configuration with user_config and optional pipeline_config

**Returns:**
- Tuple of `(is_valid: bool, list_of_errors: List[str])`

**Example:**
```python
from skills.config_validator import validate_config
is_valid, errors = validate_config(config_dict)
if not is_valid:
    print("Validation errors:", errors)
```

---

### `expand_config(config_dict: Dict) -> FullConfig`
Expand a user config to a full execution config.

**Args:**
- `config_dict`: Configuration with user_config and pipeline_config

**Returns:**
- `FullConfig` object with expanded services

**Example:**
```python
from skills.config_validator import expand_config
full_config = expand_config(config_dict)
print(f"Expanded to {len(full_config.services)} services")
```

---

### `load_and_validate_config(filepath: str) -> Tuple[FullConfig, TemplateLoader, Dict]`
All-in-one: load config from file, validate, expand, and load templates.

**Args:**
- `filepath`: Path to config file

**Returns:**
- Tuple of `(full_config: FullConfig, template_loader: TemplateLoader, config_dict: Dict)`

**Example:**
```python
from skills.config_validator import load_and_validate_config
full_config, template_loader, config_dict = load_and_validate_config("examples/demo_config.py")
```

## When to Use This Skill
1. **At the start of any workflow** - Load and validate your config first
2. **Before launching services** - Ensure config is valid
3. **When inspecting configs** - See what services would be launched

## See Also
- `skills/service_manager/README.md` - Next step: launch services
- `AGENT_GUIDELINES.md` - Complete usage guide
