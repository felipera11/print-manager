CLIENT_PAYLOAD = {
    "name": "Acme Corp",
    "email": "contact@acme.com",
    "cnpj": "12.345.678/0001-90",
    "address": "Rua das Flores, 123",
    "mobile": "+55 35 99999-0000",
    "phone": None,
}


def test_create(client):
    response = client.post("/api/v1/clients/", json=CLIENT_PAYLOAD)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == CLIENT_PAYLOAD["name"]
    assert data["cnpj"] == CLIENT_PAYLOAD["cnpj"]
    assert "id" in data

    client.delete(f"/api/v1/clients/{data['id']}")


def test_list(client):
    created = client.post("/api/v1/clients/", json=CLIENT_PAYLOAD).json()

    response = client.get("/api/v1/clients/")
    assert response.status_code == 200
    assert any(c["id"] == created["id"] for c in response.json())

    client.delete(f"/api/v1/clients/{created['id']}")


def test_edit(client):
    created = client.post("/api/v1/clients/", json=CLIENT_PAYLOAD).json()

    updated_payload = {**CLIENT_PAYLOAD, "name": "Acme Corporation", "mobile": "+55 35 98888-1111"}
    response = client.put(f"/api/v1/clients/{created['id']}", json=updated_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Acme Corporation"
    assert data["mobile"] == "+55 35 98888-1111"

    client.delete(f"/api/v1/clients/{created['id']}")


def test_delete(client):
    created = client.post("/api/v1/clients/", json=CLIENT_PAYLOAD).json()

    response = client.delete(f"/api/v1/clients/{created['id']}")
    assert response.status_code == 204

    response = client.get(f"/api/v1/clients/{created['id']}")
    assert response.status_code == 404


def test_not_found(client):
    assert client.get("/api/v1/clients/999999").status_code == 404
    assert client.put("/api/v1/clients/999999", json=CLIENT_PAYLOAD).status_code == 404
    assert client.delete("/api/v1/clients/999999").status_code == 404
