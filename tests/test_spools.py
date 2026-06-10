import pytest

FILAMENT_TYPE_PAYLOAD = {
    "name": "PLA",
    "temp_min": 190,
    "temp_max": 220,
}

SPOOL_PAYLOAD = {
    "number": 1,
    "brand": "eSun",
    "color": "Black",
    "total_weight_g": 1000,
    "remaining_weight_g": 750,
    "cost_per_kg": 120.0,
}


@pytest.fixture
def filament_type(client):
    created = client.post("/api/v1/filament-types/", json=FILAMENT_TYPE_PAYLOAD).json()
    yield created
    client.delete(f"/api/v1/filament-types/{created['id']}")


def test_create(client, filament_type):
    payload = {**SPOOL_PAYLOAD, "type_id": filament_type["id"]}
    response = client.post("/api/v1/spools/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["brand"] == payload["brand"]
    assert data["type_id"] == filament_type["id"]
    assert "id" in data

    client.delete(f"/api/v1/spools/{data['id']}")


def test_list(client, filament_type):
    payload = {**SPOOL_PAYLOAD, "type_id": filament_type["id"]}
    created = client.post("/api/v1/spools/", json=payload).json()

    response = client.get("/api/v1/spools/")
    assert response.status_code == 200
    assert any(spool["id"] == created["id"] for spool in response.json())

    client.delete(f"/api/v1/spools/{created['id']}")


def test_edit(client, filament_type):
    payload = {**SPOOL_PAYLOAD, "type_id": filament_type["id"]}
    created = client.post("/api/v1/spools/", json=payload).json()

    updated_payload = {**payload, "color": "White", "remaining_weight_g": 500}
    response = client.put(f"/api/v1/spools/{created['id']}", json=updated_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["color"] == "White"
    assert data["remaining_weight_g"] == 500

    client.delete(f"/api/v1/spools/{created['id']}")


def test_delete(client, filament_type):
    payload = {**SPOOL_PAYLOAD, "type_id": filament_type["id"]}
    created = client.post("/api/v1/spools/", json=payload).json()

    response = client.delete(f"/api/v1/spools/{created['id']}")
    assert response.status_code == 204

    response = client.get(f"/api/v1/spools/{created['id']}")
    assert response.status_code == 404


def test_not_found(client):
    assert client.get("/api/v1/spools/999999").status_code == 404
    payload = {**SPOOL_PAYLOAD, "type_id": 1}
    assert client.put("/api/v1/spools/999999", json=payload).status_code == 404
    assert client.delete("/api/v1/spools/999999").status_code == 404


def test_suggest_returns_correct_spool(client, filament_type):
    too_small = client.post(
        "/api/v1/spools/",
        json={**SPOOL_PAYLOAD, "type_id": filament_type["id"], "number": 1, "remaining_weight_g": 300},
    ).json()
    best_match = client.post(
        "/api/v1/spools/",
        json={**SPOOL_PAYLOAD, "type_id": filament_type["id"], "number": 2, "remaining_weight_g": 500},
    ).json()
    larger = client.post(
        "/api/v1/spools/",
        json={**SPOOL_PAYLOAD, "type_id": filament_type["id"], "number": 3, "remaining_weight_g": 800},
    ).json()

    response = client.get("/api/v1/spools/suggest", params={"weight_g": 400, "type_id": filament_type["id"]})
    assert response.status_code == 200
    data = response.json()

    assert data[0]["id"] == best_match["id"]
    assert all(spool["id"] != too_small["id"] for spool in data)

    client.delete(f"/api/v1/spools/{too_small['id']}")
    client.delete(f"/api/v1/spools/{best_match['id']}")
    client.delete(f"/api/v1/spools/{larger['id']}")
