# Benchmark Results Report

**Generated:** 2026-04-09 13:29:12

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
| **Input Length** | 64 |
| **Output Length** | 32 |
| **Max Concurrency** | 16 |
| **Image Size/Count** | 448x448/1 |

![Group 0 Plot](group_0_results.png)

#### Results

| idx | Throughput (tok/s) | TTFT (ms) | TPOT (ms) |
| --- | --- | --- | --- |
| 0 | 4073.7 | 0.0 | 38.5 |
| 1 | 4414.1 | 0.0 | 35.5 |

#### Configuration Details

| idx | Env Opt | Server Args Opt | Additional Options |
| --- | --- | --- | --- |
| 0 | (none) | (none) | --context-length 262144 --reasoning-parser qwen3 |
| 1 | (none) | --decode-attention-backend flashinfer | --context-length 262144 --reasoning-parser qwen3 |

### Group 1

| Attribute | Value |
|-----------|-------|
| **Model** | Qwen3.5-9B |
| **Deploy Method** | tp1 |
| **Template ID** | 1 |
| **Input Length** | 64 |
| **Output Length** | 32 |
| **Max Concurrency** | 32 |
| **Image Size/Count** | 448x448/1 |

![Group 1 Plot](group_1_results.png)

#### Results

| idx | Throughput (tok/s) | TTFT (ms) | TPOT (ms) |
| --- | --- | --- | --- |
| 0 | 4713.1 | 0.0 | 66.6 |
| 1 | 4888.6 | 0.0 | 64.3 |

#### Configuration Details

| idx | Env Opt | Server Args Opt | Additional Options |
| --- | --- | --- | --- |
| 0 | (none) | (none) | --context-length 262144 --reasoning-parser qwen3 |
| 1 | (none) | --decode-attention-backend flashinfer | --context-length 262144 --reasoning-parser qwen3 |

### Group 2

| Attribute | Value |
|-----------|-------|
| **Model** | Qwen3.5-9B |
| **Deploy Method** | tp1 |
| **Template ID** | 1 |
| **Input Length** | 64 |
| **Output Length** | 32 |
| **Max Concurrency** | 64 |
| **Image Size/Count** | 448x448/1 |

![Group 2 Plot](group_2_results.png)

#### Results

| idx | Throughput (tok/s) | TTFT (ms) | TPOT (ms) |
| --- | --- | --- | --- |
| 0 | 5196.8 | 0.0 | 120.9 |
| 1 | 5300.9 | 0.0 | 118.5 |

#### Configuration Details

| idx | Env Opt | Server Args Opt | Additional Options |
| --- | --- | --- | --- |
| 0 | (none) | (none) | --context-length 262144 --reasoning-parser qwen3 |
| 1 | (none) | --decode-attention-backend flashinfer | --context-length 262144 --reasoning-parser qwen3 |

### Group 3

| Attribute | Value |
|-----------|-------|
| **Model** | Qwen3.5-9B |
| **Deploy Method** | tp1 |
| **Template ID** | 1 |
| **Input Length** | 128 |
| **Output Length** | 64 |
| **Max Concurrency** | 8 |
| **Image Size/Count** | 1280x1280/1 |

![Group 3 Plot](group_3_results.png)

#### Results

| idx | Throughput (tok/s) | TTFT (ms) | TPOT (ms) |
| --- | --- | --- | --- |
| 0 | 4326.3 | 22.2 | 52.6 |
| 1 | 4802.3 | 0.0 | 47.7 |

#### Configuration Details

| idx | Env Opt | Server Args Opt | Additional Options |
| --- | --- | --- | --- |
| 0 | (none) | (none) | --context-length 262144 --reasoning-parser qwen3 |
| 1 | SGLANG_VISION_ATTN_FP8=1 | (none) | --context-length 262144 --reasoning-parser qwen3 |

### Group 4

| Attribute | Value |
|-----------|-------|
| **Model** | Qwen3.5-9B |
| **Deploy Method** | tp1 |
| **Template ID** | 1 |
| **Input Length** | 128 |
| **Output Length** | 64 |
| **Max Concurrency** | 16 |
| **Image Size/Count** | 1280x1280/1 |

![Group 4 Plot](group_4_results.png)

#### Results

| idx | Throughput (tok/s) | TTFT (ms) | TPOT (ms) |
| --- | --- | --- | --- |
| 0 | 4775.7 | 0.0 | 96.1 |
| 1 | 5287.8 | 0.0 | 86.7 |

#### Configuration Details

| idx | Env Opt | Server Args Opt | Additional Options |
| --- | --- | --- | --- |
| 0 | (none) | (none) | --context-length 262144 --reasoning-parser qwen3 |
| 1 | SGLANG_VISION_ATTN_FP8=1 | (none) | --context-length 262144 --reasoning-parser qwen3 |
