"""
IMF World Economic Outlook API fetcher.
Converts WEO indicator time-series for Senegal into indexable text chunks.

API docs: https://www.imf.org/external/datamapper/api/v1
"""

import httpx
from loguru import logger

INDICATOR_LABELS = {
    "NGDP_RPCH": "Croissance du PIB réel (%)",
    "NGDPDPC": "PIB par habitant (USD courants)",
    "PCPIPCH": "Inflation IPC (variation annuelle %)",
    "BCA_NGDPD": "Solde du compte courant (% PIB)",
    "GGXCNL_NGDP": "Solde budgétaire (% PIB)",
    "GGXWDG_NGDP": "Dette publique brute (% PIB)",
    "LUR": "Taux de chômage (%)",
    "PPPGDP": "PIB PPA (milliards USD)",
    "NID_NGDP": "Investissement total (% PIB)",
}


def fetch_imf_weo(source: dict) -> list[dict]:
    """
    Fetch WEO time-series for Senegal, return list of text chunks ready for indexing.
    One chunk per indicator containing its full historical + forecast series.
    """
    cfg = source.get("api_config", {})
    base_url = cfg.get("base_url", "https://www.imf.org/external/datamapper/api/v1")
    country = cfg.get("country_code", "SEN")
    indicators = cfg.get("indicators", list(INDICATOR_LABELS.keys()))

    chunks = []
    for indicator in indicators:
        url = f"{base_url}/{indicator}/{country}"
        try:
            resp = httpx.get(url, timeout=30, follow_redirects=True)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            logger.warning(f"IMF WEO: failed to fetch {indicator}: {e}")
            continue

        values: dict = data.get("values", {}).get(indicator, {}).get(country, {})
        if not values:
            logger.warning(f"IMF WEO: no data for {indicator}/{country}")
            continue

        label = INDICATOR_LABELS.get(indicator, indicator)
        series_lines = [f"{year}: {val}" for year, val in sorted(values.items()) if val is not None]
        if not series_lines:
            continue

        text = (
            f"IMF WEO — Sénégal — {label}\n"
            f"Indicateur: {indicator}\n"
            f"Série temporelle ({sorted(values.keys())[0]}–{sorted(values.keys())[-1]}):\n"
            + "\n".join(series_lines)
        )

        chunks.append(
            {
                "text": text,
                "source_id": source["id"],
                "institution": source["institution"],
                "report_name": source["name"],
                "year": source.get("year"),
                "page_number": 0,
                "chunk_index": indicators.index(indicator),
                "is_table": False,
                "indicator_code": indicator,
                "indicator_label": label,
            }
        )
        logger.debug(f"IMF WEO: fetched {indicator} — {len(series_lines)} data points")

    logger.info(f"IMF WEO: {len(chunks)} indicator chunks fetched for {country}")
    return chunks
