import camelot
import pandas as pd
from loguru import logger

def extract_tables_from_pdf(pdf_path: str) -> list[dict]:
    """
    Extrait les tableaux d'un PDF via camelot.
    Retourne liste de {page, table_index, markdown, dataframe}
    """
    tables_data = []

    try:
        tables = camelot.read_pdf(pdf_path, pages='all', flavor='lattice')
        logger.info(f"{len(tables)} tableaux trouvés dans {pdf_path}")

        for i, table in enumerate(tables):
            df = table.df
            # Première ligne = header
            df.columns = df.iloc[0]
            df = df[1:].reset_index(drop=True)

            tables_data.append({
                "page": table.page,
                "table_index": i,
                "markdown": df.to_markdown(index=False),
                "shape": df.shape,
                "accuracy": table.accuracy
            })
    except Exception as e:
        logger.warning(f"camelot échoué : {e} → skip tables")

    return tables_data
