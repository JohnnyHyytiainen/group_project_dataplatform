# Module Overview: API Core, Connection Pooling & Data Contracts
*Written and developed by Indira and Johnny*


This document describes the architecture, performance optimizations, and security layers of our FastAPI build serving the Silver Layer data.

## 1. Performance: Why Connection Pooling? `database_connection_pool.py`
Establishing a connection to a PostgreSQL database over a network requires an asynchronous 'handshake'. If 100 users (or a dashboard) call our API at the same time and create 100 new handshakes, the database will crash. As Kristoffer would note, that is *not* industry standard.

To solve this, we use `psycopg_pool.ConnectionPool`:

* **The Mechanics:** When FastAPI starts, we open a predetermined number of connections in advance.

* **The Flow:** When a user calls an endpoint, they simply 'borrow' a ready connection from the pool, execute their query at lightning speed, and return it.

* **Lifecycle Management:** We manage the pool via FastAPIs `@asynccontextmanager lifespan` in `main.py`. This ensures the pool starts before the API receives traffic and shuts down safely to prevent memory leaks when the server stops.

## 2. Data Contracts & Testing (`api_schemas.py` & Tests)

* **Pydantic Response Models:** Think of the API as a strict contract between Backend and Frontend. Pydantic schemas force FastAPI to double check that we don't accidentally send out the wrong data types (e.g, leaking passwords or sending a string instead of a float). It's also the magic behind our pagination and the auto generated `/docs` page.

* **Dependency Overrides:** In our tests, we don't want to destroy the real database (or fail if the DB is offline). We use dependency overrides to "trick" FastAPI into using a fake, mocked connection that returns hardcoded test data.

## 3. Architecture & Security (`main.py`)
Our API is built with a *Defense in Depth* mindset to protect our data and ensure high technical quality.

### Security Layers
* **DDoS Protection via Pagination:** Our `/api/v1/sensors` endpoint has built-in limits `limit: int = Query(100, ge=1, le=1000)`. This ensures no one can accidentally or maliciously request millions of rows at once and crash the API.

* **Zero SQL Injection:** We never hardcode user input into our SQL strings. By using `psycopg`s parameterized queries (`%s` and the `params` list), all input is automatically sanitized. If someone submits `appliance_type = "dishwasher; DROP TABLE..."`, Postgres simply interprets it as a harmless text string.

* **CORS Middleware:** Prepared for future BI integrations. By configuring CORS, we allow separate frontend applications (like a Streamlit Dashboard on port 8501) to fetch data without being blocked by browser security rules.

### Smart Code Patterns

* **Dependency Injection (`Depends(get_db_connection)`):** Makes our code extremely modular. The endpoint doesn't need to worry about *how* it gets a database connection; it just asks for one. 

* **Row Formatting (`dict_row`):** By default `psycopg` returns data as anonymous tuples. By enabling `row_factory=dict_row`, database rows are automatically converted to Python Dictionaries (with keys like `rpm` and `engine_temp`). This allows FastAPI to seamlessly translate the response into JSON.

* **Dynamic SQL (`WHERE 1=1`):** Starting our query with `WHERE 1=1` is a classic trick(thanks geeksforgeeks!). It allows us to bypass complex `if/else` logic to determine which filter comes first. We just dynamically append `AND [condition]` for every query parameter the user provides.

## Running Instructions
To start the API in development mode with "hot reload" (the server automatically restarts when you change the code), run:

```bash
uv run uvicorn src.api.main:app --reload
```

## Testing Instructions.
To test our API run this command:

```bash
uv run pytest tests/test_api.py -v
```