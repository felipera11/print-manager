PRINTER_PAYLOAD = {
    "name": "Ender 3",
    "brand": "Creality",
    "hourly_cost": 5.5,
    "active": True,
}


def test_create(client):
    response = client.post("/api/v1/printers/", json=PRINTER_PAYLOAD)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == PRINTER_PAYLOAD["name"]
    assert data["brand"] == PRINTER_PAYLOAD["brand"]
    assert "id" in data

    client.delete(f"/api/v1/printers/{data['id']}")


def test_list(client):
    created = client.post("/api/v1/printers/", json=PRINTER_PAYLOAD).json()

    response = client.get("/api/v1/printers/")
    assert response.status_code == 200
    assert any(printer["id"] == created["id"] for printer in response.json())

    client.delete(f"/api/v1/printers/{created['id']}")


def test_edit(client):
    created = client.post("/api/v1/printers/", json=PRINTER_PAYLOAD).json()

    updated_payload = {**PRINTER_PAYLOAD, "name": "Ender 3 V2", "hourly_cost": 6.0}
    response = client.put(f"/api/v1/printers/{created['id']}", json=updated_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Ender 3 V2"
    assert data["hourly_cost"] == 6.0

    client.delete(f"/api/v1/printers/{created['id']}")


def test_delete(client):
    created = client.post("/api/v1/printers/", json=PRINTER_PAYLOAD).json()

    response = client.delete(f"/api/v1/printers/{created['id']}")
    assert response.status_code == 204

    response = client.get(f"/api/v1/printers/{created['id']}")
    assert response.status_code == 404


def test_not_found(client):
    assert client.get("/api/v1/printers/999999").status_code == 404
    assert client.put("/api/v1/printers/999999", json=PRINTER_PAYLOAD).status_code == 404
    assert client.delete("/api/v1/printers/999999").status_code == 404
