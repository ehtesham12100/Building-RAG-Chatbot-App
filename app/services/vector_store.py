import os
# Restrict thread pools to 1 thread to avoid memory ballooning on 512MB RAM servers (Render free tier)
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
import gc
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings
from app.config import settings

class VectorStore:
    def __init__(self):
        self.persist_directory = settings.CHROMA_PATH
        self.client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        self.collection_name = "document_chunks"
        self._collection = None

    def _get_embedding_function(self):
        """
        Use Chroma's robust built-in ONNX all-MiniLM-L6-v2 embedding function.
        Runs locally, fast (~5ms), offline, with zero API cost and no quota limits.
        """
        from chromadb.utils import embedding_functions
        return embedding_functions.DefaultEmbeddingFunction()

    @property
    def collection(self):
        if self._collection is None:
            emb_fn = self._get_embedding_function()
            self._collection = self.client.get_or_create_collection(
                name=self.collection_name,
                embedding_function=emb_fn,
                metadata={"hnsw:space": "cosine"}
            )
        return self._collection

    def add_chunks(self, chunks: List[Dict[str, Any]]):
        """
        Insert chunks into ChromaDB using lightweight micro-batches
        to preserve low memory footprint on cloud containers (<= 512MB RAM).
        """
        if not chunks:
            return

        ids = [c["id"] for c in chunks]
        documents = [c["text"] for c in chunks]
        metadatas = [c["metadata"] for c in chunks]

        # Use micro-batches of 8 chunks to keep RAM usage under 250MB
        batch_size = 8
        for i in range(0, len(ids), batch_size):
            self.collection.upsert(
                ids=ids[i:i + batch_size],
                documents=documents[i:i + batch_size],
                metadatas=metadatas[i:i + batch_size]
            )
            # Free temporary tensor memory immediately
            gc.collect()

    def delete_document_chunks(self, document_id: int):
        """
        Delete all chunks belonging to a specific document.
        """
        try:
            self.collection.delete(
                where={"document_id": document_id}
            )
        except Exception as e:
            print(f"Warning deleting chunks for doc {document_id}: {e}")

    def query_similar(
        self,
        query_text: str,
        n_results: int = 4,
        document_ids: Optional[List[int]] = None
    ) -> List[Dict[str, Any]]:
        """
        Query vector store for relevant chunks with optional document filtering.
        """
        where_filter = None
        if document_ids:
            if len(document_ids) == 1:
                where_filter = {"document_id": document_ids[0]}
            else:
                where_filter = {"document_id": {"$in": document_ids}}

        # If collection is empty, return empty list
        count = self.collection.count()
        if count == 0:
            return []

        actual_n = min(n_results, count)

        query_kwargs = {
            "query_texts": [query_text],
            "n_results": actual_n
        }
        if where_filter:
            query_kwargs["where"] = where_filter

        results = self.collection.query(**query_kwargs)

        extracted = []
        if results and "documents" in results and results["documents"]:
            docs = results["documents"][0]
            metas = results["metadatas"][0] if "metadatas" in results else [{}] * len(docs)
            distances = results["distances"][0] if "distances" in results else [0.0] * len(docs)
            ids = results["ids"][0] if "ids" in results else [""] * len(docs)

            for doc_id, text, meta, dist in zip(ids, docs, metas, distances):
                # For cosine distance, similarity is roughly 1 - distance
                similarity = max(0.0, 1.0 - dist)
                extracted.append({
                    "id": doc_id,
                    "text": text,
                    "metadata": meta,
                    "similarity": round(similarity, 4)
                })

        # Sort by similarity descending
        extracted.sort(key=lambda x: x["similarity"], reverse=True)
        return extracted

vector_store = VectorStore()
