#!/bin/bash

# 指定使用 GPU 0


# 启动 API 服务器
CUDA_VISIBLE_DEVICES=5 python -m vllm.entrypoints.openai.api_server --model RebuttalAgent --host 0.0.0.0 --port 8001 --trust_remote_code
