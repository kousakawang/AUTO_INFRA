# Test Suite

This directory contains unit tests for the AI Model Serving Benchmark Framework.

## Running Tests

### Prerequisites
- Python 3.8+
- pytest >= 7.0.0 (install with `pip install pytest`)

### Run All Tests
```bash
cd tests
python -m pytest -v
```

### Run Individual Test Files
```bash
# Run config tests only
python -m pytest test_config.py -v

# Run config generator tests only
python -m pytest test_config_generator.py -v

# Run template tests only
python -m pytest test_templates.py -v
```

### Test Coverage
- `test_config.py` - Tests for configuration loading and validation
- `test_config_generator.py` - Tests for config expansion and data classes
- `test_templates.py` - Tests for template loading and command generation
