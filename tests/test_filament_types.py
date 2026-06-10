FILAMENT_TYPE_PAYLOAD = {
    "name": "PLA",
    "temp_min": 190,
    "temp_max": 220,
}


def test_create(client):
    response = client.post("/api/v1/filament-types/", json=FILAMENT_TYPE_PAYLOAD)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == FILAMENT_TYPE_PAYLOAD["name"]
    assert data["temp_min"] == FILAMENT_TYPE_PAYLOAD["temp_min"]
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

    updated_payload = {**FILAMENT_TYPE_PAYLOAD, "name": "PETG", "temp_min": 220, "temp_max": 250}
    response = client.put(f"/api/v1/filament-types/{created['id']}", json=updated_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "PETG"
    assert data["temp_max"] == 250

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
