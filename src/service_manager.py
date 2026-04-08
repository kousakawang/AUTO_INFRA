"""
Service Manager - Handles server process lifecycle.
"""
import os
import subprocess
import time
import socket
import logging
import signal
import errno
import threading
from typing import Dict, Optional, Tuple
from dataclasses import dataclass, field

from .config_generator import ServiceConfig, FullConfig
from .templates import CommandGenerator, tokenize_command, parse_env_var

logger = logging.getLogger(__name__)


@dataclass
class ServiceInstance:
    """Represents a single running service instance."""
    global_id: int
    port: int
    model_path: str
    process: Optional[subprocess.Popen] = None
    state: str = "pending"  # "pending", "starting", "ready", "running", "stopping", "stopped"
    start_time: Optional[float] = None
    ready_time: Optional[float] = None
    service_config: Optional[ServiceConfig] = None
    launch_command: str = ""
    env_vars: Dict[str, str] = field(default_factory=dict)
    output_thread: Optional[threading.Thread] = None
    output_buffer: list = field(default_factory=list)


def _get_pids_listening_on_port(port: int) -> list:
    """
    Get list of PIDs listening on the given port using lsof.
    Returns empty list if no process found or lsof not available.
    """
    try:
        result = subprocess.run(
            ['lsof', '-t', f'-i:{port}', '-sTCP:LISTEN'],
            capture_output=True,
            text=True,
            timeout=5
        )
        pids = result.stdout.strip().split('\n')
        return [int(pid) for pid in pids if pid.strip()]
    except (subprocess.SubprocessError, FileNotFoundError, ValueError):
        return []


def _kill_pid(pid: int, timeout: float = 10.0) -> bool:
    """
    Kill a process by PID with SIGTERM first, then SIGKILL.
    Returns True if killed successfully.
    """
    try:
        # Check if process exists
        os.kill(pid, 0)
    except OSError as e:
        if e.errno == errno.ESRCH:
            # Process doesn't exist
            return True
        return False

    # Try SIGTERM
    try:
        os.kill(pid, signal.SIGTERM)
    except OSError:
        pass

    # Wait and check
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            os.kill(pid, 0)
        except OSError as e:
            if e.errno == errno.ESRCH:
                return True
        time.sleep(0.5)

    # Try SIGKILL
    try:
        os.kill(pid, signal.SIGKILL)
    except OSError:
        pass

    # Check again
    time.sleep(0.5)
    try:
        os.kill(pid, 0)
        return False
    except OSError as e:
        if e.errno == errno.ESRCH:
            return True
        return False


def _kill_processes_on_port(port: int) -> bool:
    """
    Kill all processes listening on the given port.
    Returns True if all processes were killed (or none existed).
    """
    pids = _get_pids_listening_on_port(port)
    if not pids:
        return True

    logger.info(f"Found {len(pids)} process(es) listening on port {port}: {pids}")
    all_killed = True
    for pid in pids:
        logger.info(f"Killing process {pid} on port {port}")
        if not _kill_pid(pid):
            logger.warning(f"Failed to kill process {pid}")
            all_killed = False
    return all_killed


def _read_process_output(process, buffer, stop_event):
    """Background thread function to read process output."""
    try:
        for line in process.stdout:
            if stop_event.is_set():
                break
            buffer.append(line)
            # Could also log here if needed: logger.debug(line.rstrip())
    except Exception:
        pass


class ServiceManager:
    """Manages the lifecycle of model serving services."""

    def __init__(self, full_config: FullConfig, command_generator: CommandGenerator):
        self.full_config = full_config
        self.command_generator = command_generator
        self.services: Dict[int, ServiceInstance] = {}
        self.max_concurrent = full_config.pipeline_config.get("max_existed_service_num", 2)

    def create_service_instance(self, service_config: ServiceConfig) -> ServiceInstance:
        """Create a service instance without launching it yet."""
        instance = ServiceInstance(
            global_id=service_config.global_id,
            port=service_config.port,
            model_path=service_config.model_path,
            state="pending",
            service_config=service_config
        )
        self.services[service_config.global_id] = instance
        return instance

    def _parse_command_and_env(self, full_command: str) -> Tuple[str, Dict[str, str]]:
        """
        Split a command string into the actual command and environment variables.

        Returns:
            (command_str, env_dict)
        """
        tokens = tokenize_command(full_command)
        env_vars = dict(os.environ)
        command_tokens = []

        for token in tokens:
            if '=' in token and not token.startswith('-'):
                # This looks like an environment variable
                key, value = parse_env_var(token)
                env_vars[key] = value
            else:
                command_tokens.append(token)

        command_str = ' '.join(command_tokens)
        return command_str, env_vars

    def launch_service(self, service_config: ServiceConfig, dry_run: bool = False) -> ServiceInstance:
        """
        Launch a service instance.

        Args:
            service_config: Configuration for the service to launch
            dry_run: If True, don't actually launch the process

        Returns:
            ServiceInstance object
        """
        if service_config.global_id in self.services:
            instance = self.services[service_config.global_id]
        else:
            instance = self.create_service_instance(service_config)

        # Generate the full command
        full_command = self.command_generator.generate_server_command(service_config)
        instance.launch_command = full_command

        logger.info(f"Service {instance.global_id}: Generating launch command")
        logger.info(f"Service {instance.global_id}: Command: {full_command}")
        

        # Parse env vars and command
        command_str, env_vars = self._parse_command_and_env(full_command)
        instance.env_vars = env_vars

        logger.debug(f"Service {instance.global_id}: Clean command: {command_str}")
        logger.debug(f"Service {instance.global_id}: Env vars: {dict(env_vars)}")

        if dry_run:
            logger.info(f"Service {instance.global_id}: Dry run - not launching process")
            instance.state = "ready"
            instance.start_time = time.time()
            instance.ready_time = time.time()
            return instance

        # Kill any existing processes on this port first
        logger.info(f"Service {instance.global_id}: Checking port {instance.port} for existing processes")
        _kill_processes_on_port(instance.port)

        # Launch the process
        logger.info(f"Service {instance.global_id}: Launching process on port {instance.port}")
        instance.state = "starting"
        instance.start_time = time.time()

        try:
            # Launch with stdout/stderr piped, and use a thread to read output
            # This prevents the process from blocking on full pipe buffers
            instance.process = subprocess.Popen(
                command_str,
                shell=True,
                env=env_vars,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                preexec_fn=os.setsid  # Create a new process group
            )

            logger.info(f"Service {instance.global_id}: Process started with PID {instance.process.pid} (PGID: {os.getpgid(instance.process.pid)})")

            # Start a background thread to read output
            stop_event = threading.Event()
            instance.output_thread = threading.Thread(
                target=_read_process_output,
                args=(instance.process, instance.output_buffer, stop_event),
                daemon=True
            )
            instance.output_thread.start()

        except Exception as e:
            logger.error(f"Service {instance.global_id}: Failed to launch - {e}")
            instance.state = "stopped"
            raise

        return instance

    def _check_port_listening(self, port: int, host: str = "127.0.0.1") -> bool:
        """Check if a port is accepting connections."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1.0)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except Exception:
            return False

    def wait_for_ready(self, instance: ServiceInstance, timeout: int = 300,
                      check_interval: float = 2.0, dry_run: bool = False) -> bool:
        """
        Wait for a service to become ready.

        Args:
            instance: Service instance to wait for
            timeout: Maximum time to wait in seconds
            check_interval: How often to check in seconds
            dry_run: If True, return immediately without checking

        Returns:
            True if service is ready, False otherwise
        """
        if dry_run:
            logger.info(f"Service {instance.global_id}: Dry run - assuming ready")
            instance.state = "ready"
            instance.ready_time = time.time()
            return True

        if instance.state == "ready":
            return True

        if instance.state != "starting":
            logger.warning(f"Service {instance.global_id}: Cannot wait for ready in state {instance.state}")
            return False

        logger.info(f"Service {instance.global_id}: Waiting for readiness on port {instance.port}")
        start_time = time.time()

        while time.time() - start_time < timeout:
            # Check if process is still running
            if instance.process and instance.process.poll() is not None:
                logger.error(f"Service {instance.global_id}: Process died unexpectedly")
                instance.state = "stopped"
                return False

            # Check if port is listening
            if self._check_port_listening(instance.port):
                instance.state = "ready"
                instance.ready_time = time.time()
                wait_time = instance.ready_time - instance.start_time
                logger.info(f"Service {instance.global_id}: Ready after {wait_time:.1f}s")
                return True

            time.sleep(check_interval)

        logger.error(f"Service {instance.global_id}: Timed out waiting for ready after {timeout}s")
        return False

    def kill_service(self, instance: ServiceInstance, dry_run: bool = False,
                    grace_period: float = 10.0) -> bool:
        """
        Kill a running service.

        Args:
            instance: Service instance to kill
            dry_run: If True, don't actually kill the process
            grace_period: Seconds to wait after SIGTERM before SIGKILL

        Returns:
            True if service was killed successfully
        """
        if instance.state == "stopped":
            logger.debug(f"Service {instance.global_id}: Already stopped")
            return True

        logger.info(f"Service {instance.global_id}: Stopping service")
        instance.state = "stopping"

        if dry_run:
            logger.info(f"Service {instance.global_id}: Dry run - not killing process")
            instance.state = "stopped"
            return True

        if not instance.process:
            logger.warning(f"Service {instance.global_id}: No process to kill")
            instance.state = "stopped"
            # Still try to kill anything on the port
            _kill_processes_on_port(instance.port)
            return True

        # Try to kill the process group first (kills all children)
        killed = False
        try:
            pgid = os.getpgid(instance.process.pid)
            logger.info(f"Service {instance.global_id}: Sending SIGTERM to process group {pgid}")
            os.killpg(pgid, signal.SIGTERM)
        except (OSError, ProcessLookupError) as e:
            logger.warning(f"Service {instance.global_id}: Failed to send SIGTERM to group - {e}")
            # Fall back to just the process
            try:
                instance.process.terminate()
            except Exception as e2:
                logger.warning(f"Service {instance.global_id}: SIGTERM failed - {e2}")

        # Wait for process to exit
        try:
            instance.process.wait(timeout=grace_period)
            killed = True
            logger.info(f"Service {instance.global_id}: Process exited gracefully")
        except subprocess.TimeoutExpired:
            # Still running - try SIGKILL on process group
            logger.warning(f"Service {instance.global_id}: Grace period expired, sending SIGKILL")
            try:
                pgid = os.getpgid(instance.process.pid)
                os.killpg(pgid, signal.SIGKILL)
            except (OSError, ProcessLookupError):
                # Fall back to just the process
                try:
                    instance.process.kill()
                except Exception:
                    pass
            # Wait a bit more
            try:
                instance.process.wait(timeout=5.0)
                killed = True
                logger.info(f"Service {instance.global_id}: Process killed")
            except subprocess.TimeoutExpired:
                logger.error(f"Service {instance.global_id}: Process still alive after SIGKILL")
                killed = False

        instance.state = "stopped"

        # Also explicitly kill anything still on the port
        logger.info(f"Service {instance.global_id}: Checking for leftover processes on port {instance.port}")
        _kill_processes_on_port(instance.port)

        return killed

    def get_service(self, global_id: int) -> Optional[ServiceInstance]:
        """Get a service instance by global ID."""
        return self.services.get(global_id)

    def cleanup_all(self, dry_run: bool = False):
        """Clean up all running services."""
        logger.info("Cleaning up all services")
        for instance in list(self.services.values()):
            if instance.state in ("starting", "ready", "running"):
                self.kill_service(instance, dry_run=dry_run)
