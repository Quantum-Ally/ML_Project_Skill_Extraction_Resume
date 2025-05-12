
# run uvicorn main:app --reload
#!/usr/bin/env python3
import os
import sys
import json
import numpy as np

from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from typing import List, Optional, Dict
from pydantic import BaseModel
from sklearn.metrics import silhouette_samples

# Ensure parent directory is on the path to import project modules
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(BASE_DIR)
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

import searches
from kmeans import SkillsClusterer

# Paths
DATA_PATH = os.path.join(PARENT_DIR, 'results.json')
SEARCH_RESULTS_DIR = os.path.join(PARENT_DIR, 'results')
SEARCH_RESULTS_FILE = os.path.join(SEARCH_RESULTS_DIR, 'search_results.json')

# Clustering output files
CLUSTER_RESULTS_DIR = SEARCH_RESULTS_DIR
CLUSTER_ASSIGNMENTS_FILE = os.path.join(CLUSTER_RESULTS_DIR, 'cluster_assignments.json')
CLUSTER_ANALYSIS_FILE = os.path.join(CLUSTER_RESULTS_DIR, 'cluster_analysis.json')
FILTERED_OUTPUT_FILE = os.path.join(CLUSTER_RESULTS_DIR, 'kmeans_cluster_filtered.json')

# FastAPI setup
app = FastAPI()
PDF_DIR = os.path.join(PARENT_DIR, 'data')
if os.path.isdir(PDF_DIR):
    app.mount('/pdfs', StaticFiles(directory=PDF_DIR), name='pdfs')
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class SelectionRequest(BaseModel):
    counts: Dict[int, int]

# CV endpoints
@app.get('/cvs', response_model=List[str])
def get_all_ids():
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        cvs = json.load(f)
    return [e.get('id') for e in cvs]

@app.get('/cvs/{cv_id}')
def download_cv(cv_id: str):
    p1 = os.path.join(PDF_DIR, f"{cv_id}.pdf")
    p2 = os.path.join(PARENT_DIR, f"{cv_id}.pdf")
    for path in (p1, p2):
        if os.path.isfile(path):
            return FileResponse(path, media_type='application/pdf', filename=os.path.basename(path))
    raise HTTPException(status_code=404, detail='CV PDF not found')

# Search endpoints
@app.get('/search', response_model=List[dict])
def search(
    algo: str = Query(..., pattern='^(bfs|dfs|hill)$'),
    keyword: str = Query(...),
    count: int = Query(..., ge=1)
):
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        cvs = json.load(f)
    subset = [e for e in cvs if keyword.lower() in (e.get('summary') or '').lower()
              or any(keyword.lower() in s.lower() for s in (e.get('skills') or []))]
    funcs = {'bfs': searches.bfs, 'dfs': searches.dfs, 'hill': searches.hill_climbing}
    func = funcs.get(algo)
    if not func:
        raise HTTPException(status_code=400, detail='Invalid algorithm')
    raw = func(subset, keyword)[:count]
    results = [e for e in raw if any(os.path.isfile(os.path.join(d, f"{e['id']}.pdf")) for d in (PDF_DIR, PARENT_DIR))]
    final = results or raw
    os.makedirs(SEARCH_RESULTS_DIR, exist_ok=True)
    with open(SEARCH_RESULTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(final, f, ensure_ascii=False, indent=2)
    return final

@app.get('/search/total', response_model=int)
def total_search_results():
    if not os.path.exists(SEARCH_RESULTS_FILE):
        return 0
    with open(SEARCH_RESULTS_FILE, 'r', encoding='utf-8') as f:
        return len(json.load(f))

# Cluster endpoints
@app.post('/cluster/run')
def run_clustering(
    algorithm: str = Query('agglomerative', regex='^(kmeans|agglomerative|dbscan)$'),
    n_clusters: Optional[int] = Query(None, ge=1),
    min_skill_freq: int = Query(2, ge=1),
    max_df: float = Query(0.7),
    dim_reduction: Optional[str] = Query('svd', regex='^(svd|None)$'),
    dim_components: int = Query(50, ge=1, alias='dim_reduction_components'),
    dbscan_eps: float = Query(0.5, gt=0.0),
    dbscan_min_samples: int = Query(5, ge=1),
    random_state: int = Query(42)
):
    if not os.path.exists(SEARCH_RESULTS_FILE):
        raise HTTPException(status_code=400, detail='No search results to cluster')
    with open(SEARCH_RESULTS_FILE, 'r', encoding='utf-8') as f:
        profiles = json.load(f)
    clusterer = SkillsClusterer(
        n_clusters=n_clusters,
        algorithm=algorithm,
        min_skill_freq=min_skill_freq,
        max_df=max_df,
        dim_reduction=None if dim_reduction == 'None' else dim_reduction,
        dim_components=dim_components,
        random_state=random_state,
        dbscan_eps=dbscan_eps,
        dbscan_min_samples=dbscan_min_samples
    )
    clusterer.fit(profiles)
    clusterer.save(CLUSTER_RESULTS_DIR)
    with open(CLUSTER_ANALYSIS_FILE, 'r', encoding='utf-8') as f:
        return JSONResponse(content=json.load(f))

@app.get('/cluster/results')
def get_cluster_results():
    if not os.path.exists(CLUSTER_ASSIGNMENTS_FILE):
        raise HTTPException(status_code=404, detail='No clustering assignments')
    with open(CLUSTER_ASSIGNMENTS_FILE, 'r', encoding='utf-8') as f:
        return JSONResponse(content=json.load(f))

@app.get('/cluster/summary')
def get_cluster_summary():
    if not os.path.exists(CLUSTER_ANALYSIS_FILE):
        raise HTTPException(status_code=404, detail='No clustering analysis')
    with open(CLUSTER_ANALYSIS_FILE, 'r', encoding='utf-8') as f:
        analysis = json.load(f)
    return JSONResponse(content={
        'algorithm': analysis['algorithm'],
        'n_clusters': analysis['n_clusters'],
        'cluster_sizes': analysis['cluster_sizes'],
        'top_skills': {cid: skills[:3] for cid, skills in analysis['top_skills'].items()}
    })

@app.post('/cluster/select')
def select_top_candidates(selection: SelectionRequest = Body(...)):
    if not os.path.exists(SEARCH_RESULTS_FILE):
        raise HTTPException(status_code=404, detail='No search results')
    with open(SEARCH_RESULTS_FILE, 'r', encoding='utf-8') as f:
        profiles = json.load(f)
    # load cluster assignments & analysis
    with open(CLUSTER_ASSIGNMENTS_FILE, 'r', encoding='utf-8') as f:
        assignments = json.load(f)
    with open(CLUSTER_ANALYSIS_FILE, 'r', encoding='utf-8') as f:
        analysis = json.load(f)
    clusterer = SkillsClusterer(
        n_clusters=None,
        algorithm='agglomerative',
        min_skill_freq=2,
        max_df=0.7,
        dim_reduction=None,
        dim_components=50,
        random_state=42,
        dbscan_eps=0.5,
        dbscan_min_samples=5
    )
    clusterer.fit(profiles)
    X = clusterer.features
    labels = clusterer.cluster_model.labels_
    sil = silhouette_samples(X, labels) if len(set(labels)) > 1 else [0] * len(labels)
    centroids = {lbl: np.mean([X[i] for i, l in enumerate(labels) if l == lbl], axis=0) for lbl in set(labels)}
    top_skills = {lbl: {s for s, _ in clusterer.cluster_skill_importances[lbl][:10]} for lbl in set(labels)}
    filtered: Dict[int, List[str]] = {}
    for lbl, cnt in selection.counts.items():
        members = []
        for i, pid in enumerate(clusterer.profile_ids):
            if labels[i] != lbl:
                continue
            dist = float(np.linalg.norm(X[i] - centroids[lbl]))
            match = len([s for s in profiles[i].get('skills', []) if s in top_skills[lbl]])
            members.append((pid, sil[i], -dist, match))
        members.sort(key=lambda x: (x[1], x[2], x[3]), reverse=True)
        filtered[lbl] = [pid for pid, _, _, _ in members[:max(0, min(cnt, len(members)))]]
    os.makedirs(CLUSTER_RESULTS_DIR, exist_ok=True)
    with open(FILTERED_OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(filtered, f, indent=2)
    return JSONResponse(content=filtered)

# Run
# uvicorn main:app --reload