from __future__ import annotations

import ast
import threading
from pathlib import Path

import faiss
import pandas as pd

from app.core.config import settings


class FaissStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._index = None
        self._metadata: list[dict] = []
        self._index_mtime = None
        self._metadata_mtime = None

    def _resolve_path(self, configured_path: str) -> Path:
        direct = Path(configured_path)
        if direct.exists():
            return direct

        project_root = Path(__file__).resolve().parents[3]
        candidate = project_root / configured_path
        if candidate.exists():
            return candidate

        app_root = Path("/app") / configured_path
        return app_root

    def _parse_embedding(self, value):
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            try:
                parsed = ast.literal_eval(value)
            except (ValueError, SyntaxError):
                return None
            return parsed if isinstance(parsed, list) else None
        return None

    def _load_if_needed(self) -> None:
        index_path = self._resolve_path(settings.faiss_index_path)
        metadata_path = self._resolve_path(settings.faiss_metadata_csv_path)
        if not index_path.exists() or not metadata_path.exists():
            raise FileNotFoundError(
                f"FAISS artifacts not found. index={index_path} metadata={metadata_path}"
            )

        index_mtime = index_path.stat().st_mtime
        metadata_mtime = metadata_path.stat().st_mtime
        if (
            self._index is not None
            and self._metadata
            and self._index_mtime == index_mtime
            and self._metadata_mtime == metadata_mtime
        ):
            return

        index = faiss.read_index(str(index_path))
        df = pd.read_csv(metadata_path)
        if "title" not in df.columns or "content" not in df.columns:
            raise ValueError("Metadata CSV must contain 'title' and 'content' columns")

        metadata: list[dict] = []
        for _, row in df.iterrows():
            metadata.append(
                {
                    "title": str(row.get("title") or "").strip(),
                    "description": str(row.get("description") or row.get("content") or "").strip(),
                    "genre": str(row.get("genre") or "").strip() or None,
                }
            )

        if index.ntotal != len(metadata):
            raise ValueError(
                f"FAISS index/vector mismatch: index has {index.ntotal}, metadata has {len(metadata)}"
            )

        self._index = index
        self._metadata = metadata
        self._index_mtime = index_mtime
        self._metadata_mtime = metadata_mtime

    def search(self, question_embedding: list[float], top_k: int) -> list[dict]:
        with self._lock:
            self._load_if_needed()
            index = self._index
            metadata = self._metadata

        if index is None or not metadata:
            return []

        import numpy as np

        query = np.array([question_embedding], dtype="float32")
        distances, indices = index.search(query, top_k)

        results: list[dict] = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < 0 or idx >= len(metadata):
                continue
            item = metadata[idx]
            similarity_score = float(1.0 / (1.0 + dist))
            results.append(
                {
                    "title": item["title"],
                    "description": item["description"],
                    "score": round(similarity_score, 4),
                }
            )
        return results

    def is_ready(self) -> bool:
        with self._lock:
            self._load_if_needed()
        return True


faiss_store = FaissStore()
