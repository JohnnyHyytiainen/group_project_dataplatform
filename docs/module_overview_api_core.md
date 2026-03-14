 # Module Overview: API Core & Connection Pooling
*Written 12/03/2026 by Johnny*

This document describes the architecture, performance optimizations, and security layers of our FastAPI build for the Silver layer.

## 1. Performance: Why Connection Pooling? `database_connection_pool.py`

Establishing a connection to a PostgreSQL database over a network requires an asynchronous 'handshake'. If 100 users (or a dashboard) call our API at the same time and create 100 new handshakes, the database will crash. This is not an industry standard.

To solve this, we use `psycopg_pool.ConnectionPool`:

* **Mechanics:** When FastAPI starts, we open a predetermined number of connections in advance (e.g. `min_size=2`, `max_size=10`)

* **Flow:** When an endpoint is called, it 'borrows' a ready connection from the pool, executes its query at lightning speed, and then returns it via the `get_db_connection()` function.

* **Lifecycle Management:** We hook up the pool via FastAPI's `@asynccontextmanager lifespan` in `main.py`. This ensures that the pool is started correctly before the API receives traffic, and shuts down safely (prevents memory leaks) when the server is shut down.

## 2. Architecture & Security `main.py`

Our API is built with a *Defense in Depth* mindset to ensure high technical quality and protect our data.

### Security Layers

1. **DDoS Protection via Pagination:** Our `/api/v1/sensors` endpoint has built in limits `limit: int = Query(100, ge=1, le=1000)` This ensures that no one can accidentally or maliciously request millions of rows at once and crash the API.

2. **SQL Injection Protection:** We never hardcode user input into our SQL strings. By using `psycopg`s parameterized queries (`%s` and the `params` list), all input is automatically sanitized. If someone submits malicious SQL code, it is simply interpreted as a harmless text string by the database.

3. **CORS Middleware:** Prepared for future integrations. By configuring CORS, we allow separate frontend applications (ex, a Streamlit Dashboard on port 8501) to retrieve data from our API without being blocked by browser security rules.

### Smart Code Patterns

* **Dependency Injection `Depends(get_db_connection)`:** Makes our code extremely modular. The endpoint doesn't need to worry about *how* it gets a database connection, it just asks for one. This also makes it easy to replace the real database with a mocked version when writing unit tests.

* **Row Formatting `dict_row`:** The default behavior of `psycopg` is to return data as anonymous lists (Tuples). By enabling `row_factory=dict_row`, the database rows are automatically converted to Python Dictionaries (with keys like `rpm` and `engine_temp`) This allows FastAPI to seamlessly translate the response into JSON.

* **Dynamic SQL (`WHERE 1=1`):** By starting our query with `WHERE 1=1`, we avoid writing complex `if/else` logic to handle which filter comes first. We can easily add `AND [condition]` dynamically based on what the user submits.

## Running Instructions

To start the API in development mode with "hot reload" the server automatically restarts when the code changes, run:

```bash
uv run uvicorn src.api.main:app --reload

```
Then go to `http://localhost:8000/docs` in your browser to explore the auto generated swagger documentation.

---