#!/usr/bin/env python3
"""Generate a safe shell script to move files based on docs/inventory_suggestion.csv
Only generates git mv commands for files where original exists and destination does not.
Outputs: tools/apply_moves.sh
"""
import csv
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
CSV = ROOT / 'docs' / 'inventory_suggestion.csv'
OUT = ROOT / 'tools' / 'apply_moves.sh'

commands = ["#!/usr/bin/env bash", "set -euo pipefail", "echo 'Starting apply_moves...'\n"]

with CSV.open('r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for r in reader:
        orig = ROOT / r['original_path']
        dest = ROOT / r['suggested_destination']
        # normalize
        if not orig.exists():
            # skip missing originals
            commands.append(f"echo 'SKIP: original not found: {r['original_path']}'")
            continue
        if dest.exists():
            commands.append(f"echo 'SKIP: destination already exists: {dest.relative_to(ROOT)}'")
            continue
        # ensure dest dir
        commands.append(f"mkdir -p \"{dest.parent}\"")
        # git mv
        commands.append(f"git mv \"{orig.relative_to(ROOT)}\" \"{dest.relative_to(ROOT)}\"")

commands.append("echo 'Done apply_moves'")
OUT.write_text('\n'.join(commands))
OUT.chmod(0o755)
print(f"Wrote move script: {OUT}")
