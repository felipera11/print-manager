import os
from datetime import date

import requests
from flask import Flask, redirect, render_template, request, url_for

app = Flask(__name__)

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")


@app.route("/")
def index():
    return "ok"


@app.route("/printers")
def list_printers():
    response = requests.get(f"{BACKEND_URL}/api/v1/printers/")
    return render_template("printers/index.html", printers=response.json())


@app.route("/printers/new")
def new_printer():
    return render_template("printers/form.html", printer=None)


@app.route("/printers/new", methods=["POST"])
def create_printer():
    requests.post(f"{BACKEND_URL}/api/v1/printers/", json=printer_form_payload())
    return redirect(url_for("list_printers"))


@app.route("/printers/<int:printer_id>/edit")
def edit_printer(printer_id):
    response = requests.get(f"{BACKEND_URL}/api/v1/printers/{printer_id}")
    return render_template("printers/form.html", printer=response.json())


@app.route("/printers/<int:printer_id>/edit", methods=["POST"])
def update_printer(printer_id):
    requests.put(f"{BACKEND_URL}/api/v1/printers/{printer_id}", json=printer_form_payload())
    return redirect(url_for("list_printers"))


@app.route("/printers/<int:printer_id>/delete", methods=["POST"])
def delete_printer(printer_id):
    requests.delete(f"{BACKEND_URL}/api/v1/printers/{printer_id}")
    return redirect(url_for("list_printers"))


def printer_form_payload():
    return {
        "name": request.form["name"],
        "brand": request.form["brand"],
        "hourly_cost": float(request.form["hourly_cost"]),
        "active": "active" in request.form,
    }


@app.route("/filaments")
def list_filaments():
    filament_types = requests.get(f"{BACKEND_URL}/api/v1/filament-types/").json()
    spool_models = requests.get(f"{BACKEND_URL}/api/v1/spool-models/").json()
    spools = requests.get(f"{BACKEND_URL}/api/v1/spools/").json()
    spool_models_by_id = {spool_model["id"]: spool_model for spool_model in spool_models}
    for spool in spools:
        spool["spool_model"] = spool_models_by_id.get(spool["spool_model_id"])
    for filament_type in filament_types:
        filament_type["spools"] = [
            spool for spool in spools if spool["type_id"] == filament_type["id"]
        ]

    suggestion = None
    weight_g = request.args.get("weight_g")
    type_id = request.args.get("type_id")
    if weight_g and type_id:
        response = requests.get(
            f"{BACKEND_URL}/api/v1/spools/suggest",
            params={"weight_g": weight_g, "type_id": type_id},
        )
        suggestions = response.json()
        suggestion = suggestions[0] if suggestions else None

    return render_template(
        "filaments/index.html",
        filament_types=filament_types,
        spool_models=spool_models,
        suggestion=suggestion,
        weight_g=weight_g,
        type_id=type_id,
    )


@app.route("/filaments/types/new")
def new_filament_type():
    return render_template("filaments/type_form.html", filament_type=None)


@app.route("/filaments/types/new", methods=["POST"])
def create_filament_type():
    requests.post(f"{BACKEND_URL}/api/v1/filament-types/", json=filament_type_form_payload())
    return redirect(url_for("list_filaments"))


@app.route("/filaments/types/<int:type_id>/edit")
def edit_filament_type(type_id):
    response = requests.get(f"{BACKEND_URL}/api/v1/filament-types/{type_id}")
    return render_template("filaments/type_form.html", filament_type=response.json())


@app.route("/filaments/types/<int:type_id>/edit", methods=["POST"])
def update_filament_type(type_id):
    requests.put(f"{BACKEND_URL}/api/v1/filament-types/{type_id}", json=filament_type_form_payload())
    return redirect(url_for("list_filaments"))


@app.route("/filaments/types/<int:type_id>/delete", methods=["POST"])
def delete_filament_type(type_id):
    requests.delete(f"{BACKEND_URL}/api/v1/filament-types/{type_id}")
    return redirect(url_for("list_filaments"))


@app.route("/filaments/spool-models/new")
def new_spool_model():
    return render_template("filaments/spool_model_form.html", spool_model=None)


@app.route("/filaments/spool-models/new", methods=["POST"])
def create_spool_model():
    requests.post(f"{BACKEND_URL}/api/v1/spool-models/", json=spool_model_form_payload())
    return redirect(url_for("list_filaments"))


@app.route("/filaments/spool-models/<int:spool_model_id>/edit")
def edit_spool_model(spool_model_id):
    response = requests.get(f"{BACKEND_URL}/api/v1/spool-models/{spool_model_id}")
    return render_template("filaments/spool_model_form.html", spool_model=response.json())


@app.route("/filaments/spool-models/<int:spool_model_id>/edit", methods=["POST"])
def update_spool_model(spool_model_id):
    requests.put(f"{BACKEND_URL}/api/v1/spool-models/{spool_model_id}", json=spool_model_form_payload())
    return redirect(url_for("list_filaments"))


@app.route("/filaments/spool-models/<int:spool_model_id>/delete", methods=["POST"])
def delete_spool_model(spool_model_id):
    requests.delete(f"{BACKEND_URL}/api/v1/spool-models/{spool_model_id}")
    return redirect(url_for("list_filaments"))


@app.route("/filaments/spools/new")
def new_spool():
    filament_types = requests.get(f"{BACKEND_URL}/api/v1/filament-types/").json()
    spool_models = requests.get(f"{BACKEND_URL}/api/v1/spool-models/").json()
    return render_template(
        "filaments/spool_form.html", spool=None, filament_types=filament_types, spool_models=spool_models
    )


@app.route("/filaments/spools/new", methods=["POST"])
def create_spool():
    requests.post(f"{BACKEND_URL}/api/v1/spools/", json=spool_form_payload())
    return redirect(url_for("list_filaments"))


@app.route("/filaments/spools/<int:spool_id>/edit")
def edit_spool(spool_id):
    spool = requests.get(f"{BACKEND_URL}/api/v1/spools/{spool_id}").json()
    filament_types = requests.get(f"{BACKEND_URL}/api/v1/filament-types/").json()
    spool_models = requests.get(f"{BACKEND_URL}/api/v1/spool-models/").json()
    return render_template(
        "filaments/spool_form.html", spool=spool, filament_types=filament_types, spool_models=spool_models
    )


@app.route("/filaments/spools/<int:spool_id>/edit", methods=["POST"])
def update_spool(spool_id):
    requests.put(f"{BACKEND_URL}/api/v1/spools/{spool_id}", json=spool_form_payload())
    return redirect(url_for("list_filaments"))


@app.route("/filaments/spools/<int:spool_id>/delete", methods=["POST"])
def delete_spool(spool_id):
    requests.delete(f"{BACKEND_URL}/api/v1/spools/{spool_id}")
    return redirect(url_for("list_filaments"))


def filament_type_form_payload():
    return {
        "type": request.form["type"],
        "brand": request.form["brand"],
        "cost_per_kg": float(request.form["cost_per_kg"]),
    }


def spool_model_form_payload():
    return {
        "name": request.form["name"],
        "weight_g": float(request.form["weight_g"]),
    }


def spool_form_payload():
    return {
        "type_id": int(request.form["type_id"]),
        "number": int(request.form["number"]),
        "color": request.form["color"],
        "spool_model_id": int(request.form["spool_model_id"]),
        "total_weight_g": float(request.form["total_weight_g"]),
    }


@app.route("/clients")
def list_clients():
    response = requests.get(f"{BACKEND_URL}/api/v1/clients/")
    return render_template("clients/index.html", clients=response.json())


@app.route("/clients/new")
def new_client():
    return render_template("clients/form.html", client=None)


@app.route("/clients/new", methods=["POST"])
def create_client():
    requests.post(f"{BACKEND_URL}/api/v1/clients/", json=client_form_payload())
    return redirect(url_for("list_clients"))


@app.route("/clients/<int:client_id>/edit")
def edit_client(client_id):
    response = requests.get(f"{BACKEND_URL}/api/v1/clients/{client_id}")
    return render_template("clients/form.html", client=response.json())


@app.route("/clients/<int:client_id>/edit", methods=["POST"])
def update_client(client_id):
    requests.put(f"{BACKEND_URL}/api/v1/clients/{client_id}", json=client_form_payload())
    return redirect(url_for("list_clients"))


@app.route("/clients/<int:client_id>/delete", methods=["POST"])
def delete_client(client_id):
    requests.delete(f"{BACKEND_URL}/api/v1/clients/{client_id}")
    return redirect(url_for("list_clients"))


def client_form_payload():
    return {
        "name": request.form["name"],
        "email": request.form["email"],
        "cnpj": request.form["cnpj"],
        "address": request.form["address"] or None,
        "mobile": request.form["mobile"],
        "phone": request.form["phone"] or None,
    }


@app.route("/prints")
def list_prints():
    filters = {}
    client_id = request.args.get("client_id")
    printer_id = request.args.get("printer_id")
    if client_id:
        filters["client_id"] = client_id
    if printer_id:
        filters["printer_id"] = printer_id

    prints = requests.get(f"{BACKEND_URL}/api/v1/prints/", params=filters).json()
    clients = requests.get(f"{BACKEND_URL}/api/v1/clients/").json()
    printers = requests.get(f"{BACKEND_URL}/api/v1/printers/").json()

    clients_by_id = {c["id"]: c for c in clients}
    printers_by_id = {p["id"]: p for p in printers}
    for print_item in prints:
        print_item["client"] = clients_by_id.get(print_item["client_id"])
        print_item["printer"] = printers_by_id.get(print_item["printer_id"])

    return render_template(
        "prints/index.html",
        prints=prints,
        clients=clients,
        printers=printers,
        selected_client_id=client_id,
        selected_printer_id=printer_id,
    )


@app.route("/prints/new")
def new_print():
    return render_print_form(print_item=None, is_edit=False)


@app.route("/prints/new", methods=["POST"])
def create_print():
    payload = print_form_payload()
    response = requests.post(f"{BACKEND_URL}/api/v1/prints/", json=payload)
    if response.status_code >= 400:
        return render_print_form(print_item=payload, is_edit=False, error=extract_error_message(response))
    return redirect(url_for("list_prints"))


@app.route("/prints/<int:print_id>/edit")
def edit_print(print_id):
    print_item = requests.get(f"{BACKEND_URL}/api/v1/prints/{print_id}").json()
    return render_print_form(print_item=print_item, is_edit=True)


@app.route("/prints/<int:print_id>/edit", methods=["POST"])
def update_print(print_id):
    payload = print_form_payload()
    response = requests.put(f"{BACKEND_URL}/api/v1/prints/{print_id}", json=payload)
    if response.status_code >= 400:
        payload["id"] = print_id
        return render_print_form(print_item=payload, is_edit=True, error=extract_error_message(response))
    return redirect(url_for("list_prints"))


def render_print_form(print_item, is_edit, error=None):
    printers = requests.get(f"{BACKEND_URL}/api/v1/printers/").json()
    clients = requests.get(f"{BACKEND_URL}/api/v1/clients/").json()
    spools = requests.get(f"{BACKEND_URL}/api/v1/spools/").json()
    filament_types = requests.get(f"{BACKEND_URL}/api/v1/filament-types/").json()
    return render_template(
        "prints/form.html",
        print_item=print_item,
        is_edit=is_edit,
        error=error,
        printers=printers,
        clients=clients,
        spools=spools,
        filament_types=filament_types,
        today=print_item["date"] if print_item else date.today().isoformat(),
    )


def extract_error_message(response):
    detail = response.json().get("detail")
    if isinstance(detail, list):
        return "; ".join(error["msg"] for error in detail)
    return detail


@app.route("/prints/<int:print_id>/delete", methods=["POST"])
def delete_print(print_id):
    requests.delete(f"{BACKEND_URL}/api/v1/prints/{print_id}")
    return redirect(url_for("list_prints"))


def print_form_payload():
    payload = {
        "part_name": request.form["part_name"],
        "printer_id": int(request.form["printer_id"]),
        "client_id": int(request.form["client_id"]),
        "weight_g": float(request.form["weight_g"]),
        "time_h": float(request.form["time_h"]),
        "date": request.form["date"],
        "notes": request.form["notes"] or None,
        "spool_ids": [int(spool_id) for spool_id in request.form.getlist("spool_ids")],
    }
    if "status" in request.form:
        payload["status"] = request.form["status"]
    return payload


@app.route("/queue")
def print_queue():
    queued = requests.get(f"{BACKEND_URL}/api/v1/prints/", params={"status": "queued"}).json()
    printing = requests.get(f"{BACKEND_URL}/api/v1/prints/", params={"status": "printing"}).json()

    clients = requests.get(f"{BACKEND_URL}/api/v1/clients/").json()
    printers = requests.get(f"{BACKEND_URL}/api/v1/printers/").json()
    clients_by_id = {c["id"]: c for c in clients}
    printers_by_id = {p["id"]: p for p in printers}
    for print_item in queued + printing:
        print_item["client"] = clients_by_id.get(print_item["client_id"])
        print_item["printer"] = printers_by_id.get(print_item["printer_id"])

    printers_with_active_print = {p["printer_id"] for p in printing}

    return render_template(
        "queue/index.html",
        printing_prints=printing,
        queued_prints=queued,
        printers_with_active_print=printers_with_active_print,
        error=request.args.get("error"),
    )


@app.route("/queue/<int:print_id>/status", methods=["POST"])
def update_queue_status(print_id):
    response = requests.patch(
        f"{BACKEND_URL}/api/v1/prints/{print_id}/status", json={"status": request.form["status"]}
    )
    if response.status_code >= 400:
        return redirect(url_for("print_queue", error=response.json()["detail"]))
    return redirect(url_for("print_queue"))


@app.route("/queue/reorder", methods=["POST"])
def reorder_queue():
    print_ids = [int(print_id) for print_id in request.form.getlist("print_id")]
    requests.patch(f"{BACKEND_URL}/api/v1/prints/reorder", json={"print_ids": print_ids})
    return redirect(url_for("print_queue"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
