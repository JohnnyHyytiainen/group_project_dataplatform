##Som data enginner vill vi ha en fil för att ladda in miljövariabler för att f följa SOC( Seperation of concerns)

# Bryt ut det som finns i worker.py när det gäller databasen

from dotenv import load_dotenv
import os

load_dotenv()


def get_dsn() -> str:

    user = os.getenv("DB_USER")
    pwd = os.getenv("DB_PASSWORD")
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5439")
    db = os.getenv("DB_NAME")

    missing = [
        k
        for k, v in {"DB_USER": user, "DB_PASSWORD": pwd, "DB_NAME": db}.items()
        if not v
    ]

    if missing:
        raise RuntimeError(f"Missing env vars: {','.join(missing)}")

    return f"postgresql://{user}:{pwd}@{host}:{port}/{db}"
