# Phase 2 & 3 Improvement TODO Plan

This document describes potential improvements to the current Phase 2 & 3 implementation.

## Current Limitations

The current implementation works, but has the following limitations:

1. **Sequential benchmarking only**: Even with `max_existed_service_num=2`, we benchmark services one-by-one
2. **Wasteful waiting**: We wait for the entire active service list to become empty before launching the next one
3. **GPU under-utilization**: GPUs may be idle while waiting for other benchmarks to complete

---

## Improvement 1: Parallel Benchmarking

**Priority:** High

**Description:**
Currently, even when multiple services are running (up to `max_existed_service_num`), we still benchmark them sequentially. We should benchmark multiple services in parallel.

**Current Flow:**
```
Launch Service 0 → Benchmark Service 0 → Kill Service 0 → Launch Service 1 → Benchmark Service 1 → ...
OR
Launch Service 0 → Launch Service 1 → Benchmark Service 0 → Kill Service 0 → Benchmark Service 1 → Kill Service 1
```

**Improved Flow:**
```
Launch Service 0 → Benchmark Service 0 (in thread/process)
Launch Service 1 → Benchmark Service 1 (in thread/process)
[Services 0 and 1 benchmark in parallel]
```

**Implementation Plan:**
1. Modify `ServiceQueue` to track which services are ready for benchmarking
2. Create a `BenchmarkWorker` class or use threading to run benchmarks in parallel
3. Use a thread pool (e.g., `concurrent.futures.ThreadPoolExecutor`)
4. Ensure thread safety when accessing shared data structures

**Files to Modify:**
- `/root/AUTO_TEST/src/service_queue.py` - Add tracking for benchmark-ready services
- `/root/AUTO_TEST/src/benchmark_orchestrator.py` - Add parallel execution support
- (Optional) Create new `/root/AUTO_TEST/src/benchmark_workers.py`

---

## Improvement 2: Launch Next Service Immediately After Previous is Killed

**Priority:** High

**Description:**
Currently, we tend to wait for the running service list to become empty before launching the next one. Instead, we should launch the next service **as soon as a slot becomes available** (immediately after a service is killed).

**Current Behavior:**
- `max_existed_service_num = 2`
- Launch 0, Launch 1
- Benchmark 0 (1 is idle!)
- Kill 0
- **Wait for active list to be empty**
- Launch 2, Launch 3
- Benchmark 2 (3 is idle!)

**Improved Behavior:**
- `max_existed_service_num = 2`
- Launch 0, Launch 1
- Benchmark 0, Benchmark 1 (in parallel)
- Kill 0, **IMMEDIATELY launch 2** (slot is available!)
- Kill 1, **IMMEDIATELY launch 3** (slot is available!)
- Continue benchmarking...

**Implementation Plan:**
1. In the main loop, after killing a service and marking it as completed, **immediately try to launch the next pending service**
2. Don't wait for all active services to complete - maintain the `max_existed_service_num` capacity at all times
3. The queue should always be trying to fill available slots

**Files to Modify:**
- `/root/AUTO_TEST/examples/test_phase2_3.py` - Main loop logic
- `/root/AUTO_TEST/examples/test_phase2_3_real.py` - Main loop logic
- `/root/AUTO_TEST/examples/test_phase2_3_simple.py` - Main loop logic

**Pseudo-code:**
```python
while queue.has_pending() or queue.has_active():
    # Fill available slots FIRST - always try to launch
    while queue.has_pending() and queue.has_capacity():
        instance = queue.launch_next()
        # wait for ready, etc.

    # Process active services (benchmark, kill, etc.)
    for instance in queue.get_active_services():
        if instance.state == "running":
            # run benchmarks
            # kill service
            queue.mark_completed(instance)
            # After marking completed, loop will IMMEDIATELY try to launch next!
```

---

## Improvement 3: Service Queue State Machine

**Priority:** Medium

**Description:**
Currently, the service states are tracked but not fully leveraged. Create a proper state machine with callbacks.

**States:**
- `pending` → `starting` → `ready` → `running` → `stopping` → `stopped`

**Callbacks:**
- `on_ready(service)` - Called when service becomes ready
- `on_benchmark_complete(service, results)` - Called when benchmarks finish
- `on_stop(service)` - Called when service is stopped

**Files to Modify:**
- `/root/AUTO_TEST/src/service_queue.py` - Add callback support
- `/root/AUTO_TEST/src/service_manager.py` - Add state transition hooks

---

## Improvement 4: Real-time Progress Tracking

**Priority:** Low

**Description:**
Add a progress bar or real-time status display showing:
- Number of services pending/active/completed
- Current benchmark running
- Estimated time remaining

**Files to Modify:**
- Add new `/root/AUTO_TEST/src/progress.py`
- Modify test scripts to use progress tracking

---

## Improvement 5: Result Streaming & Partial Report Generation

**Priority:** Low

**Description:**
Instead of waiting for all benchmarks to complete before generating reports:
- Stream results as they come in
- Generate partial reports periodically
- Allow early termination with partial results

**Files to Modify:**
- (Future Phase 4/5 files)

---

## Implementation Order

1. **First:** Improvement 2 (Launch next service immediately) - Quick win, no major architecture changes
2. **Second:** Improvement 1 (Parallel benchmarking) - More involved, but big performance gain
3. **Then:** Improvements 3-5 as needed

---

## Expected Performance Gain

With both Improvement 1 and 2 implemented:
- **Best case:** ~2x speedup with `max_existed_service_num=2`
- **Typical case:** ~1.5-1.8x speedup
- GPU utilization will be much higher with less idle time
