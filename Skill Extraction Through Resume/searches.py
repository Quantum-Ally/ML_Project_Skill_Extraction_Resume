#!/usr/bin/env python3
import json
import os


def load_data(path):
    """
    Load JSON data from the given path.
    """
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_search_results(results, out_path):
    """
    Save search results as indented JSON to out_path.
    """
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)


def _parse_keywords(keyword_str):
    """
    Split comma-separated keywords and return a list of lowercase keywords.
    """
    return [kw.strip().lower() for kw in keyword_str.split(',') if kw.strip()]


def bfs(data, keyword_str):
    """
    Breadth-first search: returns items containing any of the keywords.
    """
    keywords = _parse_keywords(keyword_str)
    results = []
    queue = data[:]
    while queue:
        item = queue.pop(0)
        text = json.dumps(item).lower()
        if any(kw in text for kw in keywords):
            results.append(item)
    return results


def dfs(data, keyword_str):
    """
    Depth-first search: returns items containing any of the keywords.
    """
    keywords = _parse_keywords(keyword_str)
    results = []
    stack = data[:]
    while stack:
        item = stack.pop()
        text = json.dumps(item).lower()
        if any(kw in text for kw in keywords):
            results.append(item)
    return results


def hill_climbing(data, keyword_str):
    """
    Hill-climbing search: scores items by total keyword occurrences and returns sorted list.
    """
    keywords = _parse_keywords(keyword_str)
    scored = []
    for item in data:
        text = json.dumps(item).lower()
        # sum occurrences of all keywords
        score = sum(text.count(kw) for kw in keywords)
        if score > 0:
            scored.append((score, item))
    # sort descending by score
    scored.sort(key=lambda x: x[0], reverse=True)
    return [item for score, item in scored]

# Note: load_data and save_search_results remain for external use
