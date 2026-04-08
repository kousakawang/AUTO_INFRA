"""
Service Queue - Manages pending and active services with concurrency control.
"""
import logging
from typing import List, Optional
from collections import deque

from .config_generator import ServiceConfig, FullConfig
from .service_manager import ServiceManager, ServiceInstance

logger = logging.getLogger(__name__)


class ServiceQueue:
    """
    Manages a queue of services to launch, with concurrency control.

    Services are processed in FIFO order, with a maximum number of concurrent
    services running at any time.
    """

    def __init__(self, full_config: FullConfig, service_manager: ServiceManager):
        self.full_config = full_config
        self.service_manager = service_manager
        self.max_concurrent = full_config.pipeline_config.get("max_existed_service_num", 2)

        # Queues
        self.pending: deque = deque()  # Services waiting to launch
        self.active: List[ServiceInstance] = []  # Currently running services
        self.completed: List[ServiceInstance] = []  # Finished services

    def add_pending(self, service_config: ServiceConfig):
        """Add a service configuration to the pending queue."""
        logger.debug(f"Queue: Adding service {service_config.global_id} to pending queue")
        self.pending.append(service_config)

    def add_all_pending(self, service_configs: List[ServiceConfig]):
        """Add multiple service configurations to the pending queue."""
        for config in service_configs:
            self.add_pending(config)

    def has_pending(self) -> bool:
        """Check if there are services waiting to launch."""
        return len(self.pending) > 0

    def has_active(self) -> bool:
        """Check if there are services currently running."""
        return len(self.active) > 0

    def has_capacity(self) -> bool:
        """Check if we can launch another service."""
        return len(self.active) < self.max_concurrent

    def launch_next(self, dry_run: bool = False) -> Optional[ServiceInstance]:
        """
        Launch the next pending service if there is capacity.

        Args:
            dry_run: If True, don't actually launch processes

        Returns:
            The launched ServiceInstance, or None if no service was launched
        """
        if not self.has_pending():
            logger.debug("Queue: No pending services to launch")
            return None

        if not self.has_capacity():
            logger.debug(f"Queue: At capacity ({len(self.active)}/{self.max_concurrent})")
            return None

        # Get next service from queue
        service_config = self.pending.popleft()
        logger.info(f"Queue: Launching service {service_config.global_id}")

        # Launch the service
        instance = self.service_manager.launch_service(service_config, dry_run=dry_run)
        self.active.append(instance)

        logger.info(f"Queue: Active services: {len(self.active)}/{self.max_concurrent}")
        return instance

    def mark_completed(self, instance: ServiceInstance):
        """Mark a service as completed and move it to the completed list."""
        if instance in self.active:
            self.active.remove(instance)
            self.completed.append(instance)
            logger.info(f"Queue: Service {instance.global_id} marked as completed")
            logger.info(f"Queue: Active services: {len(self.active)}/{self.max_concurrent}")
        else:
            logger.warning(f"Queue: Service {instance.global_id} not in active list")

    def get_active_services(self) -> List[ServiceInstance]:
        """Get list of currently active services."""
        return list(self.active)

    def get_pending_count(self) -> int:
        """Get number of pending services."""
        return len(self.pending)

    def get_active_count(self) -> int:
        """Get number of active services."""
        return len(self.active)

    def get_completed_count(self) -> int:
        """Get number of completed services."""
        return len(self.completed)

    def get_total_count(self) -> int:
        """Get total number of services."""
        return len(self.pending) + len(self.active) + len(self.completed)

    def wait_for_capacity(self, check_interval: float = 1.0) -> bool:
        """
        Wait until there is capacity to launch a new service.

        Args:
            check_interval: How often to check in seconds

        Returns:
            True when capacity is available
        """
        import time

        while not self.has_capacity():
            time.sleep(check_interval)
        return True

    def reset(self):
        """Reset the queue (for testing)."""
        self.pending.clear()
        self.active.clear()
        self.completed.clear()
