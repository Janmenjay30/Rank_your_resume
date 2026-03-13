"""
Embedding generation and FAISS vector store.

Uses the Gemini embeddings API to generate normalized vectors and stores them in
a FAISS IndexHNSWFlat index (approximate nearest-neighbour, inner-product metric).
"""

from __future__ import annotations

import os
import pickle
from pathlib import Path

import faiss
import numpy as np
import requests

GEMINI_API_KEY_ENV = "GEMINI_API_KEY"
GEMINI_MODEL_ENV = "GEMINI_EMBED_MODEL"
GEMINI_DIM_ENV = "GEMINI_EMBED_DIMENSION"

GEMINI_EMBED_MODEL = os.getenv(GEMINI_MODEL_ENV, "models/gemini-embedding-001")
DIMENSION = int(os.getenv(GEMINI_DIM_ENV, "768"))
EMBED_ENDPOINT = (
    f"https://generativelanguage.googleapis.com/v1beta/{GEMINI_EMBED_MODEL}:embedContent"
)

TASK_RETRIEVAL_DOCUMENT = "RETRIEVAL_DOCUMENT"
TASK_RETRIEVAL_QUERY = "RETRIEVAL_QUERY"


def _normalize(vec: np.ndarray) -> np.ndarray:
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec = vec / norm
    return vec.astype(np.float32)


def _embed_with_gemini(text: str, task_type: str) -> np.ndarray:
    api_key = os.getenv(GEMINI_API_KEY_ENV)
    if not api_key:
        raise RuntimeError(
            f"{GEMINI_API_KEY_ENV} is required to generate embeddings."
        )

    payload = {
        "model": GEMINI_EMBED_MODEL,
        "content": {"parts": [{"text": text}]},
        "taskType": task_type,
        "outputDimensionality": DIMENSION,
    }
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": api_key,
    }

    response = requests.post(EMBED_ENDPOINT, json=payload, headers=headers, timeout=60)
    response.raise_for_status()

    body = response.json()
    values = body.get("embedding", {}).get("values")
    if not values:
        raise RuntimeError("Gemini embedding response did not include embedding values.")

    return _normalize(np.asarray(values, dtype=np.float32))


def embed(text: str, task_type: str = TASK_RETRIEVAL_DOCUMENT) -> np.ndarray:
    """Return a normalized float32 embedding vector for *text*."""
    return _embed_with_gemini(text, task_type)


def embed_batch(
    texts: list[str],
    task_type: str = TASK_RETRIEVAL_DOCUMENT,
) -> np.ndarray:
    """Return an (N, D) float32 matrix of normalized embeddings."""
    return np.stack([embed(text, task_type=task_type) for text in texts]).astype(np.float32)


_CHUNK_WORDS = 200
_OVERLAP_WORDS = 50


def chunk_text(
    text: str,
    chunk_words: int = _CHUNK_WORDS,
    overlap_words: int = _OVERLAP_WORDS,
) -> list[str]:
    """
    Split *text* into overlapping word-based chunks.
    Returns at least one chunk (the original text if it is short enough).
    """
    words = text.split()
    if len(words) <= chunk_words:
        return [text]

    chunks: list[str] = []
    start = 0
    while start < len(words):
        end = min(start + chunk_words, len(words))
        chunks.append(" ".join(words[start:end]))
        if end == len(words):
            break
        start += chunk_words - overlap_words
    return chunks


def embed_long_text(
    text: str,
    task_type: str = TASK_RETRIEVAL_DOCUMENT,
) -> np.ndarray:
    """
    Embed a potentially long document by chunking it, embedding each chunk, and
    returning the mean-pooled normalized vector.
    """
    chunks = chunk_text(text)
    if len(chunks) == 1:
        return embed(chunks[0], task_type=task_type)

    vecs = embed_batch(chunks, task_type=task_type)
    mean_vec = vecs.mean(axis=0)
    return _normalize(mean_vec)


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity between two normalized vectors (dot product)."""
    return float(np.dot(a, b))


STORE_DIR = Path(__file__).resolve().parent / "vector_store"
INDEX_PATH = STORE_DIR / "faiss.index"
META_PATH = STORE_DIR / "metadata.pkl"

HNSW_M = 32


class VectorStore:
    """
    Persistent FAISS-backed vector store.

    Each entry stores:
        resume_id (str) -> embedding vector + metadata dict
    """

    def __init__(self) -> None:
        STORE_DIR.mkdir(parents=True, exist_ok=True)
        self._index: faiss.IndexHNSWFlat = self._load_or_create_index()
        self._metadata: list[dict] = self._load_metadata()

    def _load_or_create_index(self) -> faiss.IndexHNSWFlat:
        if INDEX_PATH.exists():
            index = faiss.read_index(str(INDEX_PATH))
            if index.d != DIMENSION:
                raise RuntimeError(
                    "Existing FAISS index dimension "
                    f"({index.d}) does not match configured embedding dimension "
                    f"({DIMENSION}). Remove ml_service/vector_store or rebuild the index."
                )
            return index
        return faiss.IndexHNSWFlat(DIMENSION, HNSW_M, faiss.METRIC_INNER_PRODUCT)

    def _load_metadata(self) -> list[dict]:
        if META_PATH.exists():
            with META_PATH.open("rb") as f:
                return pickle.load(f)
        return []

    def save(self) -> None:
        faiss.write_index(self._index, str(INDEX_PATH))
        with META_PATH.open("wb") as f:
            pickle.dump(self._metadata, f)

    def add(self, resume_id: str, vector: np.ndarray, meta: dict | None = None) -> None:
        """Add or overwrite an embedding for *resume_id*."""
        self._remove_by_id(resume_id)

        vec = vector.reshape(1, -1).astype(np.float32)
        self._index.add(vec)
        self._metadata.append({"resume_id": resume_id, **(meta or {})})
        self.save()

    def _remove_by_id(self, resume_id: str) -> None:
        """Remove all entries with the given resume_id (FAISS rebuild strategy)."""
        keep = [(i, m) for i, m in enumerate(self._metadata) if m["resume_id"] != resume_id]
        if len(keep) == len(self._metadata):
            return

        kept_indices = [i for i, _ in keep]
        kept_meta = [m for _, m in keep]

        if not kept_indices:
            self._index = faiss.IndexHNSWFlat(DIMENSION, HNSW_M, faiss.METRIC_INNER_PRODUCT)
            self._metadata = []
            return

        all_vecs = np.zeros((self._index.ntotal, DIMENSION), dtype=np.float32)
        self._index.reconstruct_n(0, self._index.ntotal, all_vecs)
        kept_vecs = all_vecs[kept_indices]

        new_index = faiss.IndexHNSWFlat(DIMENSION, HNSW_M, faiss.METRIC_INNER_PRODUCT)
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


_store: VectorStore | None = None


def get_store() -> VectorStore:
    global _store
    if _store is None:
        _store = VectorStore()
    return _store
