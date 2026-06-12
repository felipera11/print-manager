import pytest

FILAMENT_TYPE_PAYLOAD = {
    "type": "PLA",
    "brand": "Elegoo",
    "cost_per_kg": 120.0,
}

SPOOL_MODEL_PAYLOAD = {
    "name": "Elegoo 1kg reel",
    "weight_g": 200.0,
}

SPOOL_PAYLOAD = {
    "number": 1,
    "color": "Black",
    "total_weight_g": 1000,
}


@pytest.fixture
def filament_type(client):
    created = client.post("/api/v1/filament-types/", json=FILAMENT_TYPE_PAYLOAD).json()
    yield created
    client.delete(f"/api/v1/filament-types/{created['id']}")


@pytest.fixture
def spool_model(client):
    created = client.post("/api/v1/spool-models/", json=SPOOL_MODEL_PAYLOAD).json()
    yield created
    client.delete(f"/api/v1/spool-models/{created['id']}")


def test_create(client, filament_type, spool_model):
    payload = {**SPOOL_PAYLOAD, "type_id": filament_type["id"], "spool_model_id": spool_model["id"]}
    response = client.post("/api/v1/spools/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["color"] == payload["color"]
    assert data["type_id"] == filament_type["id"]
    assert data["spool_model_id"] == spool_model["id"]
    assert data["remaining_weight_g"] == payload["total_weight_g"] - spool_model["weight_g"]
    assert "id" in data

    client.delete(f"/api/v1/spools/{data['id']}")


def test_list(client, filament_type, spool_model):
    payload = {**SPOOL_PAYLOAD, "type_id": filament_type["id"], "spool_model_id": spool_model["id"]}
    created = client.post("/api/v1/spools/", json=payload).json()

    response = client.get("/api/v1/spools/")
    assert response.status_code == 200
    assert any(spool["id"] == created["id"] for spool in response.json())

    client.delete(f"/api/v1/spools/{created['id']}")


def test_edit(client, filament_type, spool_model):
    payload = {**SPOOL_PAYLOAD, "type_id": filament_type["id"], "spool_model_id": spool_model["id"]}
    created = client.post("/api/v1/spools/", json=payload).json()

    updated_payload = {**payload, "color": "White", "total_weight_g": 700}
    response = client.put(f"/api/v1/spools/{created['id']}", json=updated_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["color"] == "White"
    assert data["remaining_weight_g"] == 700 - spool_model["weight_g"]

    client.delete(f"/api/v1/spools/{created['id']}")


def test_delete(client, filament_type, spool_model):
    payload = {**SPOOL_PAYLOAD, "type_id": filament_type["id"], "spool_model_id": spool_model["id"]}
    created = client.post("/api/v1/spools/", json=payload).json()

    response = client.delete(f"/api/v1/spools/{created['id']}")
    assert response.status_code == 204

    response = client.get(f"/api/v1/spools/{created['id']}")
    assert response.status_code == 404


def test_not_found(client):
    assert client.get("/api/v1/spools/999999").status_code == 404
    payload = {**SPOOL_PAYLOAD, "type_id": 1, "spool_model_id": 1}
    assert client.put("/api/v1/spools/999999", json=payload).status_code == 404
    assert client.delete("/api/v1/spools/999999").status_code == 404


def test_suggest_returns_correct_spool(client, filament_type, spool_model):
    too_small = client.post(
        "/api/v1/spools/",
        json={
            **SPOOL_PAYLOAD,
            "type_id": filament_type["id"],
            "spool_model_id": spool_model["id"],
            "number": 1,
            "total_weight_g": 300 + spool_model["weight_g"],
        },
    ).json()
    best_match = client.post(
        "/api/v1/spools/",
        json={
            **SPOOL_PAYLOAD,
            "type_id": filament_type["id"],
            "spool_model_id": spool_model["id"],
            "number": 2,
            "total_weight_g": 500 + spool_model["weight_g"],
        },
    ).json()
    larger = client.post(
        "/api/v1/spools/",
        json={
            **SPOOL_PAYLOAD,
            "type_id": filament_type["id"],
            "spool_model_id": spool_model["id"],
            "number": 3,
            "total_weight_g": 800 + spool_model["weight_g"],
        },
    ).json()

    response = client.get("/api/v1/spools/suggest", params={"weight_g": 400, "type_id": filament_type["id"]})
    assert response.status_code == 200
    data = response.json()

    assert data[0]["id"] == best_match["id"]
    assert all(spool["id"] != too_small["id"] for spool in data)

    client.delete(f"/api/v1/spools/{too_small['id']}")
    client.delete(f"/api/v1/spools/{best_match['id']}")
    client.delete(f"/api/v1/spools/{larger['id']}")
