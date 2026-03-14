# API endpoint tests using pytest + FastAPI TestClient
# Uses Dependency Override to mock the database — no real DB needed to run these tests
from fastapi.testclient import TestClient
from src.api.main import app
from src.api.database_connection_pool import get_db_connection

client = TestClient(app)


# --- MOCK DATABASE ---
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
        pass

    def fetchone(self):
        return (1,)

    def fetchall(self):
        return [MOCK_ROW]

    def __enter__(self):
        return self

    def __exit__(self, *_):
        pass


class MockConnection:
    def cursor(self, row_factory=None):
        return MockCursor()


def override_get_db_connection():
    """Swaps real DB connection for MockConnection during tests."""
    yield MockConnection()


app.dependency_overrides[get_db_connection] = override_get_db_connection

# --- TESTS ---


def test_read_root():
    """Root endpoint should return 200 and a welcome message."""
    response = client.get("/")
    assert response.status_code == 200
    assert "Message" in response.json()


def test_health_check_db_connected():
    """Mock DB always works — health should report connected."""
    response = client.get("/health")
    data = response.json()

    assert data["status"] == "healthy"
    assert data["database"] == "connected"


def test_get_sensor_data_returns_200():
    """Sensor endpoint should return 200."""
    response = client.get("/api/v1/sensors")
    assert response.status_code == 200


def test_get_sensor_data_schema_validation():
    """Pydantic must accept the mock row — all fields correct types."""
    response = client.get("/api/v1/sensors")
    data = response.json()

    row = data["data"][0]
    assert row["silver_id"] == 1
    assert row["engine_id"] == "test-uuid-123"
    assert row["appliance_type"] == "washing_machine"
    assert row["run_hours"] == 100.5
    assert row["is_valid"] is True  # --- TESTS ---


def test_read_root():
    """Root endpoint should return 200 and a welcome message."""
    response = client.get("/")
    assert response.status_code == 200
    assert "Message" in response.json()


def test_health_check_db_connected():
    """Mock DB always works — health should report connected."""
    response = client.get("/health")
    data = response.json()

    assert data["status"] == "healthy"
    assert data["database"] == "connected"


def test_get_sensor_data_returns_200():
    """Sensor endpoint should return 200."""
    response = client.get("/api/v1/sensors")
    assert response.status_code == 200


def test_get_sensor_data_schema_validation():
    """Pydantic must accept the mock row — all fields correct types."""
    response = client.get("/api/v1/sensors")
    data = response.json()

    row = data["data"][0]
    assert row["silver_id"] == 1
    assert row["engine_id"] == "test-uuid-123"
    assert row["appliance_type"] == "washing_machine"
    assert row["run_hours"] == 100.5
    assert row["is_valid"] is True
