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

SPOOL_MODEL_PAYLOAD = {
    "name": "Elegoo 1kg reel",
    "weight_g": 200.0,
}

SPOOL_PAYLOAD = {
    "number": 1,
    "color": "Black",
    "total_weight_g": 1000,
}

PRINT_PAYLOAD = {
    "part_name": "Phone stand",
    "weight_g": 100,
    "time_h": 2,
    "date": "2026-06-01",
    "notes": "Sample print",
}


@pytest.fixture
def printer(client):
    created = client.post("/api/v1/printers/", json=PRINTER_PAYLOAD).json()
    yield created
    client.delete(f"/api/v1/printers/{created['id']}")


@pytest.fixture
def print_client(client):
    created = client.post("/api/v1/clients/", json=CLIENT_PAYLOAD).json()
    yield created
    client.delete(f"/api/v1/clients/{created['id']}")


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


@pytest.fixture
def spool(client, filament_type, spool_model):
    payload = {
        **SPOOL_PAYLOAD,
        "type_id": filament_type["id"],
        "spool_model_id": spool_model["id"],
    }
    created = client.post("/api/v1/spools/", json=payload).json()
    yield created
    client.delete(f"/api/v1/spools/{created['id']}")


@pytest.fixture
def spool2(client, filament_type, spool_model):
    payload = {
        **SPOOL_PAYLOAD,
        "number": 2,
        "type_id": filament_type["id"],
        "spool_model_id": spool_model["id"],
    }
    created = client.post("/api/v1/spools/", json=payload).json()
    yield created
    client.delete(f"/api/v1/spools/{created['id']}")


def test_create_calculates_price(client, printer, print_client, spool):
    payload = {
        **PRINT_PAYLOAD,
        "printer_id": printer["id"],
        "client_id": print_client["id"],
        "spool_ids": [spool["id"]],
    }
    response = client.post("/api/v1/prints/", json=payload)
    assert response.status_code == 201
    data = response.json()

    filament_cost = (payload["weight_g"] / 1000) * FILAMENT_TYPE_PAYLOAD["cost_per_kg"]
    printing_cost = payload["time_h"] * PRINTER_PAYLOAD["hourly_cost"]
    assert data["price"] == filament_cost + printing_cost
    assert data["spool_ids"] == [spool["id"]]
    assert data["status"] == "queued"
    assert isinstance(data["queue_position"], int)

    client.delete(f"/api/v1/prints/{data['id']}")


def test_create_reserves_spool(client, printer, print_client, spool):
    payload = {
        **PRINT_PAYLOAD,
        "printer_id": printer["id"],
        "client_id": print_client["id"],
        "spool_ids": [spool["id"]],
    }
    created = client.post("/api/v1/prints/", json=payload).json()

    updated_spool = client.get(f"/api/v1/spools/{spool['id']}").json()
    assert updated_spool["reserved_weight_g"] == payload["weight_g"]
    assert updated_spool["remaining_weight_g"] == spool["remaining_weight_g"]

    client.delete(f"/api/v1/prints/{created['id']}")


def test_complete_consumes_spool_and_releases_reservation(client, printer, print_client, spool):
    payload = {
        **PRINT_PAYLOAD,
        "printer_id": printer["id"],
        "client_id": print_client["id"],
        "spool_ids": [spool["id"]],
    }
    created = client.post("/api/v1/prints/", json=payload).json()

    response = client.patch(f"/api/v1/prints/{created['id']}/status", json={"status": "completed"})
    assert response.status_code == 200
    assert response.json()["status"] == "completed"

    updated_spool = client.get(f"/api/v1/spools/{spool['id']}").json()
    assert updated_spool["reserved_weight_g"] == 0
    assert updated_spool["remaining_weight_g"] == spool["remaining_weight_g"] - payload["weight_g"]
    assert updated_spool["total_weight_g"] == spool["total_weight_g"] - payload["weight_g"]

    client.delete(f"/api/v1/prints/{created['id']}")


def test_reverting_completed_restores_spool(client, printer, print_client, spool):
    payload = {
        **PRINT_PAYLOAD,
        "printer_id": printer["id"],
        "client_id": print_client["id"],
        "spool_ids": [spool["id"]],
    }
    created = client.post("/api/v1/prints/", json=payload).json()
    client.patch(f"/api/v1/prints/{created['id']}/status", json={"status": "completed"})

    response = client.patch(f"/api/v1/prints/{created['id']}/status", json={"status": "queued"})
    assert response.status_code == 200

    updated_spool = client.get(f"/api/v1/spools/{spool['id']}").json()
    assert updated_spool["reserved_weight_g"] == payload["weight_g"]
    assert updated_spool["remaining_weight_g"] == spool["remaining_weight_g"]
    assert updated_spool["total_weight_g"] == spool["total_weight_g"]

    client.delete(f"/api/v1/prints/{created['id']}")


def test_failed_releases_reservation_without_consuming(client, printer, print_client, spool):
    payload = {
        **PRINT_PAYLOAD,
        "printer_id": printer["id"],
        "client_id": print_client["id"],
        "spool_ids": [spool["id"]],
    }
    created = client.post("/api/v1/prints/", json=payload).json()

    response = client.patch(f"/api/v1/prints/{created['id']}/status", json={"status": "failed"})
    assert response.status_code == 200

    updated_spool = client.get(f"/api/v1/spools/{spool['id']}").json()
    assert updated_spool["reserved_weight_g"] == 0
    assert updated_spool["remaining_weight_g"] == spool["remaining_weight_g"]

    client.delete(f"/api/v1/prints/{created['id']}")


def test_update_moves_reservation_to_new_spool(client, printer, print_client, spool, spool2):
    payload = {
        **PRINT_PAYLOAD,
        "printer_id": printer["id"],
        "client_id": print_client["id"],
        "spool_ids": [spool["id"]],
    }
    created = client.post("/api/v1/prints/", json=payload).json()

    update_payload = {**payload, "spool_ids": [spool2["id"]]}
    response = client.put(f"/api/v1/prints/{created['id']}", json=update_payload)
    assert response.status_code == 200
    assert response.json()["spool_ids"] == [spool2["id"]]

    old_spool = client.get(f"/api/v1/spools/{spool['id']}").json()
    new_spool = client.get(f"/api/v1/spools/{spool2['id']}").json()
    assert old_spool["reserved_weight_g"] == 0
    assert new_spool["reserved_weight_g"] == payload["weight_g"]

    client.delete(f"/api/v1/prints/{created['id']}")


def test_list(client, printer, print_client, spool):
    payload = {
        **PRINT_PAYLOAD,
        "printer_id": printer["id"],
        "client_id": print_client["id"],
        "spool_ids": [spool["id"]],
    }
    created = client.post("/api/v1/prints/", json=payload).json()

    response = client.get("/api/v1/prints/")
    assert response.status_code == 200
    assert any(p["id"] == created["id"] for p in response.json())

    response = client.get("/api/v1/prints/", params={"client_id": print_client["id"]})
    assert all(p["client_id"] == print_client["id"] for p in response.json())
    assert any(p["id"] == created["id"] for p in response.json())

    response = client.get("/api/v1/prints/", params={"printer_id": printer["id"]})
    assert all(p["printer_id"] == printer["id"] for p in response.json())
    assert any(p["id"] == created["id"] for p in response.json())

    response = client.get("/api/v1/prints/", params={"status": "queued"})
    assert all(p["status"] == "queued" for p in response.json())
    assert any(p["id"] == created["id"] for p in response.json())

    response = client.get("/api/v1/prints/", params={"status": "completed"})
    assert all(p["id"] != created["id"] for p in response.json())

    client.delete(f"/api/v1/prints/{created['id']}")


def test_delete_releases_reservation(client, printer, print_client, spool):
    payload = {
        **PRINT_PAYLOAD,
        "printer_id": printer["id"],
        "client_id": print_client["id"],
        "spool_ids": [spool["id"]],
    }
    created = client.post("/api/v1/prints/", json=payload).json()

    response = client.delete(f"/api/v1/prints/{created['id']}")
    assert response.status_code == 204

    response = client.get(f"/api/v1/prints/{created['id']}")
    assert response.status_code == 404

    restored_spool = client.get(f"/api/v1/spools/{spool['id']}").json()
    assert restored_spool["reserved_weight_g"] == spool["reserved_weight_g"]
    assert restored_spool["remaining_weight_g"] == spool["remaining_weight_g"]


def test_suggest_excludes_reserved_weight(client, printer, print_client, spool):
    remaining_weight_g = spool["remaining_weight_g"]

    payload = {
        **PRINT_PAYLOAD,
        "weight_g": remaining_weight_g - 50,
        "printer_id": printer["id"],
        "client_id": print_client["id"],
        "spool_ids": [spool["id"]],
    }
    created = client.post("/api/v1/prints/", json=payload).json()

    # remaining_weight_g alone would still satisfy this, but most of it is now reserved
    response = client.get(
        "/api/v1/spools/suggest", params={"weight_g": remaining_weight_g - 25, "type_id": spool["type_id"]}
    )
    assert all(s["id"] != spool["id"] for s in response.json())

    response = client.get(
        "/api/v1/spools/suggest", params={"weight_g": 25, "type_id": spool["type_id"]}
    )
    assert any(s["id"] == spool["id"] for s in response.json())

    client.delete(f"/api/v1/prints/{created['id']}")


def test_not_found(client, printer, print_client):
    payload = {
        **PRINT_PAYLOAD,
        "printer_id": printer["id"],
        "client_id": print_client["id"],
        "spool_ids": [1],
    }
    assert client.get("/api/v1/prints/999999").status_code == 404
    assert client.put("/api/v1/prints/999999", json=payload).status_code == 404
    assert client.patch("/api/v1/prints/999999/status", json={"status": "completed"}).status_code == 404
    assert client.delete("/api/v1/prints/999999").status_code == 404


def test_create_requires_spool_ids(client, printer, print_client):
    payload = {
        **PRINT_PAYLOAD,
        "printer_id": printer["id"],
        "client_id": print_client["id"],
        "spool_ids": [],
    }
    response = client.post("/api/v1/prints/", json=payload)
    assert response.status_code == 422


def test_create_rejects_weight_exceeding_spool_capacity(client, printer, print_client, spool):
    payload = {
        **PRINT_PAYLOAD,
        "weight_g": spool["remaining_weight_g"] + 1,
        "printer_id": printer["id"],
        "client_id": print_client["id"],
        "spool_ids": [spool["id"]],
    }
    response = client.post("/api/v1/prints/", json=payload)
    assert response.status_code == 400

    updated_spool = client.get(f"/api/v1/spools/{spool['id']}").json()
    assert updated_spool["reserved_weight_g"] == 0


def test_update_rejects_weight_exceeding_spool_capacity_when_not_completed(client, printer, print_client, spool):
    payload = {
        **PRINT_PAYLOAD,
        "printer_id": printer["id"],
        "client_id": print_client["id"],
        "spool_ids": [spool["id"]],
    }
    created = client.post("/api/v1/prints/", json=payload).json()

    update_payload = {**payload, "weight_g": spool["remaining_weight_g"] + 1}
    response = client.put(f"/api/v1/prints/{created['id']}", json=update_payload)
    assert response.status_code == 400

    updated_spool = client.get(f"/api/v1/spools/{spool['id']}").json()
    assert updated_spool["reserved_weight_g"] == payload["weight_g"]

    client.delete(f"/api/v1/prints/{created['id']}")


def test_update_allows_exceeding_capacity_when_already_completed(client, printer, print_client, spool):
    payload = {
        **PRINT_PAYLOAD,
        "printer_id": printer["id"],
        "client_id": print_client["id"],
        "spool_ids": [spool["id"]],
    }
    created = client.post("/api/v1/prints/", json=payload).json()
    client.patch(f"/api/v1/prints/{created['id']}/status", json={"status": "completed"})

    update_payload = {**payload, "weight_g": spool["remaining_weight_g"] + 1, "status": "completed"}
    response = client.put(f"/api/v1/prints/{created['id']}", json=update_payload)
    assert response.status_code == 200

    client.delete(f"/api/v1/prints/{created['id']}")


def test_only_one_printing_print_per_printer(client, printer, print_client, spool, spool2):
    payload1 = {
        **PRINT_PAYLOAD,
        "printer_id": printer["id"],
        "client_id": print_client["id"],
        "spool_ids": [spool["id"]],
    }
    payload2 = {
        **PRINT_PAYLOAD,
        "printer_id": printer["id"],
        "client_id": print_client["id"],
        "spool_ids": [spool2["id"]],
    }
    print1 = client.post("/api/v1/prints/", json=payload1).json()
    print2 = client.post("/api/v1/prints/", json=payload2).json()

    response = client.patch(f"/api/v1/prints/{print1['id']}/status", json={"status": "printing"})
    assert response.status_code == 200

    response = client.patch(f"/api/v1/prints/{print2['id']}/status", json={"status": "printing"})
    assert response.status_code == 400

    client.delete(f"/api/v1/prints/{print1['id']}")
    client.delete(f"/api/v1/prints/{print2['id']}")


def test_reorder_queue(client, printer, print_client, spool, spool2):
    payload1 = {
        **PRINT_PAYLOAD,
        "weight_g": 10,
        "printer_id": printer["id"],
        "client_id": print_client["id"],
        "spool_ids": [spool["id"]],
    }
    payload2 = {
        **PRINT_PAYLOAD,
        "weight_g": 10,
        "printer_id": printer["id"],
        "client_id": print_client["id"],
        "spool_ids": [spool2["id"]],
    }
    print1 = client.post("/api/v1/prints/", json=payload1).json()
    print2 = client.post("/api/v1/prints/", json=payload2).json()

    response = client.patch("/api/v1/prints/reorder", json={"print_ids": [print2["id"], print1["id"]]})
    assert response.status_code == 204

    response = client.get("/api/v1/prints/", params={"status": "queued"})
    queue_ids = [p["id"] for p in response.json()]
    assert queue_ids.index(print2["id"]) < queue_ids.index(print1["id"])

    client.delete(f"/api/v1/prints/{print1['id']}")
    client.delete(f"/api/v1/prints/{print2['id']}")
