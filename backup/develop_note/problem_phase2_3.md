# Problems Solved During Phase 2 & 3 Development

This document summarizes the issues encountered and fixed during the implementation of Phase 2 (Service Manager) and Phase 3 (Benchmark Orchestrator).

## Problem 1: Environment variables placed at the end of command

**Date:** 2026-04-08

**Issue:**
- Environment variables like `CUDA_VISIBLE_DEVICES=0` were being appended to the **end** of the server launch command
- They should be at the **beginning** of the command before the actual executable

**Root Cause:**
- The `merge_options()` function in `templates.py` was appending environment variables to the end of the token list

**Fix:**
- Modified `_merge_all_options_tokenized()` to separate environment variables from command tokens
- Prepend all environment variables at the beginning of the final command
- Example: `CUDA_VISIBLE_DEVICES=0 python3 -m sglang.launch_server ...`

**Files Modified:**
- `/root/AUTO_TEST/src/templates.py`

---

## Problem 2: Hardcoded `--max-concurrency 20` in benchmark template

**Date:** 2026-04-08

**Issue:**
- The benchmark template had `--max-concurrency 20` hardcoded
- The user configuration values (10, 20, 30, etc.) were being ignored

**Root Cause:**
- `benchmark_template/benchmark_template_1.md` had the value hardcoded instead of using `${MAX_CONCURRENCY}` variable

**Fix:**
- Replaced `--max-concurrency 20` with `--max-concurrency ${MAX_CONCURRENCY}` in the template
- The variable is now properly substituted with values from user config

**Files Modified:**
- `/root/AUTO_TEST/benchmark_template/benchmark_template_1.md`

---

## Problem 3: Server process blocking due to full output pipe buffer (CRITICAL)

**Date:** 2026-04-08

**Issue:**
- When running benchmarks with large numbers of requests (60, 120, 180), the server process would **block indefinitely**
- Even running benchmarks in a separate terminal would block
- The issue was not with the benchmark subprocess, but with the **server launch process**

**Root Cause:**
- Server was launched with `stdout=subprocess.PIPE` and `stderr=subprocess.STDOUT`
- Server writes lots of output to stdout/stderr during operation
- The OS pipe buffer filled up (~64KB on Linux), and the server blocked waiting to write more output
- We were not reading from the pipe at all!

**Fix:**
- Added a **background thread** (`_read_process_output()`) that continuously reads from the server's stdout/stderr
- Added `output_buffer` to `ServiceInstance` to store the output (optional, for debugging)
- The thread runs as a daemon so it doesn't block program exit
- This ensures the pipe never fills up, no matter how much output the server generates

**Files Modified:**
- `/root/AUTO_TEST/src/service_manager.py`

**Key Changes:**
```python
# Added to ServiceInstance:
output_thread: Optional[threading.Thread] = None
output_buffer: list = field(default_factory=list)

# Background thread function to read output:
def _read_process_output(process, buffer, stop_event):
    for line in process.stdout:
        if stop_event.is_set():
            break
        buffer.append(line)

# Start the thread when launching:
instance.output_thread = threading.Thread(
    target=_read_process_output,
    args=(instance.process, instance.output_buffer, stop_event),
    daemon=True
)
instance.output_thread.start()
```

---

## Problem 4: Server processes not being fully killed

**Date:** 2026-04-08

**Issue:**
- Sometimes server processes would remain alive even after calling `kill_service()`
- The port would still be occupied when trying to launch a new service

**Root Cause:**
- When using `shell=True`, `subprocess.Popen` only kills the shell process, not the child Python process
- Multiple child processes could be spawned

**Fix:**
- Use `preexec_fn=os.setsid` to create a new process group when launching
- When killing, use `os.killpg()` to kill the entire process group
- Also added explicit port checking before launching and after killing:
  - `_get_pids_listening_on_port()` - uses `lsof` to find PIDs on a port
  - `_kill_pid()` - kills a single PID with SIGTERM then SIGKILL
  - `_kill_processes_on_port()` - kills all processes on a given port

**Files Modified:**
- `/root/AUTO_TEST/src/service_manager.py`

---

## Summary Statistics

- **Total Problems Fixed:** 4
- **Critical Problems:** 1 (server blocking)
- **Files Modified:** 3 core files + 1 template
- **Key Lessons:** Always read from subprocess pipes when using `stdout=subprocess.PIPE`!
