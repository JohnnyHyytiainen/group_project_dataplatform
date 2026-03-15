# API endpoint tests
# Uses Dependency Override to mock the database —> no real DB needed to run these tests
from fastapi.testclient import TestClient
from src.api.main import app
from src.api.database_connection_pool import get_db_connection

client = TestClient(app)


# --- FAKE DATABASE SETUP ---
# Instead of connecting to the real postgres, we just return hardcoded data
# This way anyone can run the tests without starting docker compose

MOCK_ROW = {
    "silver_id": 1,
    "engine_id": "test-uuid-123",
    "appliance_type": "washing_machine",
    "timestamp": "2024-01-01T12:00:00",
    "run_hours": 100.5,
    "location": "Test City",
    "rpm": 1200.0,
    "engine_temp": 45.0,
    "vibration_hz": 5.5,
    "is_valid": True,
    "silver_processed_at": "2024-01-01T12:05:00",
}


class MockCursor:
    def execute(self, query, params=None):
        pass  # we dont actually run any SQL here

    def fetchone(self):
        return (1,)  # Used by /health endpoint —> simulates SELECT 1

    def fetchall(self):
        return [MOCK_ROW]  # pretend the database returned our test row

    def __enter__(self):
        return self  # # needed so "with cursor() as cur:" doesnt crash

    def __exit__(self, *_):
        pass  # nothing to clean up since its all fake


class MockConnection:
    def cursor(self, row_factory=None):
        return MockCursor()  # give back our fake cursor

    def close(self):
        pass  # Mimics real connection cleanup


def override_get_db_connection():
    """Yield so FastAPI can still run cleanup after the test finishes"""
    mock_conn = MockConnection()
    try:
        yield mock_conn  # give the connection to FastAPI
    finally:
        mock_conn.close()  # This needs to run after the test finishes


# Tell FastAPI to use the mock instead of the real pool
app.dependency_overrides[get_db_connection] = override_get_db_connection


# --- TESTS ---


def test_read_root():
    """Just checking the root endpoint doesnt crash"""
    response = client.get("/")
    assert response.status_code == 200
    assert "Message" in response.json()


def test_health_check_db_connected():
    """Mock DB always works —> health should report connected."""
    response = client.get("/health")
    data = response.json()

    assert data["status"] == "healthy"
    assert data["database"] == "connected"


def test_get_sensor_data_returns_200():
    """Sensor endpoint should return 200."""
    response = client.get("/api/v1/sensors")
    assert response.status_code == 200


def test_get_sensor_data_schema_validation():
    """Pydantic must accept the mock row —> all fields correct types."""
    response = client.get("/api/v1/sensors")
    data = response.json()

    row = data["data"][0]
    assert row["silver_id"] == 1
    assert row["engine_id"] == "test-uuid-123"
    assert row["appliance_type"] == "washing_machine"
    assert row["run_hours"] == 100.5
    assert row["is_valid"] is True


def test_get_sensor_data_filter_appliance_type():
    """Pass a filter and check it shows up in the metadata"""
    response = client.get("/api/v1/sensors?appliance_type=washing_machine")
    data = response.json()

    assert response.status_code == 200
    assert data["metadata"]["filters_applied"]["appliance_type"] == "washing_machine"


def test_get_sensor_data_filter_is_valid():
    """Making sure the string "true" in the url gets parsed as a real boolean"""
    response = client.get("/api/v1/sensors?is_valid=true")
    data = response.json()

    assert response.status_code == 200
    assert data["metadata"]["filters_applied"]["is_valid"] is True


def test_get_sensor_data_limit_too_high():
    """Limit has a max of 1000, anything above should give a 422 error"""
    response = client.get("/api/v1/sensors?limit=9999")
    assert response.status_code == 422


def test_get_sensor_data_negative_skip():
    """Skip cant be negative, fastapi should catch this automatically"""
    response = client.get("/api/v1/sensors?skip=-1")
    assert response.status_code == 422


def teardown_module():
    """remove the fake db override after all tests are done otherwise it could affect other test files"""
    app.dependency_overrides.clear()
