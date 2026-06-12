import pytest

PRINTER_PAYLOAD = {
    "name": "Ender 3",
    "brand": "Creality",
    "hourly_cost": 10.0,
    "active": True,
}

CLIENT_PAYLOAD = {
    "name": "Acme Corp",
    "email": "contact@acme.com",
    "cnpj": "12.345.678/0001-90",
    "address": "Rua das Flores, 123",
    "mobile": "+55 35 99999-0000",
    "phone": None,
}

FILAMENT_TYPE_PAYLOAD = {
    "type": "PLA",
    "brand": "Elegoo",
    "cost_per_kg": 100.0,
}


@pytest.fixture
def printer(client):
    created = client.post("/api/v1/printers/", json=PRINTER_PAYLOAD).json()
    yield created
    client.delete(f"/api/v1/printers/{created['id']}")


@pytest.fixture
def quote_client(client):
    created = client.post("/api/v1/clients/", json=CLIENT_PAYLOAD).json()
    yield created
    client.delete(f"/api/v1/clients/{created['id']}")


@pytest.fixture
def filament_type(client):
    created = client.post("/api/v1/filament-types/", json=FILAMENT_TYPE_PAYLOAD).json()
    yield created
    client.delete(f"/api/v1/filament-types/{created['id']}")


def item_payload(printer, filament_type, **overrides):
    payload = {
        "part_name": "Phone stand",
        "quantity": 2,
        "weight_g": 100,
        "time_h": 2,
        "margin": 20,
        "printer_id": printer["id"],
        "filament_type_id": filament_type["id"],
    }
    payload.update(overrides)
    return payload


def expected_unit_price_and_total(item):
    filament_cost = (item["weight_g"] / 1000) * FILAMENT_TYPE_PAYLOAD["cost_per_kg"]
    printing_cost = item["time_h"] * PRINTER_PAYLOAD["hourly_cost"]
    unit_price = round((filament_cost + printing_cost) * (1 + item["margin"] / 100), 2)
    total = round(unit_price * item["quantity"], 2)
    return unit_price, total


def test_create_with_items(client, printer, quote_client, filament_type):
    payload = {
        "client_id": quote_client["id"],
        "discount": 10,
        "items": [item_payload(printer, filament_type)],
    }
    response = client.post("/api/v1/quotes/", json=payload)
    assert response.status_code == 201
    data = response.json()

    assert data["client_id"] == quote_client["id"]
    assert data["status"] == "pending"
    assert len(data["items"]) == 1

    item = data["items"][0]
    expected_unit_price, expected_total = expected_unit_price_and_total(payload["items"][0])
    assert item["unit_price"] == expected_unit_price
    assert item["total"] == expected_total
    assert item["printer_id"] == printer["id"]
    assert item["filament_type_id"] == filament_type["id"]

    expected_quote_total = round(expected_total * (1 - payload["discount"] / 100), 2)
    assert data["total"] == expected_quote_total

    client.delete(f"/api/v1/quotes/{data['id']}")


def test_total_calculation(client, printer, quote_client, filament_type):
    items = [
        item_payload(printer, filament_type, part_name="Phone stand", quantity=2, weight_g=100, time_h=2, margin=20),
        item_payload(printer, filament_type, part_name="Keychain", quantity=5, weight_g=20, time_h=0.5, margin=50),
    ]
    payload = {
        "client_id": quote_client["id"],
        "discount": 15,
        "items": items,
    }
    response = client.post("/api/v1/quotes/", json=payload)
    assert response.status_code == 201
    data = response.json()

    item_totals = []
    for item, item_data in zip(items, data["items"]):
        expected_unit_price, expected_total = expected_unit_price_and_total(item)
        assert item_data["unit_price"] == expected_unit_price
        assert item_data["total"] == expected_total
        item_totals.append(expected_total)

    expected_quote_total = round(sum(item_totals) * (1 - payload["discount"] / 100), 2)
    assert data["total"] == expected_quote_total

    client.delete(f"/api/v1/quotes/{data['id']}")


def test_list(client, printer, quote_client, filament_type):
    payload = {
        "client_id": quote_client["id"],
        "discount": 0,
        "items": [item_payload(printer, filament_type)],
    }
    created = client.post("/api/v1/quotes/", json=payload).json()

    response = client.get("/api/v1/quotes/")
    assert response.status_code == 200
    assert any(quote["id"] == created["id"] for quote in response.json())

    client.delete(f"/api/v1/quotes/{created['id']}")


def test_delete(client, printer, quote_client, filament_type):
    payload = {
        "client_id": quote_client["id"],
        "discount": 0,
        "items": [item_payload(printer, filament_type)],
    }
    created = client.post("/api/v1/quotes/", json=payload).json()

    response = client.delete(f"/api/v1/quotes/{created['id']}")
    assert response.status_code == 204

    response = client.get(f"/api/v1/quotes/{created['id']}")
    assert response.status_code == 404
