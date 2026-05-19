"""
World Bank Open Data API fetcher.
Fetches development indicators for Senegal.

API docs: https://datahelpdesk.worldbank.org/knowledgebase/articles/889392
"""
import httpx
from loguru import logger

INDICATOR_LABELS = {
    "NY.GDP.MKTP.CD":      "PIB (USD courants)",
    "NY.GDP.PCAP.CD":      "PIB par habitant (USD courants)",
    "NY.GDP.MKTP.KD.ZG":   "Croissance du PIB réel (%)",
    "SP.POP.TOTL":         "Population totale",
    "SP.URB.TOTL.IN.ZS":   "Population urbaine (% du total)",
    "SI.POV.NAHC":         "Taux de pauvreté national (%)",
    "SI.POV.GINI":         "Coefficient de Gini",
    "SL.UEM.TOTL.ZS":      "Chômage total (% population active)",
    "SL.TLF.CACT.ZS":      "Taux d'activité (% population 15+)",
    "SE.ADT.LITR.ZS":      "Taux d'alphabétisation adultes (%)",
    "SE.PRM.NENR":         "Taux net scolarisation primaire (%)",
    "SH.DYN.MORT":         "Mortalité infantile (pour 1000 naissances)",
    "GC.DOD.TOTL.GD.ZS":   "Dette publique (% PIB)",
    "BN.CAB.XOKA.GD.ZS":   "Solde compte courant (% PIB)",
}


def fetch_worldbank(source: dict) -> list[dict]:
    """
    Fetch World Bank indicator series for Senegal, return text chunks.
    One chunk per indicator.
    """
    cfg = source.get("api_config", {})
    base_url = cfg.get("base_url", "https://api.worldbank.org/v2")
    country = cfg.get("country_code", "SN")
    indicators = cfg.get("indicators", list(INDICATOR_LABELS.keys()))

    chunks = []
    for i, indicator in enumerate(indicators):
        url = f"{base_url}/country/{country}/indicator/{indicator}"
        params = {"format": "json", "per_page": 60, "mrv": 20}
        try:
            resp = httpx.get(url, params=params, timeout=30, follow_redirects=True)
            resp.raise_for_status()
            payload = resp.json()
        except Exception as e:
            logger.warning(f"World Bank: failed to fetch {indicator}: {e}")
            continue

        if not isinstance(payload, list) or len(payload) < 2:
            continue

        records = payload[1] or []
        label = INDICATOR_LABELS.get(indicator, indicator)

        yearly: dict[str, str] = {}
        unit = ""
        for rec in records:
            year = rec.get("date", "")
            value = rec.get("value")
            if value is not None:
                yearly[year] = str(round(value, 3))
                unit = rec.get("indicator", {}).get("value", "")

        series_lines = [f"{yr}: {val}" for yr, val in sorted(yearly.items())]
        if not series_lines:
            continue

        text = (
            f"Banque Mondiale — Sénégal — {label}\n"
            f"Indicateur: {indicator}\n"
            + (f"Unité: {unit}\n" if unit else "")
            + f"Série ({min(yearly.keys())}–{max(yearly.keys())}):\n"
            + "\n".join(series_lines)
        )

        chunks.append({
            "text": text,
            "source_id": source["id"],
            "institution": source["institution"],
            "report_name": source["name"],
            "year": source.get("year"),
            "page_number": 0,
            "chunk_index": i,
            "is_table": False,
            "indicator_code": indicator,
            "indicator_label": label,
        })
        logger.debug(f"World Bank: fetched {indicator} — {len(series_lines)} years")

    logger.info(f"World Bank: {len(chunks)} indicator chunks for {country}")
    return chunks
