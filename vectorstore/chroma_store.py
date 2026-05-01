import chromadb
from chromadb.utils import embedding_functions
from loguru import logger
import os

class ChromaStore:
    def __init__(self):
        persist_dir = os.getenv("CHROMA_PERSIST_DIR", "./data/chroma")
        model_name = os.getenv("EMBEDDING_MODEL",
                               "intfloat/multilingual-e5-large")

        self.client = chromadb.PersistentClient(path=persist_dir)
        self.ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=model_name
        )
        self.collection = self.client.get_or_create_collection(
            name="senstat",
            embedding_function=self.ef,
            metadata={"hnsw:space": "cosine"}
        )

    def add_chunks(self, chunks: list[dict]):
        if not chunks:
            return

        ids = [f"{c['source_id']}_p{c['page_number']}_c{c['chunk_index']}"
               for c in chunks]
        documents = [c["text"] for c in chunks]
        metadatas = [{k: v for k, v in c.items()
                      if k not in ("text",) and isinstance(v, (str, int, float, bool))}
                     for c in chunks]

        # Batch de 100 pour éviter les timeouts
        batch_size = 100
        for i in range(0, len(chunks), batch_size):
            self.collection.add(
                ids=ids[i:i+batch_size],
                documents=documents[i:i+batch_size],
                metadatas=metadatas[i:i+batch_size]
            )

    def search(self, query: str, n_results: int = 20,
               where: dict = None) -> list[dict]:
        kwargs = {"query_texts": [query], "n_results": n_results,
                  "include": ["documents", "metadatas", "distances"]}
        if where:
            kwargs["where"] = where

        results = self.collection.query(**kwargs)

        chunks = []
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0]
        ):
            chunks.append({
                "text": doc,
                "score": 1 - dist,  # cosine distance → similarity
                **meta
            })
        return chunks
