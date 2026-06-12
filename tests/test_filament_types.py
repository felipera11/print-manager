FILAMENT_TYPE_PAYLOAD = {
    "type": "PLA",
    "brand": "Elegoo",
    "cost_per_kg": 120.0,
}


def test_create(client):
    response = client.post("/api/v1/filament-types/", json=FILAMENT_TYPE_PAYLOAD)
    assert response.status_code == 201
    data = response.json()
    assert data["type"] == FILAMENT_TYPE_PAYLOAD["type"]
    assert data["brand"] == FILAMENT_TYPE_PAYLOAD["brand"]
    assert data["cost_per_kg"] == FILAMENT_TYPE_PAYLOAD["cost_per_kg"]
    assert "id" in data

    client.delete(f"/api/v1/filament-types/{data['id']}")


def test_list(client):
    created = client.post("/api/v1/filament-types/", json=FILAMENT_TYPE_PAYLOAD).json()

    response = client.get("/api/v1/filament-types/")
    assert response.status_code == 200
    assert any(filament_type["id"] == created["id"] for filament_type in response.json())

    client.delete(f"/api/v1/filament-types/{created['id']}")


def test_edit(client):
    created = client.post("/api/v1/filament-types/", json=FILAMENT_TYPE_PAYLOAD).json()

    updated_payload = {**FILAMENT_TYPE_PAYLOAD, "type": "PETG", "cost_per_kg": 150.0}
    response = client.put(f"/api/v1/filament-types/{created['id']}", json=updated_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "PETG"
    assert data["cost_per_kg"] == 150.0

    client.delete(f"/api/v1/filament-types/{created['id']}")


def test_delete(client):
    created = client.post("/api/v1/filament-types/", json=FILAMENT_TYPE_PAYLOAD).json()

    response = client.delete(f"/api/v1/filament-types/{created['id']}")
    assert response.status_code == 204

    response = client.get(f"/api/v1/filament-types/{created['id']}")
    assert response.status_code == 404


def test_not_found(client):
    assert client.get("/api/v1/filament-types/999999").status_code == 404
    assert client.put("/api/v1/filament-types/999999", json=FILAMENT_TYPE_PAYLOAD).status_code == 404
    assert client.delete("/api/v1/filament-types/999999").status_code == 404
