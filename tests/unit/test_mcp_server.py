"""MCP tools answer through the HTTP API; the API is replaced by httpx.MockTransport."""

import json

import httpx
import pytest

pytest.importorskip("mcp")

import mcp_server  # noqa: E402


def _use_api(monkeypatch, handler):
    calls = []

    def recording(request):
        calls.append(request)
        return handler(request)

    monkeypatch.setattr(
        mcp_server,
        "_client",
        lambda: httpx.Client(base_url="http://api.test", transport=httpx.MockTransport(recording)),
    )
    return calls


class TestQuery:
    def test_posts_the_question_and_formats_citations(self, monkeypatch):
        calls = _use_api(
            monkeypatch,
            lambda r: httpx.Response(
                200,
                json={
                    "answer": "Le taux de pauvreté est de 37,5 %.",
                    "citations": [
                        {"institution": "ANSD", "report_name": "EHCVM 2021-2022", "page": 36}
                    ],
                },
            ),
        )

        out = mcp_server.senstat_query("taux de pauvreté")

        assert calls[0].method == "POST"
        assert calls[0].url.path == "/query"
        assert json.loads(calls[0].content) == {"query": "taux de pauvreté"}
        assert out == (
            "Le taux de pauvreté est de 37,5 %.\n\nSources:\n  • ANSD — EHCVM 2021-2022, p.36"
        )

    def test_english_request_and_no_citations(self, monkeypatch):
        calls = _use_api(
            monkeypatch, lambda r: httpx.Response(200, json={"answer": "No data.", "citations": []})
        )

        out = mcp_server.senstat_query("poverty rate", language="en")

        assert json.loads(calls[0].content)["query"] == "poverty rate Answer in English."
        assert out == "No data."


class TestListSources:
    def test_searchable_means_chunks_in_the_index(self, monkeypatch):
        _use_api(
            monkeypatch,
            lambda r: httpx.Response(
                200,
                json=[
                    {
                        "source_id": "ehcvm_2021",
                        "institution": "ANSD",
                        "report_name": "EHCVM 2021",
                        "year": 2021,
                        "topics": ["pauvreté"],
                        "chunk_count": 628,
                    },
                    {
                        "source_id": "ansd_neer",
                        "institution": "ANSD",
                        "report_name": "NEER",
                        "year": None,
                        "topics": [],
                        "chunk_count": 0,
                    },
                ],
            ),
        )

        out = mcp_server.senstat_list_sources()

        searchable, absent = out.split("NOT INDEXED")
        assert "(1 searchable, 1 registered but not indexed)" in out
        assert "EHCVM 2021" in searchable and "628 chunks" in searchable
        assert "NEER" in absent and "NEER" not in searchable


class TestErrors:
    def test_unreachable_api_names_the_url(self, monkeypatch):
        def refuse(request):
            raise httpx.ConnectError("connection refused", request=request)

        _use_api(monkeypatch, refuse)

        with pytest.raises(RuntimeError, match="unreachable at"):
            mcp_server.senstat_query("q")

    def test_api_error_status_is_reported(self, monkeypatch):
        _use_api(monkeypatch, lambda r: httpx.Response(500, json={"detail": "chroma down"}))

        with pytest.raises(RuntimeError, match="500"):
            mcp_server.senstat_list_sources()
