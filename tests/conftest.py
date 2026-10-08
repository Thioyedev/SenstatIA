import os

os.environ.setdefault(
    "ANTHROPIC_API_KEY",
    "sk-ant-api03-test-dummy-key-000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000AA",
)
os.environ.setdefault("CHROMA_PERSIST_DIR", "/tmp/test-chroma")
os.environ.setdefault("EMBEDDING_MODEL", "intfloat/multilingual-e5-large")

import pytest

from agents.state import AgentState

SAMPLE_CHUNKS = [
    {
        "text": "Le taux de pauvreté monétaire est de 37,5% en 2021-2022, soit environ 7 millions de personnes.",
        "institution": "ANSD",
        "report_name": "EHCVM 2021-2022",
        "year": 2021,
        "page_number": 32,
        "source_id": "ehcvm_2021",
        "url": "https://www.ansd.sn/ehcvm",
        "chunk_id": "chunk_001",
    },
    {
        "text": "En 2018-2019, le taux de pauvreté était estimé à 38,0% selon la même méthodologie EHCVM.",
        "institution": "ANSD",
        "report_name": "EHCVM 2021-2022",
        "year": 2021,
        "page_number": 33,
        "source_id": "ehcvm_2021",
        "url": "https://www.ansd.sn/ehcvm",
        "chunk_id": "chunk_002",
    },
]

TREND_OUTPUT = {
    "series": [
        {"year": 2018, "value": 38.0, "unit": "%", "label": "Taux de pauvreté"},
        {"year": 2021, "value": 37.5, "unit": "%", "label": "Taux de pauvreté"},
    ],
    "cagr": -0.004,
    "trend": "baisse",
    "insight": "Le taux de pauvreté a légèrement baissé entre 2018 et 2021.",
}

COMPARE_OUTPUT = {
    "entities": [
        {
            "name": "Milieu urbain",
            "values": [{"metric": "taux de pauvreté", "value": 20.5, "unit": "%", "year": 2021}],
        },
        {
            "name": "Milieu rural",
            "values": [{"metric": "taux de pauvreté", "value": 52.0, "unit": "%", "year": 2021}],
        },
    ],
    "gaps": [
        {
            "metric": "taux de pauvreté",
            "absolute": 31.5,
            "relative": 1.54,
            "winner": "Milieu rural",
            "unit": "%",
        }
    ],
    "insight": "Le milieu rural affiche un taux 2,5× supérieur au milieu urbain.",
}


@pytest.fixture
def sample_chunks():
    return SAMPLE_CHUNKS


@pytest.fixture
def trend_output():
    return TREND_OUTPUT


@pytest.fixture
def compare_output():
    return COMPARE_OUTPUT


@pytest.fixture
def base_state() -> AgentState:
    return AgentState(
        query="Quel est le taux de pauvreté au Sénégal en 2021 ?",
        intent="lookup",
        retrieved_chunks=SAMPLE_CHUNKS,
        trend_output=None,
        compare_output=None,
        compute_output=None,
        viz_output=None,
        synthesis="",
        citations=[],
        messages=[],
        conversation_history=[],
    )
