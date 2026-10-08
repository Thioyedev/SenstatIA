from ingestion.api_fetchers.faostat import fetch_faostat
from ingestion.api_fetchers.ilostat import fetch_ilostat
from ingestion.api_fetchers.imf_weo import fetch_imf_weo
from ingestion.api_fetchers.worldbank import fetch_worldbank

__all__ = ["fetch_imf_weo", "fetch_ilostat", "fetch_faostat", "fetch_worldbank"]
