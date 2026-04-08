# Examples

This directory contains example scripts demonstrating how to use the AI Model Serving Benchmark Framework.

## Example Configuration

### Running the Example
```bash
cd examples
python example_config.py
```

### What This Example Demonstrates
1. **Loading Configuration** - Loads a sample user config and pipeline config
2. **Validating Config** - Validates the configuration structure
3. **Expanding Config** - Expands the simple config into full execution config
4. **Loading Templates** - Loads server templates, benchmark templates, and optimization options
5. **Generating Commands** - Generates actual server launch commands and benchmark commands

### Sample Output
The example will output:
- Validation status
- Number of services expanded
- Number of templates/options loaded
- Generated launch commands for each service
- Generated benchmark commands for each benchmark case

### Customization
You can modify the `config_dict` in `example_config.py` to test with your own:
- Model paths
- Deployment methods (tp1, tp2, etc.)
- Device IDs
- Benchmark parameters
