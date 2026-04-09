# Benchmark Results Report

**Generated:** 2026-04-08 14:34:13

## SLO Criteria

- No SLO thresholds applied
- Data Policy: remove_min_max

## Group Results

### Group 0

| Attribute | Value |
|-----------|-------|
| **Model** | Qwen3.5-9B |
| **Deploy Method** | tp1 |
| **Template ID** | 1 |
| **Input Length** | 32 |
| **Output Length** | 64 |
| **Max Concurrency** | 20 |
| **Image Size/Count** | 448x448/1 |

![Group 0 Plot](group_0_results.png)

#### Results

| idx | Throughput (tok/s) | TTFT (ms) | TPOT (ms) |
| --- | --- | --- | --- |
| 0 | 3210.0 | 0.0 | 24.2 |
| 1 | 3210.0 | 0.0 | 24.2 |

#### Configuration Details

| idx | Env Opt | Server Args Opt | Additional Options |
| --- | --- | --- | --- |
| 0 | (none) | (none) | SGLANG_VLM_CACHE_SIZE_MB=0 --context-length 262144 --reasoning-parser qwen3 |
| 1 | (none) | (none) | SGLANG_VLM_CACHE_SIZE_MB=512 --context-length 262144 --reasoning-parser qwen3 |

### Group 1

| Attribute | Value |
|-----------|-------|
| **Model** | Qwen3.5-9B |
| **Deploy Method** | tp1 |
| **Template ID** | 1 |
| **Input Length** | 128 |
| **Output Length** | 128 |
| **Max Concurrency** | 20 |
| **Image Size/Count** | 448x448/1 |

![Group 1 Plot](group_1_results.png)

#### Results

| idx | Throughput (tok/s) | TTFT (ms) | TPOT (ms) |
| --- | --- | --- | --- |
| 0 | 3210.0 | 0.0 | 24.2 |

#### Configuration Details

| idx | Env Opt | Server Args Opt | Additional Options |
| --- | --- | --- | --- |
| 0 | (none) | (none) | SGLANG_VLM_CACHE_SIZE_MB=512 --context-length 262144 --reasoning-parser qwen3 |

### Group 2

| Attribute | Value |
|-----------|-------|
| **Model** | Qwen3.5-9B |
| **Deploy Method** | tp2 |
| **Template ID** | 1 |
| **Input Length** | 32 |
| **Output Length** | 64 |
| **Max Concurrency** | 20 |
| **Image Size/Count** | 448x448/1 |

![Group 2 Plot](group_2_results.png)

#### Results

| idx | Throughput (tok/s) | TTFT (ms) | TPOT (ms) |
| --- | --- | --- | --- |
| 0 | 1605.0 (per-device) | 0.0 | 24.2 |

#### Configuration Details

| idx | Env Opt | Server Args Opt | Additional Options |
| --- | --- | --- | --- |
| 0 | (none) | (none) | SGLANG_VLM_CACHE_SIZE_MB=256 --cuda-graph-bs 64 56 48 40 32 24 16 8 4 2 1 --context-length 262144 --reasoning-parser qwen3 |
