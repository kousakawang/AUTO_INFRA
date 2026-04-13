#launch server
SGLANG_VLM_CACHE_SIZE_MB=0 CUDA_VISIBLE_DEVICES=0 python3 -m sglang.launch_server --model-path /data01/models/Qwen3.5-9B --host 127.0.0.1 --port 8080 --mem-fraction-static 0.7 --cuda-graph-max-bs 128 --tensor-parallel-size 1 --mm-attention-backend fa3 --cuda-graph-bs 128 120 112 104 96 88 80 72 64 56 48 40 32 24 16 8 4 2 1 --disable-radix-cache --context-length 262144 --reasoning-parser qwen3
#benchmark
python3 -m sglang.bench_serving --backend sglang-oai-chat --dataset-name image --num-prompts 120 --apply-chat-template --random-output-len 64 --random-input-len 32 --image-resolution 448x448 --image-format jpeg --image-count 1 --image-content blank --random-range-ratio 1 --max-concurrency 20 --host=127.0.0.1 --port=8080

#lauch server
SGLANG_VLM_CACHE_SIZE_MB=256 CUDA_VISIBLE_DEVICES=1 python3 -m sglang.launch_server --model-path /data01/models/Qwen3.5-9B --host 127.0.0.1 --port 8070 --mem-fraction-static 0.7 --cuda-graph-max-bs 128 --tensor-parallel-size 1 --mm-attention-backend fa3 --cuda-graph-bs 128 120 112 104 96 88 80 72 64 56 48 40 32 24 16 8 4 2 1 --disable-radix-cache --context-length 262144 --reasoning-parser qwen3
#benchmark
python3 -m sglang.bench_serving --backend sglang-oai-chat --dataset-name image --num-prompts 120 --apply-chat-template --random-output-len 64 --random-input-len 32 --image-resolution 448x448 --image-format jpeg --image-count 1 --image-content blank --random-range-ratio 1 --max-concurrency 20 --host=127.0.0.1 --port=8070

#lauch server
SGLANG_VLM_CACHE_SIZE_MB=512 CUDA_VISIBLE_DEVICES=2 python3 -m sglang.launch_server --model-path /data01/models/Qwen3.5-9B --host 127.0.0.1 --port 8060 --mem-fraction-static 0.7 --cuda-graph-max-bs 128 --tensor-parallel-size 1 --mm-attention-backend fa3 --cuda-graph-bs 128 120 112 104 96 88 80 72 64 56 48 40 32 24 16 8 4 2 1 --disable-radix-cache --context-length 262144 --reasoning-parser qwen3
#benchmark
python3 -m sglang.bench_serving --backend sglang-oai-chat --dataset-name image --num-prompts 120 --apply-chat-template --random-output-len 64 --random-input-len 32 --image-resolution 448x448 --image-format jpeg --image-count 1 --image-content blank --random-range-ratio 1 --max-concurrency 20 --host=127.0.0.1 --port=8060
python3 -m sglang.bench_serving --backend sglang-oai-chat --dataset-name image --num-prompts 120 --apply-chat-template --random-output-len 128 --random-input-len 128 --image-resolution 448x448 --image-format jpeg --image-count 1 --image-content blank --random-range-ratio 1 --max-concurrency 20 --host=127.0.0.1 --port=8060