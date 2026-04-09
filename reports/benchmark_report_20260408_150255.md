# Benchmark Results Report

**Generated:** 2026-04-08 15:02:56

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
| 0 | 4065.7 | 829.3 | 10.5 |
| 1 | 5233.2 | 475.0 | 10.9 |

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
| 0 | 4490.6 | 818.2 | 9.9 |

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
| 0 | 3091.9 (per-device) | 629.3 | 5.6 |

#### Configuration Details

| idx | Env Opt | Server Args Opt | Additional Options |
| --- | --- | --- | --- |
| 0 | (none) | (none) | SGLANG_VLM_CACHE_SIZE_MB=256 --cuda-graph-bs 64 56 48 40 32 24 16 8 4 2 1 --context-length 262144 --reasoning-parser qwen3 |
