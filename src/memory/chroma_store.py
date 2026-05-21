"""
Lightweight ChromaDB vector store for ADHD memory.
Stores conversation snippets, user patterns, and intervention outcomes
for semantic retrieval.
"""

import json
import hashlib
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

try:
    import chromadb
    from chromadb.config import Settings
    HAS_CHROMA = True
except ImportError:
    logger.warning("ChromaDB not installed — using JSON fallback storage")
    HAS_CHROMA = False


class ChromaMemoryStore:
    """
    Persistent memory store using ChromaDB (lightweight mode).
    Falls back to JSON file storage if ChromaDB is unavailable.

    Stores:
      - User conversation summaries
      - Procrastination triggers
      - Successful intervention patterns
      - Focus session stats
      - Emotional patterns
    """

    COLLECTION_NAME = "adhd_memory"
    PERSIST_DIR = ".adhd_memory_db"

    _instance = None

    def __new__(cls, *args, **kwargs):
        """Singleton to reuse the same ChromaDB client."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, user_id: str = "default"):
        if hasattr(self, "_initialized") and self._initialized:
            return
        self._initialized = True

        self.user_id = user_id
        self.persist_dir = Path(self.PERSIST_DIR)
        self.persist_dir.mkdir(exist_ok=True)

        self._collection = None
        self._fallback_file = self.persist_dir / f"fallback_{user_id}.json"
        self._fallback_data = self._load_fallback()

        if HAS_CHROMA:
            self._init_chromadb()
        else:
            logger.info("Using JSON fallback storage for memory")

    def _init_chromadb(self):
        """Initialize ChromaDB client and collection."""
        try:
            persist_path = str(self.persist_dir / "chroma")
            self._client = chromadb.PersistentClient(
                path=persist_path,
                settings=Settings(anonymized_telemetry=False),
            )
            # Try to get existing collection or create new
            existing = self._client.list_collections()
            names = [c.name for c in existing] if existing else []
            if self.COLLECTION_NAME in names:
                self._collection = self._client.get_collection(self.COLLECTION_NAME)
                logger.debug(f"Loaded existing collection: {self.COLLECTION_NAME}")
            else:
                self._collection = self._client.create_collection(self.COLLECTION_NAME)
                logger.debug(f"Created new collection: {self.COLLECTION_NAME}")
        except Exception as e:
            logger.warning(f"ChromaDB init failed: {e} — using JSON fallback")
            self._collection = None

    @property
    def collection(self):
        return self._collection

    # ---------- ID generation ----------

    def _make_id(self, prefix: str, content: str) -> str:
        raw = f"{self.user_id}:{prefix}:{content}"
        return hashlib.md5(raw.encode()).hexdigest()[:16]

    # ---------- Fallback JSON storage ----------

    def _load_fallback(self) -> list:
        if self._fallback_file.exists():
            try:
                with open(self._fallback_file) as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                return []
        return []

    def _save_fallback(self):
        try:
            with open(self._fallback_file, "w") as f:
                json.dump(self._fallback_data, f, indent=2)
        except OSError as e:
            logger.error(f"Failed to save fallback memory: {e}")

    # ---------- Store operations ----------

    def store(
        self,
        content: str,
        metadata: Optional[dict] = None,
        memory_type: str = "conversation",
    ):
        """Store a memory entry with optional metadata."""
        if metadata is None:
            metadata = {}
        metadata.update({
            "user_id": self.user_id,
            "memory_type": memory_type,
            "timestamp": datetime.now().isoformat(),
        })

        entry_id = self._make_id(memory_type, content[:100])

        if self.collection is not None:
            try:
                self.collection.add(
                    ids=[entry_id],
                    documents=[content],
                    metadatas=[metadata],
                )
                return
            except Exception as e:
                logger.warning(f"ChromaDB store failed: {e} — falling back")

        # Fallback: JSON storage
        existing_ids = {e.get("id") for e in self._fallback_data}
        if entry_id not in existing_ids:
            self._fallback_data.append({
                "id": entry_id,
                "content": content,
                "metadata": metadata,
            })
            self._save_fallback()

    def search(
        self,
        query: str,
        n_results: int = 5,
        memory_type: Optional[str] = None,
    ) -> list[dict]:
        """
        Semantic search across stored memories.
        Falls back to keyword matching if ChromaDB is unavailable.
        """
        results = []

        if self.collection is not None:
            try:
                where = {"user_id": self.user_id}
                if memory_type:
                    where["memory_type"] = memory_type

                raw = self.collection.query(
                    query_texts=[query],
                    n_results=n_results,
                    where=where,
                )
                if raw and raw.get("documents") and raw["documents"][0]:
                    for i, doc in enumerate(raw["documents"][0]):
                        results.append({
                            "content": doc,
                            "metadata": (raw.get("metadatas") or [{}])[0][i]
                            if raw.get("metadatas") else {},
                            "distance": (raw.get("distances") or [[]])[0][i]
                            if raw.get("distances") else None,
                        })
                return results
            except Exception as e:
                logger.warning(f"ChromaDB search failed: {e} — using fallback")

        # Fallback: keyword matching
        query_lower = query.lower()
        query_words = set(query_lower.split())

        for entry in self._fallback_data:
            if memory_type and entry.get("metadata", {}).get("memory_type") != memory_type:
                continue
            content_lower = entry.get("content", "").lower()
            # Simple relevance: count matching words
            content_words = set(content_lower.split())
            overlap = len(query_words & content_words)
            if overlap > 0:
                results.append({
                    "content": entry.get("content", ""),
                    "metadata": entry.get("metadata", {}),
                    "relevance_score": overlap / max(len(query_words), 1),
                })

        results.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
        return results[:n_results]

    def get_recent(self, memory_type: Optional[str] = None, limit: int = 10) -> list[dict]:
        """Get most recent memories of a given type (or all types if None)."""
        entries = []

        if self.collection is not None:
            try:
                where: dict[str, Any] = {"user_id": self.user_id}
                if memory_type:
                    where["memory_type"] = memory_type
                raw = self.collection.get(
                    where=where,
                    limit=limit,
                )
                if raw and raw.get("documents"):
                    metadatas = raw.get("metadatas") or []
                    for i, doc in enumerate(raw["documents"]):
                        meta = metadatas[i] if i < len(metadatas) and metadatas[i] else {}
                        entries.append({
                            "content": doc,
                            "metadata": meta,
                        })
                return entries
            except Exception as e:
                logger.warning(f"ChromaDB get_recent failed: {e} — using fallback")

        # Fallback
        for entry in reversed(self._fallback_data):
            meta = entry.get("metadata", {})
            if memory_type is None or meta.get("memory_type") == memory_type:
                entries.append({
                    "content": entry.get("content", ""),
                    "metadata": meta,
                })
                if len(entries) >= limit:
                    break
        return entries

    def get_stats(self) -> dict:
        """Get memory store statistics."""
        count = 0
        if self.collection is not None:
            try:
                count = self.collection.count()
            except Exception as e:
                logger.warning(f"ChromaDB count failed: {e}")
                count = len(self._fallback_data)
        else:
            count = len(self._fallback_data)

        return {
            "total_entries": count,
            "user_id": self.user_id,
            "storage": "chromadb" if self.collection is not None else "json_fallback",
        }

    def clear_user_memory(self):
        """Clear all memories for this user."""
        if self.collection is not None:
            try:
                self.collection.delete(where={"user_id": self.user_id})
            except Exception as e:
                logger.warning(f"ChromaDB clear_user_memory failed: {e} — clearing fallback only")
        self._fallback_data = []
        self._save_fallback()
