@echo off
cd /d C:\Users\user\Documents\kimi\workspace\cc-eval\harness
C:\Users\user\Documents\kimi\workspace\cc-eval\.venv\Scripts\python.exe gguf_score_k.py --gguf ..\models\Llama-3.1-8B-GGUF\Meta-Llama-3.1-8B-Instruct-Q8_0.gguf --data data\cceval_kno.jsonl --out ..\results\harness\Llama-3.1-8B-q8_0\kno.json --budget 60000 > l8b_kno.log 2>&1
