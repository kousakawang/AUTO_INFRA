# Benchmark Results Report

**Generated:** 2026-04-10 07:04:18

## SLO Criteria

- No SLO thresholds applied
- Data Policy: remove_min_max

## Group Results

### Group 0

| Attribute | Value |
|-----------|-------|
| **Model** | Qwen3.5-9B |
| **Deploy Method** | tp1 |
| **Template ID** | 2 |
| **Input Length** | 32 |
| **Output Length** | 64 |
| **Max Concurrency** | 3 |
| **Image Size/Count** | 448x448/1 |

![Group 0 Plot](group_0_results.png)

#### Results

| idx | Throughput (tok/s) | TTFT (ms) | TPOT (ms) |
| --- | --- | --- | --- |
| 0 | 1474.9 | 0.0 | 9.8 |
| 1 | 1488.0 | 0.0 | 9.7 |

#### Configuration Details

| idx | Env Opt | Server Args Opt | Additional Options |
| --- | --- | --- | --- |
| 0 | (none) | (none) | --context-length 262144 --reasoning-parser qwen3 |
| 1 | (none) | (none) | --context-length 262144 --reasoning-parser qwen3 |

### Group 1

| Attribute | Value |
|-----------|-------|
| **Model** | Qwen3.5-9B |
| **Deploy Method** | tp1 |
| **Template ID** | 2 |
| **Input Length** | 64 |
| **Output Length** | 128 |
| **Max Concurrency** | 3 |
| **Image Size/Count** | 448x448/1 |

![Group 1 Plot](group_1_results.png)

#### Results

| idx | Throughput (tok/s) | TTFT (ms) | TPOT (ms) |
| --- | --- | --- | --- |
| 0 | 1080.1 | 0.0 | 8.8 |
| 1 | 1088.8 | 38.6 | 8.2 |

#### Configuration Details

| idx | Env Opt | Server Args Opt | Additional Options |
| --- | --- | --- | --- |
| 0 | (none) | (none) | --context-length 262144 --reasoning-parser qwen3 |
| 1 | (none) | (none) | --context-length 262144 --reasoning-parser qwen3 |
