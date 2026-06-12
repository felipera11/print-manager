from datetime import date


def test_returns_correct_structure(client):
    response = client.get("/api/v1/dashboard/")
    assert response.status_code == 200
    data = response.json()

    assert isinstance(data["critical_spools"], list)
    assert isinstance(data["recent_prints"], list)
    assert isinstance(data["monthly_spend"], (int, float))
    assert isinstance(data["open_quotes"], int)

    if data["critical_spools"]:
        spool = data["critical_spools"][0]
        assert {"id", "number", "type", "color", "remaining_weight_g", "total_weight_g"} <= spool.keys()

    if data["recent_prints"]:
        print_item = data["recent_prints"][0]
        assert {"part_name", "client", "date", "price"} <= print_item.keys()


def test_monthly_spend_reflects_cost_not_price(client):
    printer = client.post(
        "/api/v1/printers/",
        json={"name": "Dashboard test printer", "brand": "Generic", "hourly_cost": 10.0, "active": True},
    ).json()
    test_client = client.post(
        "/api/v1/clients/",
        json={"name": "Dashboard test client", "email": "dashboard@test.com", "cnpj": "00.000.000/0000-00", "mobile": "+55 35 90000-0000"},
    ).json()
    filament_type = client.post(
        "/api/v1/filament-types/", json={"type": "PLA", "brand": "Generic", "cost_per_kg": 100.0}
    ).json()
    spool_model = client.post("/api/v1/spool-models/", json={"name": "Generic reel", "weight_g": 200.0}).json()
    spool = client.post(
        "/api/v1/spools/",
        json={
            "number": 99,
            "color": "White",
            "type_id": filament_type["id"],
            "spool_model_id": spool_model["id"],
            "total_weight_g": 1000,
        },
    ).json()

    before = client.get("/api/v1/dashboard/").json()["monthly_spend"]

    payload = {
        "part_name": "Dashboard test part",
        "printer_id": printer["id"],
        "client_id": test_client["id"],
        "weight_g": 100,
        "time_h": 2,
        "price": 999.0,
        "date": date.today().isoformat(),
        "spool_ids": [spool["id"]],
    }
    created = client.post("/api/v1/prints/", json=payload).json()

    after = client.get("/api/v1/dashboard/").json()["monthly_spend"]
    assert round(after - before, 2) == created["cost"]
    assert created["cost"] != created["price"]

    client.delete(f"/api/v1/prints/{created['id']}")
    client.delete(f"/api/v1/spools/{spool['id']}")
    client.delete(f"/api/v1/spool-models/{spool_model['id']}")
    client.delete(f"/api/v1/filament-types/{filament_type['id']}")
    client.delete(f"/api/v1/clients/{test_client['id']}")
    client.delete(f"/api/v1/printers/{printer['id']}")
