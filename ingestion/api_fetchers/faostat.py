"""
FAO FAOSTAT API fetcher.
Fetches agricultural production and food balance data for Senegal.

API docs: https://fenixservices.fao.org/faostat/api/v1
Domains: QCL (production), TCL (trade), FBS (food balance), PP (prices)
"""
import httpx
from loguru import logger

DOMAIN_LABELS = {
    "QCL": "Production agricole (cultures et bétail)",
    "TCL": "Commerce alimentaire (importations et exportations)",
    "FBS": "Bilan alimentaire (disponibilité par habitant)",
    "PP":  "Prix agricoles",
}

# Key items to fetch per domain (FAO item codes)
DOMAIN_ITEMS = {
    "QCL": ["27", "56", "79", "101", "103", "116", "135", "156", "176", "191", "197", "217"],
    "TCL": [],   # fetch all — filter to top items by value
    "FBS": ["2901"],  # aggregate food supply
    "PP":  ["15", "27", "56", "79"],
}


def fetch_faostat(source: dict) -> list[dict]:
    """
    Fetch FAOSTAT data for Senegal, return indexable text chunks.
    One chunk per domain containing a summary of recent data.
    """
    cfg = source.get("api_config", {})
    base_url = cfg.get("base_url", "https://fenixservices.fao.org/faostat/api/v1")
    country_code = cfg.get("country_code", "272")  # FAO code for Senegal
    domains = cfg.get("domains", ["QCL", "FBS"])

    chunks = []
    for i, domain in enumerate(domains):
        url = f"{base_url}/fr/data/{domain}"
        params = {
            "area": country_code,
            "year": "2018,2019,2020,2021,2022,2023",
            "output_type": "objects",
        }
        if DOMAIN_ITEMS.get(domain):
            params["item"] = ",".join(DOMAIN_ITEMS[domain])

        try:
            resp = httpx.get(url, params=params, timeout=60, follow_redirects=True)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            logger.warning(f"FAOSTAT: failed to fetch domain {domain}: {e}")
            continue

        records = data.get("data", [])
        if not records:
            logger.warning(f"FAOSTAT: no records for domain {domain}/Senegal")
            continue

        label = DOMAIN_LABELS.get(domain, domain)

        # Build readable lines: "Item (unit), Year: Value"
        lines = []
        for rec in records[:200]:  # cap to avoid oversized chunks
            item = rec.get("Item", "")
            year = rec.get("Year", "")
            value = rec.get("Value", "")
            unit = rec.get("Unit", "")
            if item and year and value:
                lines.append(f"{item} ({unit}), {year}: {value}")

        if not lines:
            continue

        text = (
            f"FAO FAOSTAT — Sénégal — {label}\n"
            f"Domaine: {domain}\n"
            f"Données récentes:\n" + "\n".join(lines)
        )

        chunks.append({
            "text": text,
            "source_id": source["id"],
            "institution": source["institution"],
            "report_name": source["name"],
            "year": source.get("year"),
            "page_number": 0,
            "chunk_index": i,
            "is_table": True,
            "fao_domain": domain,
        })
        logger.debug(f"FAOSTAT: domain {domain} — {len(lines)} records")

    logger.info(f"FAOSTAT: {len(chunks)} domain chunks fetched for Senegal")
    return chunks
