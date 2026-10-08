"""
ILO ILOSTAT API fetcher.
Fetches labour market indicators for Senegal and returns indexable text chunks.

API docs: https://rplumber.ilo.org/data/indicator/
"""

import httpx
from loguru import logger

INDICATOR_LABELS = {
    "EMP_TEMP_SEX_AGE_STE_NB": "Emploi total par sexe, âge et statut",
    "UNE_TUNE_SEX_AGE_NB": "Chômage total par sexe et âge",
    "EAP_TEAP_SEX_AGE_NB": "Population active par sexe et âge",
    "EMP_2EMP_SEX_AGE_NB": "Emploi informel par sexe et âge",
    "SDG_0111_SEX_RT": "Taux de pauvreté laborieuse (ODD 1.1.1)",
}

# Aggregation codes to request (total, both sexes, all ages)
DEFAULT_PARAMS = {
    "sex": "SEX_T",
    "classif1": "AGE_AGGREGATE_TOTAL",
    "timefrom": "2010",
}


def fetch_ilostat(source: dict) -> list[dict]:
    """
    Fetch ILOSTAT time-series for Senegal, return list of text chunks.
    One chunk per indicator.
    """
    cfg = source.get("api_config", {})
    base_url = cfg.get("base_url", "https://rplumber.ilo.org/data/indicator/")
    country = cfg.get("country_code", "SEN")
    indicators = cfg.get("indicators", list(INDICATOR_LABELS.keys()))

    chunks = []
    for i, indicator in enumerate(indicators):
        params = {
            "id": indicator,
            "ref_area": country,
            **DEFAULT_PARAMS,
            "type": "label",
            "lang": "fr",
        }
        try:
            resp = httpx.get(base_url, params=params, timeout=40, follow_redirects=True)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            logger.warning(f"ILOSTAT: failed to fetch {indicator}: {e}")
            continue

        observations = data.get("data", [])
        if not observations:
            logger.warning(f"ILOSTAT: no observations for {indicator}/{country}")
            continue

        label = INDICATOR_LABELS.get(indicator, indicator)

        # Group by year, pick total values
        yearly: dict[str, str] = {}
        for obs in observations:
            year = str(obs.get("time", ""))[:4]
            value = obs.get("obs_value")
            unit = obs.get("measure", "")
            if year and value is not None:
                yearly[year] = f"{value} {unit}".strip()

        series_lines = [f"{yr}: {val}" for yr, val in sorted(yearly.items())]
        if not series_lines:
            continue

        text = (
            f"OIT ILOSTAT — Sénégal — {label}\n"
            f"Indicateur: {indicator}\n"
            f"Série ({min(yearly.keys())}–{max(yearly.keys())}):\n" + "\n".join(series_lines)
        )

        chunks.append(
            {
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
            }
        )
        logger.debug(f"ILOSTAT: fetched {indicator} — {len(series_lines)} years")

    logger.info(f"ILOSTAT: {len(chunks)} indicator chunks fetched for {country}")
    return chunks
