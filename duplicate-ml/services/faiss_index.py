"""
FAISS index for scalable candidate retrieval.

Uses IndexFlatIP (inner product) on L2-normalised embeddings,
which is equivalent to cosine similarity search.

For N projects, FAISS avoids the O(N^2) brute-force pair comparison
by returning only the top-K most similar candidates for each query.
"""
from __future__ import annotations

import logging
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)


class FAISSProjectIndex:
    """
    Wraps a FAISS IndexFlatIP and keeps a registry mapping
    FAISS integer indices → project IDs.
    """

    def __init__(self) -> None:
        self._index = None
        self._id_map: list[str] = []   # position i → project_id
        self._dim: Optional[int] = None

    def build(self, embeddings: np.ndarray, project_ids: list[str]) -> None:
        """
        Build the index from an (N, D) float32 embedding matrix.
        Embeddings must be L2-normalised (unit vectors).
        """
        try:
            import faiss  # type: ignore
        except ImportError:
            raise RuntimeError(
                "faiss-cpu is not installed. Run: pip install faiss-cpu"
            )

        if embeddings.ndim != 2 or embeddings.shape[0] == 0:
            raise ValueError("embeddings must be a non-empty 2-D float32 matrix.")

        n, d = embeddings.shape
        if n != len(project_ids):
            raise ValueError("Number of embeddings must equal number of project_ids.")

        self._dim = d
        self._id_map = list(project_ids)
        self._index = faiss.IndexFlatIP(d)
        self._index.add(embeddings)
        logger.info(f"FAISS index built with {n} projects (dim={d}).")

    def search(self, query_emb: np.ndarray, k: int = 10) -> list[tuple[str, float]]:
        """
        Find top-k most similar projects to a query embedding.

        Returns a list of (project_id, cosine_similarity) tuples,
        excluding exact-match hits (similarity == 1.0 for self-lookup).
        """
        if self._index is None:
            raise RuntimeError("Index has not been built. Call build() first.")

        k = min(k, len(self._id_map))
        query = query_emb.reshape(1, -1).astype(np.float32)
        scores, indices = self._index.search(query, k)

        results: list[tuple[str, float]] = []
        for idx, score in zip(indices[0], scores[0]):
            if idx < 0:          # FAISS returns -1 for empty slots
                continue
            pid = self._id_map[idx]
            results.append((pid, float(score)))

        return results

    def is_built(self) -> bool:
        return self._index is not None

    @property
    def size(self) -> int:
        return len(self._id_map) if self._id_map else 0
