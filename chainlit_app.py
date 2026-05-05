import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import os
import httpx
import chainlit as cl
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("API_URL", "http://localhost:8000")

STARTERS = [
    ("👥 Population totale du Sénégal 2023 ?",
     "Quelle est la population totale du Sénégal en 2023 ?"),
    ("💰 Taux de pauvreté au Sénégal ?",
     "Quel est le taux de pauvreté au Sénégal ?"),
    ("📈 Croissance du PIB prévue en 2024 ?",
     "Quelle est la croissance du PIB prévue en 2024 ?"),
    ("💧 Accès à l'eau potable en milieu rural ?",
     "Quel est le taux d'accès à l'eau potable en milieu rural au Sénégal ?"),
    ("💼 Taux de chômage par région ?",
     "Quel est le taux de chômage par région au Sénégal selon le RGPH-5 ?"),
    ("🗺️ Régions les plus pauvres du Sénégal ?",
     "Quelles sont les régions les plus pauvres du Sénégal ?"),
]


@cl.set_starters
async def set_starters():
    return [
        cl.Starter(label=label, message=message)
        for label, message in STARTERS
    ]


@cl.on_message
async def on_message(message: cl.Message):
    async with cl.Step(name="Recherche dans les sources officielles…", show_input=False):
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{API_URL}/query",
                    json={"query": message.content},
                    timeout=90.0,
                )
                resp.raise_for_status()
                data      = resp.json()
                answer    = data["answer"]
                citations = data.get("citations", [])
        except Exception:
            answer    = "⚠️ Le service est momentanément indisponible. Réessayez dans quelques instants."
            citations = []

    # Deduplicate citations by (institution, report_name)
    seen, unique = set(), []
    for c in citations:
        key = (c.get("institution"), c.get("report_name"))
        if key not in seen:
            seen.add(key)
            unique.append(c)

    # Append source pills as HTML at end of answer
    if unique:
        pills = "".join(
            f'<span class="senstat-pill">📎 {c["institution"]} — {c["report_name"]}</span>'
            for c in unique
        )
        answer += f'\n\n<div class="senstat-sources">{pills}</div>'

    await cl.Message(content=answer).send()
