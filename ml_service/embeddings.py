"""
Embedding generation and FAISS vector store.
Generates 384-d sentence vectors (all-MiniLM-L6-v2) and stores them in FAISS.
"""

from __future__ import annotations

import json
import os
import pickle
from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

# ─────────────────────────────────────────────
# Model singleton
# ─────────────────────────────────────────────

_model: SentenceTransformer | None = None


def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


# ─────────────────────────────────────────────
# Embedding helpers
# ─────────────────────────────────────────────

def embed(text: str) -> np.ndarray:
    """Return a normalised float32 embedding vector for *text*."""
    model = get_model()
    vec = model.encode(text, convert_to_numpy=True, normalize_embeddings=True)
    return vec.astype(np.float32)


def embed_batch(texts: list[str]) -> np.ndarray:
    """Return an (N, D) float32 matrix of normalised embeddings."""
    model = get_model()
    vecs = model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
    return vecs.astype(np.float32)


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity between two normalised vectors (dot product)."""
    return float(np.dot(a, b))


# ─────────────────────────────────────────────
# FAISS Vector Store
# ─────────────────────────────────────────────

STORE_DIR = Path(__file__).resolve().parent / "vector_store"
INDEX_PATH = STORE_DIR / "faiss.index"
META_PATH = STORE_DIR / "metadata.pkl"

DIMENSION = 384  # all-MiniLM-L6-v2 output size


class VectorStore:
    """
    Persistent FAISS-backed vector store.

    Each entry stores:
        resume_id (str) → embedding vector + metadata dict
    """

    def __init__(self) -> None:
        STORE_DIR.mkdir(parents=True, exist_ok=True)
        self._index: faiss.IndexFlatIP = self._load_or_create_index()
        self._metadata: list[dict] = self._load_metadata()  # parallel list to index rows

    # ── persistence ──────────────────────────

    def _load_or_create_index(self) -> faiss.IndexFlatIP:
        if INDEX_PATH.exists():
            return faiss.read_index(str(INDEX_PATH))
        # Inner-product index works as cosine similarity when vectors are normalised
        return faiss.IndexFlatIP(DIMENSION)

    def _load_metadata(self) -> list[dict]:
        if META_PATH.exists():
            with META_PATH.open("rb") as f:
                return pickle.load(f)
        return []

    def save(self) -> None:
        faiss.write_index(self._index, str(INDEX_PATH))
        with META_PATH.open("wb") as f:
            pickle.dump(self._metadata, f)

    # ── CRUD ─────────────────────────────────

    def add(self, resume_id: str, vector: np.ndarray, meta: dict | None = None) -> None:
        """Add or overwrite an embedding for *resume_id*."""
        # Remove existing entry for this id (if any)
        self._remove_by_id(resume_id)

        vec = vector.reshape(1, -1).astype(np.float32)
        self._index.add(vec)
        self._metadata.append({"resume_id": resume_id, **(meta or {})})
        self.save()

    def _remove_by_id(self, resume_id: str) -> None:
        """Remove all entries with the given resume_id (FAISS rebuild strategy)."""
        keep = [(i, m) for i, m in enumerate(self._metadata) if m["resume_id"] != resume_id]
        if len(keep) == len(self._metadata):
            return  # nothing to remove

        kept_indices = [i for i, _ in keep]
        kept_meta = [m for _, m in keep]

        if not kept_indices:
            self._index = faiss.IndexFlatIP(DIMENSION)
            self._metadata = []
            return

        # Reconstruct vectors for kept entries
        all_vecs = np.zeros((self._index.ntotal, DIMENSION), dtype=np.float32)
        self._index.reconstruct_n(0, self._index.ntotal, all_vecs)
        kept_vecs = all_vecs[kept_indices]

        new_index = faiss.IndexFlatIP(DIMENSION)
        new_index.add(kept_vecs)
        self._index = new_index
        self._metadata = kept_meta

    def remove(self, resume_id: str) -> None:
        self._remove_by_id(resume_id)
        self.save()

    def search(self, query_vector: np.ndarray, top_k: int = 20) -> list[dict]:
        """
        Return the top-k most similar resumes.
        Each result: {"resume_id": ..., "score": ..., ...meta}
        """
        if self._index.ntotal == 0:
            return []

        k = min(top_k, self._index.ntotal)
        vec = query_vector.reshape(1, -1).astype(np.float32)
        scores, indices = self._index.search(vec, k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:
                continue
            entry = dict(self._metadata[idx])
            entry["score"] = float(score)
            results.append(entry)

        return results

    def count(self) -> int:
        return self._index.ntotal

    def get_all_ids(self) -> list[str]:
        return [m["resume_id"] for m in self._metadata]


# Module-level singleton
_store: VectorStore | None = None


def get_store() -> VectorStore:
    global _store
    if _store is None:
        _store = VectorStore()
    return _store
