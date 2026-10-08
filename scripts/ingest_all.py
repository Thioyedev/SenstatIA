from dotenv import load_dotenv

load_dotenv()

from ingestion.pipeline import run_ingestion

if __name__ == "__main__":
    run_ingestion()
