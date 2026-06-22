#!/usr/bin/env python3
"""Inventory and classify markdown files for doc reorganization.
Outputs: docs/inventory_suggestion.csv
"""
import os
import re
import csv
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "inventory_suggestion.csv"
KEYWORDS_BUSINESS = [
    "business", "stakeholder", "persona", "brd", "kpi", "roi", "use case", "use-case", "goals", "vision", "stakeholders"
]
KEYWORDS_TECH = [
    "architecture", "api", "ragg","rag", "agent", "llm", "postgres", "redis", "milvus", "neo4j", "docker", "k8s", "kubernetes", "puml", "plantuml", "schema", "database", "service", "technical", "frd"
]

FRONTMATTER_RE = re.compile(r"^---\s*(.*?)\s*---\s*", re.S)


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def read_frontmatter(text: str) -> dict:
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}
    body = m.group(1)
    # naive YAML key: value parse for top-level keys
    data = {}
    for line in body.splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            data[k.strip()] = v.strip().strip('"').strip("'")
    return data


def classify(content: str, front: dict):
    text = (" ".join([front.get('title',''), front.get('tags','')]) + " " + content).lower()
    score_b = sum(text.count(k) for k in KEYWORDS_BUSINESS)
    score_t = sum(text.count(k) for k in KEYWORDS_TECH)
    if score_b and not score_t:
        return 'business'
    if score_t and not score_b:
        return 'technical'
    if score_b and score_t:
        return 'both'
    # fallback heuristics by filename
    return 'technical' if any(k in content.lower() for k in KEYWORDS_TECH) else 'business'


def suggested_path(original: str, dtype: str) -> str:
    fname = os.path.basename(original)
    if dtype == 'business':
        return os.path.join('docs', 'business', fname)
    if dtype == 'technical':
        # keep services/agents under technical subfolders
        if original.startswith('agents/'):
            return os.path.join('docs', 'technical', 'agents', fname)
        if original.startswith('services/'):
            return os.path.join('docs', 'technical', 'services', fname)
        return os.path.join('docs', 'technical', fname)
    if dtype == 'both':
        return os.path.join('docs', 'both', fname)
    return os.path.join('docs', 'archive', fname)


def main():
    rows = []
    md_files = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        # skip git, .venv, node_modules
        if '.git' in dirpath or 'node_modules' in dirpath:
            continue
        for fn in filenames:
            if fn.lower().endswith('.md'):
                p = Path(dirpath) / fn
                # skip files in docs/inventory output
                if str(p).endswith('inventory_suggestion.csv'):
                    continue
                md_files.append(p)

    for p in sorted(md_files):
        try:
            text = p.read_text(encoding='utf-8')
        except Exception:
            text = ''
        front = read_frontmatter(text)
        dtype = classify(text, front)
        dest = suggested_path(str(p.relative_to(ROOT)).replace('\\','/'), dtype)
        row = {
            'original_path': str(p.relative_to(ROOT)).replace('\\','/'),
            'sha256': sha256_of(p),
            'has_frontmatter': 'yes' if front else 'no',
            'title': front.get('title', ''),
            'owner': front.get('owner',''),
            'suggested_type': dtype,
            'suggested_destination': dest
        }
        rows.append(row)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['original_path','sha256','has_frontmatter','title','owner','suggested_type','suggested_destination'])
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

    print(f"Scanned {len(rows)} markdown files. Suggestions written to: {OUT}")


if __name__ == '__main__':
    main()
