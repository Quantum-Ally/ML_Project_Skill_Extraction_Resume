#!/usr/bin/env python3
import re
import os
import sys
import json
from typing import Dict, List, Any

try:
    import fitz  # PyMuPDF
except ModuleNotFoundError:
    print(
        "Error: PyMuPDF not installed. Please run: pip uninstall fitz && pip install PyMuPDF",
        file=sys.stderr
    )
    sys.exit(1)

# === Configuration ===
INPUT_DIR = 'data'
OUTPUT_JSON = 'results.json'
SECTION_KEYWORD = 'skills'
WINDOW_SIZE = 500
DELIM_REGEX = re.compile(r"[;,\u2022\*\n]+")

class CVParser:
    """
    Parser to extract meaningful skills and capture full CV text as summary.
    """
    DATE_REGEX = re.compile(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b\d{4}\b")

    def extract_skills(self, text: str) -> List[str]:
        # Locate 'skills' section
        low = text.lower()
        idx = low.find(SECTION_KEYWORD)
        if idx == -1:
            return []
        start = idx + len(SECTION_KEYWORD)
        snippet = text[start:start + WINDOW_SIZE]
        # trim at blank line
        if '\n\n' in snippet:
            snippet = snippet.split('\n\n', 1)[0]
        # split and clean
        raw_items = [item.strip().rstrip(':') for item in DELIM_REGEX.split(snippet) if item.strip()]
        seen = set()
        skills = []
        for s in raw_items:
            # skip dates or numeric entries
            if self.DATE_REGEX.search(s):
                continue
            # skip if same as section keyword or too verbose
            words = s.split()
            if s.lower() == SECTION_KEYWORD or len(words) > 4:
                continue
            # skip full sentences (ending with period) or containing verbs
            if s.endswith('.') or re.search(r"\b(is|are|manage|led|develop|experience)\b", s, re.IGNORECASE):
                continue
            key = s.lower()
            if key not in seen:
                seen.add(key)
                skills.append(s)
        return skills

    def parse_file(self, path: str) -> Dict[str, Any]:
        # extract full text
        with fitz.open(path) as doc:
            pages = [page.get_text() for page in doc]
        full_text = '\n'.join(pages)
        skills = self.extract_skills(full_text)
        return {'id': os.path.splitext(os.path.basename(path))[0],
                'skills': skills,
                'summary': full_text}

if __name__ == '__main__':
    parser = CVParser()
    results = []
    for fname in sorted(os.listdir(INPUT_DIR)):
        if not fname.lower().endswith('.pdf'):
            continue
        path = os.path.join(INPUT_DIR, fname)
        try:
            entry = parser.parse_file(path)
        except Exception as e:
            print(f"Warning: failed to parse {fname}: {e}", file=sys.stderr)
            entry = {'id': os.path.splitext(fname)[0], 'skills': [], 'summary': ''}
        results.append(entry)
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"Wrote {len(results)} records to {OUTPUT_JSON}")