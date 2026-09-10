@echo off
cd /d C:\Users\Donal\Documents\kimi\workspace\cc-eval\harness
C:\Users\Donal\Documents\kimi\workspace\cc-eval\.venv\Scripts\python.exe gguf_score_k.py --gguf ..\models\Qwen2.5-7B-GGUF\qwen2.5-7b-instruct-q8_0-00001-of-00003.gguf --data data\cceval_kno.jsonl --out ..\results\harness\Qwen2.5-7B-q8_0\kno.json --budget 43200 > kno_7b_run4.log 2>&1
