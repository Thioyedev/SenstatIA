"""FastAPI routes, with the agent graph and the vector store replaced by fakes."""

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

import api.routes.documents as documents_route
import api.routes.health as health_route
import api.routes.query as query_route
from api.main import app


@pytest.fixture
def client():
    return TestClient(app, raise_server_exceptions=False)


class _FakeGraph:
    def __init__(self, result=None, error=None):
        self.result = result
        self.error = error
        self.state = None

    def invoke(self, state):
        self.state = state
        if self.error:
            raise self.error
        return self.result


# ── POST /query ───────────────────────────────────────────────────────────────


class TestQuery:
    def _use_graph(self, monkeypatch, graph):
        monkeypatch.setattr(query_route, "get_graph", lambda: graph)

    def test_returns_answer_citations_and_intent(self, client, monkeypatch):
        graph = _FakeGraph(
            {
                "synthesis": "Le taux de pauvreté est de 37,5 %.",
                "citations": [
                    {"institution": "ANSD", "report_name": "EHCVM", "year": 2021, "page": 47}
                ],
                "intent": "lookup",
                "viz_output": None,
            }
        )
        self._use_graph(monkeypatch, graph)

        r = client.post("/query", json={"query": "taux de pauvreté"})

        assert r.status_code == 200
        body = r.json()
        assert body["query"] == "taux de pauvreté"
        assert body["answer"] == "Le taux de pauvreté est de 37,5 %."
        assert body["citations"][0]["institution"] == "ANSD"
        assert body["citations"][0]["page"] == 47
        assert body["intent"] == "lookup"

    def test_strips_inline_page_citations(self, client, monkeypatch):
        graph = _FakeGraph({"synthesis": "Le taux est de 37,5 % [ANSD — EHCVM 2021, p.47]."})
        self._use_graph(monkeypatch, graph)

        r = client.post("/query", json={"query": "q"})

        assert r.json()["answer"] == "Le taux est de 37,5 %."

    def test_defaults_when_graph_omits_optional_keys(self, client, monkeypatch):
        self._use_graph(monkeypatch, _FakeGraph({"synthesis": "ok"}))

        body = client.post("/query", json={"query": "q"}).json()

        assert body["citations"] == []
        assert body["intent"] == "lookup"
        assert body["viz"] is None

    def test_passes_history_and_a_clean_state_to_the_graph(self, client, monkeypatch):
        graph = _FakeGraph({"synthesis": "ok"})
        self._use_graph(monkeypatch, graph)

        client.post(
            "/query",
            json={
                "query": "et en 2018 ?",
                "messages": [
                    {"role": "user", "content": "taux de pauvreté"},
                    {"role": "assistant", "content": "37,5 %"},
                ],
            },
        )

        assert graph.state["query"] == "et en 2018 ?"
        assert graph.state["conversation_history"] == [
            {"role": "user", "content": "taux de pauvreté"},
            {"role": "assistant", "content": "37,5 %"},
        ]
        assert graph.state["retrieved_chunks"] == []
        assert graph.state["citations"] == []

    def test_graph_failure_returns_500_with_detail(self, client, monkeypatch):
        self._use_graph(monkeypatch, _FakeGraph(error=RuntimeError("chroma unavailable")))

        r = client.post("/query", json={"query": "q"})

        assert r.status_code == 500
        assert r.json()["detail"] == "chroma unavailable"

    def test_missing_query_is_rejected(self, client):
        assert client.post("/query", json={}).status_code == 422


# ── GET /health ───────────────────────────────────────────────────────────────


class TestHealth:
    def test_ok_reports_chunk_count(self, client, monkeypatch):
        store = MagicMock()
        store.collection.count.return_value = 3793
        monkeypatch.setattr(health_route, "_get_store", lambda: store)

        body = client.get("/health").json()

        assert body["status"] == "ok"
        assert body["chunks_indexed"] == 3793

    def test_store_failure_is_degraded_not_500(self, client, monkeypatch):
        def broken():
            raise RuntimeError("no store")

        monkeypatch.setattr(health_route, "_get_store", broken)

        r = client.get("/health")

        assert r.status_code == 200
        assert r.json() == {"status": "degraded", "chunks_indexed": 0, "version": "0.1.0"}


# ── GET /documents ────────────────────────────────────────────────────────────


class TestDocuments:
    def _use_store(self, monkeypatch, counts):
        store = MagicMock()

        def count(where):
            value = counts[where["source_id"]]
            if isinstance(value, Exception):
                raise value
            return value

        store.count.side_effect = count
        monkeypatch.setattr(documents_route, "_get_store", lambda: store)

    def test_lists_sources_with_chunk_counts(self, client, monkeypatch):
        monkeypatch.setattr(
            documents_route,
            "load_sources",
            lambda: [
                {
                    "id": "ehcvm_2021",
                    "institution": "ANSD",
                    "name": "EHCVM",
                    "year": 2021,
                    "topics": ["pauvreté"],
                    "url": "https://www.ansd.sn",
                }
            ],
        )
        self._use_store(monkeypatch, {"ehcvm_2021": 412})

        r = client.get("/documents")

        assert r.status_code == 200
        assert r.json() == [
            {
                "source_id": "ehcvm_2021",
                "institution": "ANSD",
                "report_name": "EHCVM",
                "year": 2021,
                "topics": ["pauvreté"],
                "url": "https://www.ansd.sn",
                "chunk_count": 412,
            }
        ]

    def test_source_without_year_is_listed(self, client, monkeypatch):
        # Regression: year was a required int and 9 registry sources have none,
        # so the whole endpoint returned 500.
        monkeypatch.setattr(
            documents_route, "load_sources", lambda: [{"id": "ansd_neer", "year": None}]
        )
        self._use_store(monkeypatch, {"ansd_neer": 10})

        r = client.get("/documents")

        assert r.status_code == 200
        assert r.json()[0]["year"] is None

    def test_real_registry_is_served(self, client, monkeypatch):
        self._use_store(monkeypatch, MagicMock(__getitem__=lambda self, key: 0))

        r = client.get("/documents")

        assert r.status_code == 200
        assert len(r.json()) == len(documents_route.load_sources())

    def test_count_failure_reports_zero(self, client, monkeypatch):
        monkeypatch.setattr(documents_route, "load_sources", lambda: [{"id": "x", "year": 2020}])
        self._use_store(monkeypatch, {"x": RuntimeError("timeout")})

        assert client.get("/documents").json()[0]["chunk_count"] == 0


# ── CORS ──────────────────────────────────────────────────────────────────────


def _preflight(client, origin):
    return client.options(
        "/query",
        headers={"Origin": origin, "Access-Control-Request-Method": "POST"},
    )


def test_cors_allows_the_local_frontend(client):
    r = _preflight(client, "http://localhost:8501")
    assert r.headers.get("access-control-allow-origin") == "http://localhost:8501"


def test_cors_rejects_other_origins(client):
    r = _preflight(client, "https://evil.example")
    assert "access-control-allow-origin" not in r.headers
