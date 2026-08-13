"""
Tests the API layer against a mocked database connection, so the
suite runs without a live Postgres instance. Each test overrides the
`get_db` FastAPI dependency with a fake connection/cursor whose
`fetchone`/`fetchall` return canned rows, and asserts on status codes
and response shape.
"""
# from datetime import date
# from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from api.database import get_db
from api.main import app


class FakeCursor:
    def __init__(self, rows):
        self._rows = rows

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def execute(self, query, params=None):
        pass

    def fetchall(self):
        return self._rows

    def fetchone(self):
        return self._rows[0] if self._rows else None


class FakeConnection:
    def __init__(self, rows):
        self._rows = rows

    def cursor(self):
        return FakeCursor(self._rows)


def override_db(rows):
    def _get_db():
        yield FakeConnection(rows)

    return _get_db


@pytest.fixture(autouse=True)
def clear_overrides():
    yield
    app.dependency_overrides.clear()


def test_health_check():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_indicators_list_is_static_and_has_five_entries():
    client = TestClient(app)
    response = client.get("/indicators")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 5
    ids = {item["id"] for item in data}
    assert "exchange_rates" in ids
    assert "ngx_asi" in ids


def test_latest_rates_success():
    rows = [("USD", "NGN", 1530.25, "2026-06-30")]
    app.dependency_overrides[get_db] = override_db(rows)
    client = TestClient(app)
    response = client.get("/rates/latest")
    assert response.status_code == 200
    body = response.json()
    assert body[0]["base_currency"] == "USD"
    assert body[0]["rate"] == 1530.25


def test_latest_rates_not_found_returns_404():
    app.dependency_overrides[get_db] = override_db([])
    client = TestClient(app)
    response = client.get("/rates/latest")
    assert response.status_code == 404


def test_latest_rates_invalid_base_returns_400():
    app.dependency_overrides[get_db] = override_db([])
    client = TestClient(app)
    response = client.get("/rates/latest?base=ZZZ")
    assert response.status_code == 400


def test_rate_history_invalid_date_range_returns_400():
    app.dependency_overrides[get_db] = override_db([])
    client = TestClient(app)
    response = client.get(
        "/rates/history?base=USD&start=2026-06-30&end=2026-01-01"
    )
    assert response.status_code == 400


def test_inflation_series_success():
    rows = [("NG", 2024, 22.4), ("NG", 2025, 24.1)]
    app.dependency_overrides[get_db] = override_db(rows)
    client = TestClient(app)
    response = client.get("/inflation?country=NG")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2
    assert body[1]["year"] == 2025


def test_purchasing_power_insight_success():
    rows = [(2020, 13.2, 1.132, 883392.23)]
    app.dependency_overrides[get_db] = override_db(rows)
    client = TestClient(app)
    response = client.get("/insights/purchasing-power")
    assert response.status_code == 200
    body = response.json()
    assert body[0]["real_value_of_1m_naira"] == 883392.23


def test_returns_comparison_start_after_end_returns_400():
    app.dependency_overrides[get_db] = override_db([])
    client = TestClient(app)
    response = client.get(
        "/insights/returns-comparison?start=2026-06-01&end=2026-01-01"
    )
    assert response.status_code == 400


def test_fx_volatility_success():
    rows = [("USD", "2026-01-14", 1540.0, 3.05)]
    app.dependency_overrides[get_db] = override_db(rows)
    client = TestClient(app)
    response = client.get("/insights/fx-volatility?base=USD")
    assert response.status_code == 200
    body = response.json()
    assert body[0]["rolling_30d_annualized_volatility_pct"] == 3.05


def test_fx_volatility_invalid_base_returns_400():
    app.dependency_overrides[get_db] = override_db([])
    client = TestClient(app)
    response = client.get("/insights/fx-volatility?base=ZZZ")
    assert response.status_code == 400


def test_gold_ngn_success():
    rows = [("2026-01-14", 2090.0, 1540.0, 3218600.0, 103480.32)]
    app.dependency_overrides[get_db] = override_db(rows)
    client = TestClient(app)
    response = client.get("/insights/gold-ngn")
    assert response.status_code == 200
    body = response.json()
    assert body[0]["gold_price_ngn_per_gram"] == 103480.32


def test_ngx_drawdown_success():
    rows = [("2026-01-14", 103200.0, 103200.0, 0.0)]
    app.dependency_overrides[get_db] = override_db(rows)
    client = TestClient(app)
    response = client.get("/insights/ngx-drawdown")
    assert response.status_code == 200
    body = response.json()
    assert body[0]["drawdown_from_peak_pct"] == 0.0


def test_annual_summary_success():
    rows = [(2026, 20.5, 16.0, 1540.0, None, 2090.0, None, 103200.0, None)]
    app.dependency_overrides[get_db] = override_db(rows)
    client = TestClient(app)
    response = client.get("/insights/annual-summary")
    assert response.status_code == 200
    body = response.json()
    assert body[0]["year"] == 2026
    assert body[0]["naira_depreciation_yoy_pct"] is None


def test_annual_summary_invalid_year_range_returns_400():
    app.dependency_overrides[get_db] = override_db([])
    client = TestClient(app)
    response = client.get("/insights/annual-summary?start_year=2026&end_year=2020")
    assert response.status_code == 400


def test_asset_correlation_success():
    rows = [(-1.0, -1.0, 1.0, 2)]
    app.dependency_overrides[get_db] = override_db(rows)
    client = TestClient(app)
    response = client.get("/insights/asset-correlation")
    assert response.status_code == 200
    body = response.json()
    assert body["months_used"] == 2


def test_asset_correlation_not_found_returns_404():
    app.dependency_overrides[get_db] = override_db([])
    client = TestClient(app)
    response = client.get("/insights/asset-correlation")
    assert response.status_code == 404
