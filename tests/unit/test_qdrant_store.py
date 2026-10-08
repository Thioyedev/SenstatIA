"""QdrantStore dense-embedder selection and the guard against mixing models.

Runs Qdrant in local mode on a temp directory with fake embedders: no server,
no model download, no API call.
"""

import hashlib

import numpy as np
import pytest

pytest.importorskip("qdrant_client")
pytest.importorskip("fastembed")

import sentence_transformers  # noqa: E402

import vectorstore.qdrant_store as qs  # noqa: E402


def _vector(text: str, dim: int) -> np.ndarray:
    seed = int(hashlib.sha256(text.encode()).hexdigest()[:8], 16)
    return np.random.default_rng(seed).random(dim)


class _FakeSentenceTransformer:
    def __init__(self, name):
        self.name = name

    def get_sentence_embedding_dimension(self):
        return 8

    def encode(self, texts):
        return np.array([_vector(t, 8) for t in texts])


class _Sparse:
    def __init__(self, text):
        self.indices = np.array([len(text) % 50])
        self.values = np.array([1.0])


class _FakeSparse:
    def __init__(self, model):
        pass

    def embed(self, texts):
        return (_Sparse(t) for t in texts)

    def query_embed(self, query):
        return iter([_Sparse(query)])


class _FakeVoyage:
    def __init__(self, api_key=None):
        pass

    def embed(self, texts, model, input_type):
        class Result:
            embeddings = [_vector(t, qs.VOYAGE_DIM).tolist() for t in texts]

        return Result()


@pytest.fixture
def env(monkeypatch, tmp_path):
    monkeypatch.delenv("QDRANT_URL", raising=False)
    monkeypatch.delenv("QDRANT_DENSE_EMBEDDER", raising=False)
    monkeypatch.setenv("QDRANT_PATH", str(tmp_path / "qdrant"))
    monkeypatch.setenv("EMBEDDING_MODEL", "model-a")
    monkeypatch.setattr(qs, "SparseTextEmbedding", _FakeSparse)
    monkeypatch.setattr(sentence_transformers, "SentenceTransformer", _FakeSentenceTransformer)
    return monkeypatch


def _store():
    return qs.QdrantStore()


CHUNK = {"text": "Le taux de pauvreté est de 37,5 %", "source_id": "ehcvm_2021"}


def test_local_embedder_is_the_default_and_round_trips(env):
    store = _store()
    store.add_chunks([CHUNK])

    results = store.search(CHUNK["text"], n_results=1)

    assert store._embedder_name == "model-a"
    assert results[0]["text"] == CHUNK["text"]
    assert results[0]["source_id"] == "ehcvm_2021"
    assert qs.EMBEDDER_KEY not in results[0]
    store._client.close()


def test_refuses_collection_embedded_with_another_model(env):
    store = _store()
    store.add_chunks([CHUNK])
    store._client.close()

    env.setenv("EMBEDDING_MODEL", "model-b")
    with pytest.raises(RuntimeError, match="embedded with model-a"):
        _store()


def test_collection_without_marker_is_treated_as_voyage(env):
    # Collections indexed before the marker existed were all embedded with Voyage.
    store = _store()
    store._client.upsert(
        collection_name=qs.COLLECTION,
        points=[qs.PointStruct(id=1, vector={"dense": [0.1] * 8}, payload={"text": "x"})],
    )
    store._client.close()

    with pytest.raises(RuntimeError, match=f"embedded with {qs.VOYAGE_MODEL}"):
        _store()


def test_voyage_must_be_chosen_explicitly(env):
    env.setenv("QDRANT_DENSE_EMBEDDER", "voyage")
    env.setattr(qs, "_VOYAGE_AVAILABLE", True)
    env.setattr(qs, "voyageai", type("voyageai", (), {"Client": _FakeVoyage}), raising=False)

    store = _store()
    store.add_chunks([CHUNK])

    assert store._embedder_name == qs.VOYAGE_MODEL
    assert store.search(CHUNK["text"], n_results=1)[0]["text"] == CHUNK["text"]
    store._client.close()


def test_rejects_unknown_embedder_setting(env):
    env.setenv("QDRANT_DENSE_EMBEDDER", "openai")
    with pytest.raises(ValueError, match="'local' or 'voyage'"):
        _store()
