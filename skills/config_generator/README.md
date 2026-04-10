# config_generator Skill (Pre-existing)

Parse raw commands and requirements into configuration files.

## Purpose
This skill parses raw launch server and benchmark commands and generates configuration files. This skill was already present before the reconstruction.

## Usage

### Command Line

```bash
# From a raw test case file
python3 skills/generate_config.py --file raw_folder/raw_test_case.sh

# Interactive mode
python3 skills/generate_config.py
```

### Key Files
- `skills/generate_config.py` - Main entry point
- `skills/config_generator/config_builder.py` - Core logic for building configs
- `skills/config_generator/cli.py` - Command line interface

## See Also
- `skills/config_validator/README.md` - Validate the generated config
- `how_to_use_for_agent.md` - Original guide for using this skill
