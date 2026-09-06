# 按厂商名从 providers.json 读取配置并调用 run_eval.py
import json, subprocess, sys

vendor = sys.argv[1]
workers = sys.argv[2] if len(sys.argv) > 2 else '10'
budget = sys.argv[3] if len(sys.argv) > 3 else '250'
rpm = sys.argv[4] if len(sys.argv) > 4 else '0'

prov = json.load(open('runner/providers.json', encoding='utf-8'))[vendor]
base = prov['base']
if vendor == 'gemini':
    base = base.rstrip('/') + '/chat/completions'

sys.exit(subprocess.call([
    sys.executable, 'runner/run_eval.py',
    '--name', vendor, '--model', prov['chosen'],
    '--base', base, '--key', prov['key'],
    '--workers', workers, '--budget', budget, '--rpm', rpm,
]))
