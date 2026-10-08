#!/usr/bin/env bash
# usage: ask.sh <biz|dev> <step-name> <allowed-tools> <prompt>
# Runs one non-interactive Claude Code step in that person's clone, with only their plugin loaded.
set -uo pipefail
D=$(cd "$(dirname "$0")" && pwd)
who=$1; step=$2; tools=$3; prompt=$4
plugin=superbiz; [ "$who" = dev ] && plugin=superdev
cd "$D/$who"
claude -p "$prompt" --plugin-dir "./plugins/$plugin" --permission-mode acceptEdits \
  --allowedTools "$tools" --output-format json < /dev/null > "$D/log/$step.json" 2> "$D/log/$step.err"
python3 - "$D/log/$step.json" "$step" <<'PY'
import json, sys
p, step = sys.argv[1:]
j = json.load(open(p))
open(p.replace('.json', '.md'), 'w').write(j.get('result', '').rstrip() + '\n')
with open(p.rsplit('/', 1)[0] + '/costs.tsv', 'a') as f:
    f.write("%s\t%d\t%.4f\t%s\t%s\n" % (step, j.get('duration_ms', 0) // 1000, j.get('total_cost_usd', 0),
                                       j.get('num_turns'), ','.join(j.get('modelUsage', {}))))
print("[%s] %ds $%.2f turns=%s error=%s" % (step, j.get('duration_ms', 0) // 1000, j.get('total_cost_usd', 0),
                                           j.get('num_turns'), j.get('is_error')))
print(j.get('result', '')[-1800:])
PY
