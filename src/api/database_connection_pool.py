# Connection pool. Se docs/module_overview_api_core.md för docs
from psycopg_pool import ConnectionPool
from src.config.db_config import get_dsn
import logging

logger = logging.getLogger(__name__)

# Global variabel för vår pool (Startar helt empty)
pool = None


# Öppnar vår "pool" och låter minst 2st "bada i poolen" och max 10st får "bada" samtidigt
def init_db_pool():
    """Starting connection pool when FastAPI starts"""
    global pool
    logger.info("Starting database connection pool..")
    # min_size=2 betyder att vi alltid har 2 uppkopplingar redo. max_size=10 är taket.
    pool = ConnectionPool(conninfo=get_dsn(), min_size=2, max_size=10)


# Stänger vår "Pool" för dagen när FastAPI stängs ner. Ingen får bada längre
def close_db_pool():
    """Closes connection pool when FastAPI shuts down"""
    global pool
    if pool is not None:
        logger.info("Closing the DB connection pool..")
        pool.close()


# Hämtar databas connection (REFACTORED för säkerhet!!)
def get_db_connection():
    """
    Dependency Injection for FastAPI.
    Borrows a connection from the pool manually and guarantees via finally that it will be returned,
    regardless if the API crashes.
    """
    if pool is None:
        raise RuntimeError("Database pool did not initialize.")
    # Ber poolen ge mig en specifik anslutning
    conn = pool.getconn()
    try:
        # Yield innebär: Stanna upp här, skicka conn till endpointen i main.py
        yield conn
    finally:
        # När endpoint är klar eller kraschar fortsätter koden här.
        # Jag TVINGAR tillbaka connection i poolen, det här förhindrar memory leaks.
        pool.putconn(conn)
