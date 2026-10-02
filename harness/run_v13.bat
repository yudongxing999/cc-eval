@echo off
cd /d %USERPROFILE%\Documents\kimi\workspace\cc-eval\harness
set PY=%USERPROFILE%\Documents\kimi\workspace\cc-eval\.venv\Scripts\python.exe
set M7=..\models\Qwen2.5-7B-GGUF\qwen2.5-7b-instruct-q8_0-00001-of-00003.gguf
set M8=..\models\Llama-3.1-8B-GGUF\Meta-Llama-3.1-8B-Instruct-Q8_0.gguf
set O7=..\results\harness\Qwen2.5-7B-q8_0
set O8=..\results\harness\Llama-3.1-8B-q8_0
%PY% gguf_score_k.py --gguf %M7% --data data\cceval_kno_v13b.jsonl --out %O7%\kno_v13b.json --budget 60000 > v13_run.log 2>&1
%PY% gguf_score_k.py --gguf %M8% --data data\cceval_kno_v13b.jsonl --out %O8%\kno_v13b.json --budget 60000 >> v13_run.log 2>&1
