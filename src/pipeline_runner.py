# Pipeline runner - ARGPARSE CLI fjärrkontroll

import argparse
import logging
import time
import sys

# Importera mina motorer(scriptens funktioner)
from src.silver.etl_job import run_silver_batch
from src.gold.etl_job_gold import run_gold_etl


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


# Bygger hela menyn för fjärrkontrollen och dess kommandon att använda som CLI kommandon.
def build_parser() -> argparse.ArgumentParser:
    """Building CLI-menu for your remote"""
    parser = argparse.ArgumentParser(
        prog="IoT Data Platform Runner",
        description="Remote control to run batch jobs in Silver and Gold layer",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--layer",
        type=str,
        choices=["silver", "gold", "all"],
        required=True,
        help="Choose which layer that should be run: 'silver', 'gold', or 'all' for the entire pipeline",
    )

    return parser


# Main funktionen som körs beroende på 'val'
def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    logger.info(f"Starting pipeline runner. Selected mode {args.layer.upper()}")
    start_time = time.time()

    try:
        # KÖRA SILVER LAYER
        if args.layer in ["silver", "all"]:
            logger.info("=== RUNNING SILVER LAYER! (CLEANING & FILTERING) ===")
            run_silver_batch()

        # KÖRA GOLD LAYER
        if args.layer in ["gold", "all"]:
            logger.info("=== RUNNING GOLD LAYER (STAR SCHEMA UPSERT) ===")
            run_gold_etl()

        end_time = time.time()
        logger.info(
            f"Pipeline finished successfully in {round(end_time - start_time, 2)} seconds!"
        )
        return 0  # <-- 0 är Success i 'terminal-speak'

    except Exception as e:
        logger.error(f"Pipeline failed. Reason: {e}")
        return 1  # <--- 1 eller högre är Error i 'terminal-speak'


if __name__ == "__main__":
    sys.exit(main())
