# service_manager Skill

Launch, monitor, and terminate model serving services.

## Purpose
This skill manages the lifecycle of model serving services. Use this when you need to:
- Launch a model serving instance from a ServiceConfig
- Wait for a service to become ready
- Kill running services
- Clean up all services

## Key Classes

### `ServiceManagerSkill(template_loader: TemplateLoader, full_config: Optional[FullConfig] = None)`
Main skill class for service management.

**Methods:**

#### `.launch_service(service_config: ServiceConfig, dry_run: bool = False) -> ServiceInstance`
Launch a service from a ServiceConfig.

**Args:**
- `service_config`: Configuration for the service to launch
- `dry_run`: If True, don't actually launch the process

**Returns:**
- `ServiceInstance` wrapper representing the launched service

---

#### `.wait_for_ready(instance: ServiceInstance, timeout: int = 300, check_interval: float = 2.0, dry_run: bool = False) -> bool`
Wait for a service to become ready.

**Args:**
- `instance`: ServiceInstance to wait for
- `timeout`: Maximum wait time in seconds
- `check_interval`: How often to check in seconds
- `dry_run`: If True, return immediately

**Returns:**
- `True` if service is ready

---

#### `.kill_service(instance: ServiceInstance, dry_run: bool = False) -> bool`
Kill a running service.

**Args:**
- `instance`: ServiceInstance to kill
- `dry_run`: If True, don't actually kill

**Returns:**
- `True` if killed successfully

---

#### `.cleanup_all(dry_run: bool = False)`
Clean up all running services.

---

## Convenience Functions (Global)

These functions use a global skill instance:

- `launch_service(service_config, template_loader=None, dry_run=False)`
- `wait_for_ready(instance, template_loader=None, timeout=300, dry_run=False)`
- `kill_service(instance, template_loader=None, dry_run=False)`
- `cleanup_all_services(template_loader=None, dry_run=False)`

## Example Usage

```python
from skills.config_validator import load_and_validate_config
from skills.service_manager import ServiceManagerSkill

# Load config first
full_config, template_loader, config_dict = load_and_validate_config("examples/demo_config.py")

# Initialize skill
service_skill = ServiceManagerSkill(template_loader, full_config)

# Get first service config
service_config = full_config.services[0]

try:
    # Launch service
    instance = service_skill.launch_service(service_config, dry_run=True)
    print(f"Service launched on port {instance.port}")
    print(f"Command: {instance.launch_command}")

    # Wait for ready
    if service_skill.wait_for_ready(instance, dry_run=True):
        print("Service is ready!")

finally:
    # Always clean up
    service_skill.kill_service(instance, dry_run=True)
```

## Important Patterns

### Launch Service Once, Benchmark Multiple Times
When optimizing for SLO or varying benchmark parameters:
```python
# Launch ONCE
instance = service_skill.launch_service(service_config, dry_run=True)
service_skill.wait_for_ready(instance, dry_run=True)

try:
    # Benchmark MANY times with different parameters
    for concurrency in [10, 20, 30, 40, 50]:
        # run benchmark here with this concurrency
        pass
finally:
    # Clean up ONCE
    service_skill.kill_service(instance, dry_run=True)
```

### Always Clean Up
Use try/finally to ensure services are killed even if something fails:
```python
instance = service_skill.launch_service(service_config, dry_run=True)
try:
    # do work
finally:
    service_skill.kill_service(instance, dry_run=True)
```

## When to Use This Skill
1. **When you need to launch model servers**
2. **For SLO optimization workflows** - keep service running while varying concurrency
3. **For parameter search** - test different options

## See Also
- `skills/config_validator/README.md` - Load configs first
- `skills/benchmark_runner/README.md` - Run benchmarks on launched services
- `AGENT_GUIDELINES.md` - Complete usage guide
