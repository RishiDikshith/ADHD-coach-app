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
        """Store a memory entry with optional metadata and semantic deduplication."""
        if metadata is None:
            metadata = {}
        metadata.update({
            "user_id": self.user_id,
            "memory_type": memory_type,
            "timestamp": datetime.now().isoformat(),
            "duplicate_count": 1,
        })

        entry_id = self._make_id(memory_type, content[:100])

        # 1. Semantic Deduplication: Check if highly similar memory already exists
        if self.collection is not None:
            try:
                # Query for highly similar content
                similar = self.collection.query(
                    query_texts=[content],
                    n_results=1,
                    where={"user_id": self.user_id, "memory_type": memory_type}
                )
                if similar and similar.get("documents") and similar["documents"][0]:
                    doc = similar["documents"][0][0]
                    dist = similar["distances"][0][0] if similar.get("distances") else 1.0
                    # Standard cosine/L2 distance threshold for near-duplicates
                    if dist < 0.18:
                        match_id = similar["ids"][0][0]
                        existing_meta = similar["metadatas"][0][0] if (similar.get("metadatas") and similar["metadatas"][0]) else {}
                        existing_meta["duplicate_count"] = existing_meta.get("duplicate_count", 1) + 1
                        existing_meta["last_updated"] = datetime.now().isoformat()
                        if "importance" in existing_meta:
                            existing_meta["importance"] = min(1.0, existing_meta["importance"] + 0.05)
                        
                        self.collection.update(
                            ids=[match_id],
                            documents=[doc],
                            metadatas=[existing_meta]
                        )
                        logger.debug(f"Deduplicated existing memory matching: {match_id}")
                        return
            except Exception as e:
                logger.warning(f"ChromaDB deduplication check failed: {e} — writing standard entry")

        # Fallback JSON deduplication
        def content_similarity(s1, s2):
            w1 = set(s1.lower().split())
            w2 = set(s2.lower().split())
            if not w1 or not w2:
                return 0.0
            return len(w1 & w2) / max(len(w1), len(w2))

        for entry in self._fallback_data:
            if entry.get("metadata", {}).get("memory_type") == memory_type:
                if entry.get("content") == content or content_similarity(entry.get("content", ""), content) > 0.82:
                    entry["metadata"]["duplicate_count"] = entry["metadata"].get("duplicate_count", 1) + 1
                    entry["metadata"]["last_updated"] = datetime.now().isoformat()
                    if "importance" in entry["metadata"]:
                        entry["metadata"]["importance"] = min(1.0, entry["metadata"]["importance"] + 0.05)
                    self._save_fallback()
                    logger.debug(f"Deduplicated fallback memory matching content.")
                    return

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

    def search_with_sliding_window(
        self,
        query: str,
        n_results: int = 3,
        window_size: int = 2,
        memory_type: Optional[str] = None,
    ) -> list[dict]:
        """
        Semantic search with sliding window context retrieval around matching hits.
        Returns a list of matching dicts, each with an added 'window_context' string.
        """
        results = self.search(query, n_results=n_results, memory_type=memory_type)
        if not results:
            return []

        # We will build sliding window around each search match
        if self.collection is not None:
            try:
                # Fetch all documents for this user to locate sequence chronologically
                where = {"user_id": self.user_id}
                if memory_type:
                    where["memory_type"] = memory_type
                
                raw_all = self.collection.get(where=where)
                if raw_all and raw_all.get("documents"):
                    all_docs = []
                    for i, doc in enumerate(raw_all["documents"]):
                        meta = (raw_all.get("metadatas") or [{}])[i] or {}
                        ts = meta.get("timestamp", "")
                        all_docs.append({
                            "id": raw_all["ids"][i],
                            "content": doc,
                            "metadata": meta,
                            "timestamp": ts,
                        })
                    
                    # Sort chronologically by timestamp
                    all_docs.sort(key=lambda x: x["timestamp"])
                    
                    # For each match result, try to find it in chronological list
                    for res in results:
                        match_idx = None
                        res_content = res.get("content", "")
                        for idx, item in enumerate(all_docs):
                            if item["content"] == res_content:
                                match_idx = idx
                                break
                        
                        if match_idx is not None:
                            start_idx = max(0, match_idx - window_size)
                            end_idx = min(len(all_docs), match_idx + window_size + 1)
                            window_items = all_docs[start_idx:end_idx]
                            
                            # Format nicely
                            context_lines = []
                            for item in window_items:
                                m_type = item["metadata"].get("type", "message")
                                prefix = "User: " if m_type == "user_message" else "AI: " if m_type == "assistant_response" else ""
                                context_lines.append(f"{prefix}{item['content']}")
                            res["window_context"] = "\n".join(context_lines)
            except Exception as e:
                logger.warning(f"ChromaDB sliding window construction failed: {e}")

        # Fallback sliding window context
        if not results or "window_context" not in results[0]:
            for res in results:
                res_content = res.get("content", "")
                match_idx = None
                for idx, entry in enumerate(self._fallback_data):
                    if entry.get("content") == res_content:
                        match_idx = idx
                        break
                
                if match_idx is not None:
                    start_idx = max(0, match_idx - window_size)
                    end_idx = min(len(self._fallback_data), match_idx + window_size + 1)
                    window_items = self._fallback_data[start_idx:end_idx]
                    
                    context_lines = []
                    for item in window_items:
                        m_type = item.get("metadata", {}).get("type", "message")
                        prefix = "User: " if m_type == "user_message" else "AI: " if m_type == "assistant_response" else ""
                        context_lines.append(f"{prefix}{item.get('content')}")
                    res["window_context"] = "\n".join(context_lines)

        return results

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
