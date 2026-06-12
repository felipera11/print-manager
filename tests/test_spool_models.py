SPOOL_MODEL_PAYLOAD = {
    "name": "Elegoo 1kg reel",
    "weight_g": 200.0,
}


def test_create(client):
    response = client.post("/api/v1/spool-models/", json=SPOOL_MODEL_PAYLOAD)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == SPOOL_MODEL_PAYLOAD["name"]
    assert data["weight_g"] == SPOOL_MODEL_PAYLOAD["weight_g"]
    assert "id" in data

    client.delete(f"/api/v1/spool-models/{data['id']}")


def test_list(client):
    created = client.post("/api/v1/spool-models/", json=SPOOL_MODEL_PAYLOAD).json()

    response = client.get("/api/v1/spool-models/")
    assert response.status_code == 200
    assert any(spool_model["id"] == created["id"] for spool_model in response.json())

    client.delete(f"/api/v1/spool-models/{created['id']}")


def test_edit(client):
    created = client.post("/api/v1/spool-models/", json=SPOOL_MODEL_PAYLOAD).json()

    updated_payload = {**SPOOL_MODEL_PAYLOAD, "name": "Creality 1kg reel", "weight_g": 180.0}
    response = client.put(f"/api/v1/spool-models/{created['id']}", json=updated_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Creality 1kg reel"
    assert data["weight_g"] == 180.0

    client.delete(f"/api/v1/spool-models/{created['id']}")


def test_delete(client):
    created = client.post("/api/v1/spool-models/", json=SPOOL_MODEL_PAYLOAD).json()

    response = client.delete(f"/api/v1/spool-models/{created['id']}")
    assert response.status_code == 204

    response = client.get(f"/api/v1/spool-models/{created['id']}")
    assert response.status_code == 404


def test_not_found(client):
    assert client.get("/api/v1/spool-models/999999").status_code == 404
    assert client.put("/api/v1/spool-models/999999", json=SPOOL_MODEL_PAYLOAD).status_code == 404
    assert client.delete("/api/v1/spool-models/999999").status_code == 404
