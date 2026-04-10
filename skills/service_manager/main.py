"""
Service Manager Skill - Main implementation.
Launches, monitors, and terminates model serving services.
"""
import os
import sys
import time
from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass, field

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from src.config_generator import ServiceConfig
from src.templates import TemplateLoader, CommandGenerator
from src.service_manager import (
    ServiceManager as CoreServiceManager,
    ServiceInstance as CoreServiceInstance
)


@dataclass
class ServiceInstance:
    """Wrapper for CoreServiceInstance with simpler access."""
    global_id: int
    port: int
    model_path: str
    state: str = "pending"
    launch_command: str = ""
    _core_instance: Optional[CoreServiceInstance] = None

    @classmethod
    def from_core(cls, core_instance: CoreServiceInstance) -> "ServiceInstance":
        return cls(
            global_id=core_instance.global_id,
            port=core_instance.port,
            model_path=core_instance.model_path,
            state=core_instance.state,
            launch_command=core_instance.launch_command,
            _core_instance=core_instance
        )


class ServiceManagerSkill:
    """
    Skill wrapper for service management operations.
    """
    def __init__(self, template_loader: TemplateLoader, full_config=None):
        self.template_loader = template_loader
        self.command_generator = CommandGenerator(template_loader)

        # Create a dummy full_config if not provided
        if full_config is None:
            from src.config_generator import FullConfig
            full_config = FullConfig()
            full_config.pipeline_config = {"max_existed_service_num": 2}

        self.core_manager = CoreServiceManager(full_config, self.command_generator)
        self._instances: Dict[int, ServiceInstance] = {}

    def create_service_instance(self, service_config: ServiceConfig) -> ServiceInstance:
        """Create a service instance without launching it."""
        core_instance = self.core_manager.create_service_instance(service_config)
        wrapper = ServiceInstance.from_core(core_instance)
        self._instances[wrapper.global_id] = wrapper
        return wrapper

    def launch_service(self, service_config: ServiceConfig, dry_run: bool = False) -> ServiceInstance:
        """
        Launch a service from a ServiceConfig.

        Args:
            service_config: Configuration for the service
            dry_run: If True, don't actually launch the process

        Returns:
            ServiceInstance representing the launched service
        """
        core_instance = self.core_manager.launch_service(service_config, dry_run=dry_run)
        wrapper = ServiceInstance.from_core(core_instance)
        self._instances[wrapper.global_id] = wrapper
        return wrapper

    def wait_for_ready(self, instance: ServiceInstance, timeout: int = 300,
                       check_interval: float = 2.0, dry_run: bool = False) -> bool:
        """
        Wait for a service to become ready.

        Args:
            instance: ServiceInstance to wait for
            timeout: Maximum wait time in seconds
            check_interval: How often to check in seconds
            dry_run: If True, return immediately

        Returns:
            True if service is ready
        """
        core_instance = instance._core_instance
        if core_instance is None:
            # Look up from core manager
            core_instance = self.core_manager.get_service(instance.global_id)
            if core_instance is None:
                return False

        return self.core_manager.wait_for_ready(
            core_instance, timeout=timeout, check_interval=check_interval, dry_run=dry_run
        )

    def kill_service(self, instance: ServiceInstance, dry_run: bool = False) -> bool:
        """
        Kill a running service.

        Args:
            instance: ServiceInstance to kill
            dry_run: If True, don't actually kill

        Returns:
            True if killed successfully
        """
        core_instance = instance._core_instance
        if core_instance is None:
            core_instance = self.core_manager.get_service(instance.global_id)
            if core_instance is None:
                return True

        result = self.core_manager.kill_service(core_instance, dry_run=dry_run)
        instance.state = "stopped"
        return result

    def cleanup_all(self, dry_run: bool = False):
        """Clean up all running services."""
        self.core_manager.cleanup_all(dry_run=dry_run)
        for instance in self._instances.values():
            instance.state = "stopped"

    def get_service(self, global_id: int) -> Optional[ServiceInstance]:
        """Get a service instance by ID."""
        return self._instances.get(global_id)


# Convenience functions for standalone use
_global_skill: Optional[ServiceManagerSkill] = None


def _get_skill(template_loader: Optional[TemplateLoader] = None) -> ServiceManagerSkill:
    """Get or create the global skill instance."""
    global _global_skill
    if _global_skill is None:
        if template_loader is None:
            template_loader = TemplateLoader(project_root)
            template_loader.load_all()
        _global_skill = ServiceManagerSkill(template_loader)
    return _global_skill


def launch_service(service_config: ServiceConfig, template_loader: Optional[TemplateLoader] = None,
                   dry_run: bool = False) -> ServiceInstance:
    """
    Launch a service (convenience function).

    Args:
        service_config: Service configuration
        template_loader: Optional template loader
        dry_run: If True, don't actually launch

    Returns:
        ServiceInstance
    """
    skill = _get_skill(template_loader)
    return skill.launch_service(service_config, dry_run=dry_run)


def wait_for_ready(instance: ServiceInstance, template_loader: Optional[TemplateLoader] = None,
                   timeout: int = 300, dry_run: bool = False) -> bool:
    """Wait for service to be ready (convenience function)."""
    skill = _get_skill(template_loader)
    return skill.wait_for_ready(instance, timeout=timeout, dry_run=dry_run)


def kill_service(instance: ServiceInstance, template_loader: Optional[TemplateLoader] = None,
                 dry_run: bool = False) -> bool:
    """Kill a service (convenience function)."""
    skill = _get_skill(template_loader)
    return skill.kill_service(instance, dry_run=dry_run)


def cleanup_all_services(template_loader: Optional[TemplateLoader] = None,
                         dry_run: bool = False):
    """Clean up all services (convenience function)."""
    skill = _get_skill(template_loader)
    skill.cleanup_all(dry_run=dry_run)
