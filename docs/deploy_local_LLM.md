# Documentation for Deploying Local Large Language Models (LLMs) with ProvPlug

## Prerequisites
- Linux
- CUDA 12.8
- Python 3.12
- PyTorch 2.2+
- vLLM 0.6.3+
- Enough GPUs for handling the used LLM: compute capability should be 7.0 or higher (e.g., V100, T4, RTX20xx, A100, L4, H100, etc.)

Other environments may also work but are not tested.

## Installation

1. Create and activate a virtual environment with Python 3.12
```
uv venv --python 3.12 --seed
source .venv/bin/activate
```
Note that PyTorch installed via conda will statically link NCCL library, which can cause issues when vLLM tries to use NCCL.


2. Install vLLM with automatic torch backend
```
uv pip install vllm --torch-backend=auto
```


## Start Qwen3-30B-A3B-Instruct-2507 Server

1. Run the same model (i.e., Qwen3-30B-A3B-Instruct-2507) as our work.
```
CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7 vllm serve Qwen/Qwen3-30B-A3B-Instruct-2507   --trust-remote-code   --tensor-parallel-size 4   --max-model-len 160000   --gpu-memory-utilization 0.92   --max-num-seqs 32   --max-num-batched-tokens 65536   --port 8000
```