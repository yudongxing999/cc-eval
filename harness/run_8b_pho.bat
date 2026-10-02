@echo off
cd /d C:\Users\user\Documents\kimi\workspace\cc-eval\harness
set PY=C:\Users\user\Documents\kimi\workspace\cc-eval\.venv\Scripts\python.exe
set M=..\models\Llama-3.1-8B-GGUF\Meta-Llama-3.1-8B-Instruct-Q8_0.gguf
set O=..\results\harness\Llama-3.1-8B-q8_0
%PY% gguf_score_k.py --gguf %M% --data data\cceval_pho_poly.jsonl  --out %O%\pho_poly.json  --budget 43200 >  l8b_pho.log 2>&1
%PY% gguf_score_k.py --gguf %M% --data data\cceval_pho_legal.jsonl --out %O%\pho_legal.json --budget 43200 >> l8b_pho.log 2>&1
%PY% gguf_score_k.py --gguf %M% --data data\cceval_pho_level.jsonl --out %O%\pho_level.json --budget 43200 >> l8b_pho.log 2>&1
