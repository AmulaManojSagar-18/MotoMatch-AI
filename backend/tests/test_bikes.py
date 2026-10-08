"""API tests for the bike endpoints and catalog integrity."""

from app.data.catalog import BIKE_CATALOG

EXPECTED_MODELS = {
    "Splendor+",
    "Xpulse 200 4V",
    "Ronin 225",
    "R15 V4",
    "Hunter 350",
    "CB350",
    "Speed 400",
    "Pulsar NS400Z",
    "Guerrilla 450",
    "Continental GT 650",
}


def test_catalog_has_exactly_ten():
    """The fixed catalog must contain exactly 10 motorcycles."""
    assert len(BIKE_CATALOG) == 10


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_list_bikes_returns_ten(client):
    resp = client.get("/bikes")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 10


def test_list_bikes_models_match_catalog(client):
    resp = client.get("/bikes")
    models = {bike["model"] for bike in resp.json()}
    assert models == EXPECTED_MODELS


def test_ronin_present(client):
    """TVS Ronin 225 must remain in the catalog."""
    resp = client.get("/bikes")
    models = {bike["model"] for bike in resp.json()}
    assert "Ronin 225" in models


def test_get_single_bike(client):
    resp = client.get("/bikes/1")
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == 1
    assert body["brand"] == "Hero"
    assert body["model"] == "Splendor+"


def test_get_bike_includes_3d_url(client):
    resp = client.get("/bikes/3")
    assert resp.status_code == 200
    assert resp.json()["model_3d_url"] == "/models/tvs-ronin-225.glb"


def test_get_bike_not_found_returns_404(client):
    resp = client.get("/bikes/9999")
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()


def test_response_shape_has_all_fields(client):
    resp = client.get("/bikes/1")
    body = resp.json()
    expected_fields = {
        "id",
        "brand",
        "model",
        "category",
        "price",
        "engine_cc",
        "power_ps",
        "torque_nm",
        "weight_kg",
        "seat_height_mm",
        "fuel_capacity_l",
        "ground_clearance_mm",
        "transmission",
        "abs_type",
        "mileage",
        "model_3d_url",
    }
    assert expected_fields.issubset(body.keys())
