#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced Clustering for Professional Skills Data (no whitelist + blacklist)

This script filters out overly-common tokens via TF-IDF's max_df and a
custom blacklist of junk skills, so only “real” skills remain. It then
performs clustering (KMeans, Agglomerative, or DBSCAN) and saves results.

Author: Claude (enhanced)
Date: May 3, 2025
"""

import argparse
import json
import logging
import os
import sys
from collections import Counter
from typing import Dict, List, Optional, Tuple

import numpy as np
from scipy.sparse import csr_matrix, issparse
from sklearn.cluster import KMeans, AgglomerativeClustering, DBSCAN
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import normalize

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('skills_clustering.log')
    ]
)
logger = logging.getLogger(__name__)

# Blacklist of junk skill tokens to remove before encoding
JUNK_SKILLS = {
    'state', 'accomplishments', 'highlights', 'sales', 'summary',
    'experience', 'skills', 'company', 'date', 'manager',
    'benefits', 'approach', 'city'
}


def jaccard_similarity(a: set, b: set) -> float:
    """Compute Jaccard similarity between two sets."""
    if not a and not b:
        return 1.0
    inter = a & b
    union = a | b
    return len(inter) / len(union)


class SkillsClusterer:
    """Cluster professional profiles based on their skills."""

    def __init__(
        self,
        n_clusters: Optional[int] = None,
        algorithm: str = 'agglomerative',
        min_skill_freq: int = 2,
        max_df: float = 0.7,
        dim_reduction: Optional[str] = 'svd',
        dim_components: int = 50,
        random_state: int = 42,
        dbscan_eps: float = 0.5,
        dbscan_min_samples: int = 5
    ):
        self.n_clusters = n_clusters
        self.algorithm = algorithm
        self.min_skill_freq = min_skill_freq
        self.max_df = max_df
        self.dim_reduction = dim_reduction
        self.dim_components = dim_components
        self.random_state = random_state
        self.dbscan_eps = dbscan_eps
        self.dbscan_min_samples = dbscan_min_samples

        # Attributes set in fit()
        self.vectorizer = None
        self.dim_reducer = None
        self.cluster_model = None
        self.profile_ids: List[str] = []
        self.features = None
        self.cluster_skill_importances: Dict[int, List[Tuple[str, float]]] = {}
        self.silhouette_avg: Optional[float] = None

    def load_data(self, path: str) -> List[Dict]:
        logger.info(f"Loading data from {path}")
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if not isinstance(data, list) or not data:
            raise ValueError("Input must be a non-empty list of profiles")
        return data

    def preprocess(self, profiles: List[Dict]) -> Tuple[List[str], List[str]]:
        logger.info(f"Preprocessing {len(profiles)} profiles")
        docs = []
        for p in profiles:
            self.profile_ids.append(p['id'])
            toks = [
                skill.lower() for skill in p.get('skills', [])
                if len(skill) > 2
                and skill.isalnum()
                and skill.lower() not in JUNK_SKILLS
            ]
            docs.append(" ".join(toks))
        return self.profile_ids, docs

    def encode(self, docs: List[str]) -> csr_matrix:
        logger.info(f"Encoding via TF-IDF (min_df={self.min_skill_freq}, max_df={self.max_df})")
        self.vectorizer = TfidfVectorizer(
            stop_words='english',
            min_df=self.min_skill_freq,
            max_df=self.max_df,
            max_features=300
        )
        X = self.vectorizer.fit_transform(docs)
        logger.info(f"Encoded matrix: {X.shape}")
        return X

    def reduce(self, X: csr_matrix) -> np.ndarray:
        if not self.dim_reduction:
            return X.toarray() if issparse(X) else X
        n = min(self.dim_components, X.shape[0], X.shape[1])
        logger.info(f"Reducing to {n} dims via SVD")
        self.dim_reducer = TruncatedSVD(n_components=n, random_state=self.random_state)
        Xr = self.dim_reducer.fit_transform(X)
        Xr = normalize(Xr)
        logger.info(f"Explained variance: {sum(self.dim_reducer.explained_variance_ratio_):.4f}")
        return Xr

    def fit(self, profiles: List[Dict]):
        ids, docs = self.preprocess(profiles)
        X = self.encode(docs)
        Xr = self.reduce(X)
        self.features = Xr

        # Choose algorithm
        if self.algorithm == 'kmeans':
            self.cluster_model = KMeans(
                n_clusters=self.n_clusters or 4,
                random_state=self.random_state,
                n_init=10
            )
            labels = self.cluster_model.fit_predict(Xr)

        elif self.algorithm == 'agglomerative':
            self.cluster_model = AgglomerativeClustering(
                n_clusters=self.n_clusters or 4,
                linkage='ward'
            )
            labels = self.cluster_model.fit_predict(Xr)

        elif self.algorithm == 'dbscan':
            self.cluster_model = DBSCAN(
                eps=self.dbscan_eps,
                min_samples=self.dbscan_min_samples
            )
            labels = self.cluster_model.fit_predict(Xr)

        else:
            raise ValueError("Algorithm must be 'kmeans', 'agglomerative', or 'dbscan'")

        # Silhouette
        if len(set(labels)) > 1:
            self.silhouette_avg = silhouette_score(Xr, labels)
            logger.info(f"Silhouette: {self.silhouette_avg:.4f}")

        # Top-skills per cluster
        fnames = self.vectorizer.get_feature_names_out()
        for cid in sorted(set(labels)):
            idx = [i for i, l in enumerate(labels) if l == cid]
            centroid = Xr[idx].mean(axis=0)
            pairs = sorted(zip(fnames, centroid.tolist()), key=lambda x: x[1], reverse=True)
            self.cluster_skill_importances[cid] = pairs

    def get_assignments(self) -> Dict[str, int]:
        labels = None
        if hasattr(self.cluster_model, 'labels_'):
            labels = self.cluster_model.labels_
        elif hasattr(self.cluster_model, 'labels'):
            labels = self.cluster_model.labels
        labels = labels.tolist() if hasattr(labels, 'tolist') else list(labels)
        return {pid: int(l) for pid, l in zip(self.profile_ids, labels)}

    def get_analysis(self) -> Dict:
        sizes = Counter(self.get_assignments().values())
        return {
            'algorithm': self.algorithm,
            'n_clusters': int(self.n_clusters or len(sizes)),
            'silhouette_score': float(self.silhouette_avg) if self.silhouette_avg else None,
            'cluster_sizes': {int(k): int(v) for k, v in sizes.items()},
            'top_skills': {
                cid: [
                    {'skill': s, 'importance': float(im)}
                    for s, im in self.cluster_skill_importances[cid][:10]
                ]
                for cid in sizes
            }
        }

    def save(self, outdir: str = 'results'):
        os.makedirs(outdir, exist_ok=True)
        with open(os.path.join(outdir, 'cluster_assignments.json'), 'w', encoding='utf-8') as f:
            json.dump(self.get_assignments(), f, indent=2)
        with open(os.path.join(outdir, 'cluster_analysis.json'), 'w', encoding='utf-8') as f:
            json.dump(self.get_analysis(), f, indent=2)
        logger.info(f"Saved results under {outdir}/")


def main():
    parser = argparse.ArgumentParser(description="Cluster skills from profile JSON data")
    parser.add_argument('--input', default='results/search_results.json', help='Path to input JSON')
    parser.add_argument('--outdir', default='results', help='Directory to save outputs')
    parser.add_argument('--algorithm', choices=['kmeans','agglomerative','dbscan'], default='agglomerative')
    parser.add_argument('--n-clusters', type=int, default=None)
    parser.add_argument('--min-skill-freq', type=int, default=2)
    parser.add_argument('--max-df', type=float, default=0.7, help='Max document frequency for tokens')
    parser.add_argument('--dim-reduction', choices=['svd', None], default='svd')
    parser.add_argument('--dim-components', type=int, default=50)
    parser.add_argument('--dbscan-eps', type=float, default=0.5)
    parser.add_argument('--dbscan-min-samples', type=int, default=5)
    parser.add_argument('--random-state', type=int, default=42)
    args = parser.parse_args()

    clusterer = SkillsClusterer(
        n_clusters=args.n_clusters,
        algorithm=args.algorithm,
        min_skill_freq=args.min_skill_freq,
        max_df=args.max_df,
        dim_reduction=args.dim_reduction,
        dim_components=args.dim_components,
        random_state=args.random_state,
        dbscan_eps=args.dbscan_eps,
        dbscan_min_samples=args.dbscan_min_samples
    )
    try:
        profiles = clusterer.load_data(args.input)
        clusterer.fit(profiles)
        clusterer.save(args.outdir)
    except Exception as e:
        logger.error(f"Error during clustering: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()