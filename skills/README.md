# Config Generator Skill

This skill makes it easy to generate configuration files from raw server launch and benchmark commands.

## Usage

### Command Line Mode

Parse from a raw test case file:

```bash
# Non-interactive mode
python3 skills/generate_config.py --file raw_folder/raw_test_case.sh

# With custom output directory
python3 skills/generate_config.py --file raw_folder/raw_test_case.sh --output my_configs
```

### Interactive Mode

```bash
python3 skills/generate_config.py
```

This will prompt you to:
1. Parse from a raw file or enter commands manually
2. Preview the generated config
3. Save it to the test_cases directory

### What it Does

The config generator automatically:

**A. Fills opt_part (env_opt, server_opt)**
- Matches environment variables against `OPT/ENV_OPT.md`
- Matches server arguments against `OPT/SERVER_ARG_OPT.md`
- Returns IDs for matched options, -1 for no match

**B. Fills additional_option part**
- Extracts environment variables not in OPT files
- Extracts server arguments not in templates or OPT files
- Handles special args like `--context-length`, `--reasoning-parser`
- **Important**: Uses `additional_option` to override any conflicting template/OPT defaults

**C. Fills benchmark part**
- Extracts input length, output length from benchmark commands
- Extracts image size, image count, max concurrency
- Handles multiple benchmark cases per service

**D. Auto-fills device_id and port**
- Default port: starts at 8080, increments by 10 for each service
- Default device_id: round-robin across GPUs starting from 0
- Handles tensor parallelism (tp2 uses [0,1], [2,3], etc.)
- Uses values from raw commands if provided

**E. Determines template ID**
- Checks for `--disable-radix-cache` in command
- If present: uses template 1 (launch_server_template_1.md)
- If not present: uses template 2 (launch_server_template_2.md)

## Example

Input (raw_test_case.sh):
```bash
SGLANG_VLM_CACHE_SIZE_MB=0 CUDA_VISIBLE_DEVICES=0 python3 -m sglang.launch_server --model-path /data01/models/Qwen3.5-9B --port 8080 --disable-radix-cache --context-length 262144 --reasoning-parser qwen3
python3 -m sglang.bench_serving --random-output-len 64 --random-input-len 32 --max-concurrency 20 --port=8080
```

Output (config file):
- `additional_option`: `["SGLANG_VLM_CACHE_SIZE_MB=0 --context-length 262144 --reasoning-parser qwen3"]`
- `basic_template_id`: 1 (has --disable-radix-cache)
- All benchmark parameters extracted automatically
