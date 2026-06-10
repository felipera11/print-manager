import os

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
    spools = requests.get(f"{BACKEND_URL}/api/v1/spools/").json()
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


@app.route("/filaments/spools/new")
def new_spool():
    filament_types = requests.get(f"{BACKEND_URL}/api/v1/filament-types/").json()
    return render_template("filaments/spool_form.html", spool=None, filament_types=filament_types)


@app.route("/filaments/spools/new", methods=["POST"])
def create_spool():
    requests.post(f"{BACKEND_URL}/api/v1/spools/", json=spool_form_payload())
    return redirect(url_for("list_filaments"))


@app.route("/filaments/spools/<int:spool_id>/edit")
def edit_spool(spool_id):
    spool = requests.get(f"{BACKEND_URL}/api/v1/spools/{spool_id}").json()
    filament_types = requests.get(f"{BACKEND_URL}/api/v1/filament-types/").json()
    return render_template("filaments/spool_form.html", spool=spool, filament_types=filament_types)


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
        "name": request.form["name"],
        "temp_min": int(request.form["temp_min"]),
        "temp_max": int(request.form["temp_max"]),
    }


def spool_form_payload():
    return {
        "number": int(request.form["number"]),
        "type_id": int(request.form["type_id"]),
        "brand": request.form["brand"],
        "color": request.form["color"],
        "total_weight_g": float(request.form["total_weight_g"]),
        "remaining_weight_g": float(request.form["remaining_weight_g"]),
        "cost_per_kg": float(request.form["cost_per_kg"]),
    }


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
