from datetime import date as date_type
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import get_db
from models import Client, FilamentType, Print, PrintSpool, Printer, Spool

router = APIRouter()

PrintStatus = Literal["queued", "printing", "completed", "failed"]

RESERVING_STATUSES = {"queued", "printing"}
CONSUMING_STATUSES = {"completed"}


class PrintBase(BaseModel):
    part_name: str
    printer_id: int
    client_id: int
    weight_g: float
    time_h: float
    price: float
    date: date_type
    notes: str | None = None
    status: PrintStatus = "queued"
    spool_ids: list[int] = Field(min_length=1)


class PrintStatusUpdate(BaseModel):
    status: PrintStatus


class PrintReorder(BaseModel):
    print_ids: list[int]


class PrintResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    part_name: str
    printer_id: int
    client_id: int
    weight_g: float
    time_h: float
    cost: float
    price: float
    date: date_type
    notes: str | None = None
    status: PrintStatus
    queue_position: int
    spool_ids: list[int]


def get_print_or_404(print_id: int, db: Session) -> Print:
    db_print = db.get(Print, print_id)
    if db_print is None:
        raise HTTPException(status_code=404, detail="Print not found")
    return db_print


def get_printer_or_404(printer_id: int, db: Session) -> Printer:
    printer = db.get(Printer, printer_id)
    if printer is None:
        raise HTTPException(status_code=404, detail="Printer not found")
    return printer


def get_client_or_404(client_id: int, db: Session) -> Client:
    client = db.get(Client, client_id)
    if client is None:
        raise HTTPException(status_code=404, detail="Client not found")
    return client


def get_spools_or_404(spool_ids: list[int], db: Session) -> list[Spool]:
    spools = db.query(Spool).filter(Spool.id.in_(spool_ids)).all()
    if len(spools) != len(set(spool_ids)):
        raise HTTPException(status_code=404, detail="One or more spools not found")
    return spools


def get_print_spool_ids(print_id: int, db: Session) -> list[int]:
    rows = db.query(PrintSpool.spool_id).filter(PrintSpool.print_id == print_id).all()
    return [row[0] for row in rows]


def serialize_print(db_print: Print, db: Session) -> dict:
    return {
        "id": db_print.id,
        "part_name": db_print.part_name,
        "printer_id": db_print.printer_id,
        "client_id": db_print.client_id,
        "weight_g": db_print.weight_g,
        "time_h": db_print.time_h,
        "cost": db_print.cost,
        "price": db_print.price,
        "date": db_print.date,
        "notes": db_print.notes,
        "status": db_print.status,
        "queue_position": db_print.queue_position,
        "spool_ids": get_print_spool_ids(db_print.id, db),
    }


def calculate_filament_cost(spools: list[Spool], weight_g: float, db: Session) -> float:
    if not spools:
        return 0.0

    type_ids = {spool.type_id for spool in spools}
    filament_types_by_id = {
        filament_type.id: filament_type
        for filament_type in db.query(FilamentType).filter(FilamentType.id.in_(type_ids)).all()
    }

    weight_per_spool_g = weight_g / len(spools)
    return sum(
        (weight_per_spool_g / 1000) * float(filament_types_by_id[spool.type_id].cost_per_kg)
        for spool in spools
    )


def calculate_cost(weight_g: float, time_h: float, hourly_cost: float, filament_cost: float) -> float:
    printing_cost = time_h * hourly_cost
    return round(filament_cost + printing_cost, 2)


def release_inventory(spools: list[Spool], weight_g: float, status: PrintStatus) -> None:
    """Undo whatever reservation/consumption `status` previously applied to `spools`."""
    if not spools:
        return
    weight_per_spool_g = weight_g / len(spools)
    for spool in spools:
        if status in RESERVING_STATUSES:
            spool.reserved_weight_g = float(spool.reserved_weight_g) - weight_per_spool_g
        if status in CONSUMING_STATUSES:
            spool.total_weight_g = float(spool.total_weight_g) + weight_per_spool_g
            spool.remaining_weight_g = float(spool.remaining_weight_g) + weight_per_spool_g


def apply_inventory(spools: list[Spool], weight_g: float, status: PrintStatus) -> None:
    """Apply the reservation/consumption that `status` requires for `spools`."""
    if not spools:
        return
    weight_per_spool_g = weight_g / len(spools)
    for spool in spools:
        if status in RESERVING_STATUSES:
            spool.reserved_weight_g = float(spool.reserved_weight_g) + weight_per_spool_g
        if status in CONSUMING_STATUSES:
            spool.total_weight_g = float(spool.total_weight_g) - weight_per_spool_g
            spool.remaining_weight_g = float(spool.remaining_weight_g) - weight_per_spool_g


def validate_spool_capacity(spools: list[Spool], weight_g: float, status: PrintStatus) -> None:
    """Reject prints that would reserve more filament than a spool currently has available."""
    if status not in RESERVING_STATUSES or not spools:
        return

    weight_per_spool_g = weight_g / len(spools)
    for spool in spools:
        available_weight_g = float(spool.remaining_weight_g) - float(spool.reserved_weight_g)
        if weight_per_spool_g > available_weight_g:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Spool #{spool.number} only has {available_weight_g}g available, "
                    f"but {weight_per_spool_g}g is required"
                ),
            )


def validate_single_printing_per_printer(
    printer_id: int, status: PrintStatus, db: Session, exclude_print_id: int | None = None
) -> None:
    """Reject marking a print as "printing" if its printer already has one in progress."""
    if status != "printing":
        return

    query = db.query(Print).filter(Print.printer_id == printer_id, Print.status == "printing")
    if exclude_print_id is not None:
        query = query.filter(Print.id != exclude_print_id)
    if query.first() is not None:
        raise HTTPException(status_code=400, detail="This printer already has a print in progress")


def replace_print_spools(print_id: int, spool_ids: list[int], db: Session) -> None:
    db.query(PrintSpool).filter(PrintSpool.print_id == print_id).delete()
    for spool_id in spool_ids:
        db.add(PrintSpool(print_id=print_id, spool_id=spool_id))


def next_queue_position(db: Session) -> int:
    max_position = db.query(func.max(Print.queue_position)).scalar()
    return (max_position or 0) + 1


@router.get("/", response_model=list[PrintResponse])
def list_prints(
    client_id: int | None = None,
    printer_id: int | None = None,
    status: PrintStatus | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(Print)
    if client_id is not None:
        query = query.filter(Print.client_id == client_id)
    if printer_id is not None:
        query = query.filter(Print.printer_id == printer_id)
    if status is not None:
        query = query.filter(Print.status == status)
    if status == "queued":
        query = query.order_by(Print.queue_position.asc())
    return [serialize_print(db_print, db) for db_print in query.all()]


@router.get("/{print_id}", response_model=PrintResponse)
def get_print(print_id: int, db: Session = Depends(get_db)):
    return serialize_print(get_print_or_404(print_id, db), db)


@router.post("/", response_model=PrintResponse, status_code=201)
def create_print(print_data: PrintBase, db: Session = Depends(get_db)):
    printer = get_printer_or_404(print_data.printer_id, db)
    get_client_or_404(print_data.client_id, db)
    spools = get_spools_or_404(print_data.spool_ids, db)

    validate_spool_capacity(spools, print_data.weight_g, print_data.status)
    validate_single_printing_per_printer(print_data.printer_id, print_data.status, db)

    filament_cost = calculate_filament_cost(spools, print_data.weight_g, db)
    cost = calculate_cost(print_data.weight_g, print_data.time_h, float(printer.hourly_cost), filament_cost)

    db_print = Print(
        part_name=print_data.part_name,
        printer_id=print_data.printer_id,
        client_id=print_data.client_id,
        weight_g=print_data.weight_g,
        time_h=print_data.time_h,
        cost=cost,
        price=print_data.price,
        date=print_data.date,
        notes=print_data.notes,
        status=print_data.status,
        queue_position=next_queue_position(db),
    )
    db.add(db_print)
    db.flush()

    replace_print_spools(db_print.id, print_data.spool_ids, db)
    apply_inventory(spools, print_data.weight_g, print_data.status)

    db.commit()
    db.refresh(db_print)
    return serialize_print(db_print, db)


@router.put("/{print_id}", response_model=PrintResponse)
def update_print(print_id: int, print_data: PrintBase, db: Session = Depends(get_db)):
    db_print = get_print_or_404(print_id, db)
    printer = get_printer_or_404(print_data.printer_id, db)
    get_client_or_404(print_data.client_id, db)
    new_spools = get_spools_or_404(print_data.spool_ids, db)

    old_spool_ids = get_print_spool_ids(print_id, db)
    old_spools = get_spools_or_404(old_spool_ids, db)
    release_inventory(old_spools, float(db_print.weight_g), db_print.status)

    validate_spool_capacity(new_spools, print_data.weight_g, print_data.status)
    validate_single_printing_per_printer(print_data.printer_id, print_data.status, db, exclude_print_id=print_id)

    filament_cost = calculate_filament_cost(new_spools, print_data.weight_g, db)
    cost = calculate_cost(print_data.weight_g, print_data.time_h, float(printer.hourly_cost), filament_cost)

    db_print.part_name = print_data.part_name
    db_print.printer_id = print_data.printer_id
    db_print.client_id = print_data.client_id
    db_print.weight_g = print_data.weight_g
    db_print.time_h = print_data.time_h
    db_print.cost = cost
    db_print.price = print_data.price
    db_print.date = print_data.date
    db_print.notes = print_data.notes
    db_print.status = print_data.status

    replace_print_spools(print_id, print_data.spool_ids, db)
    apply_inventory(new_spools, print_data.weight_g, print_data.status)

    db.commit()
    db.refresh(db_print)
    return serialize_print(db_print, db)


@router.patch("/reorder", status_code=204)
def reorder_prints(reorder: PrintReorder, db: Session = Depends(get_db)):
    for position, print_id in enumerate(reorder.print_ids):
        db.query(Print).filter(Print.id == print_id).update({"queue_position": position})
    db.commit()


@router.patch("/{print_id}/status", response_model=PrintResponse)
def update_print_status(print_id: int, status_update: PrintStatusUpdate, db: Session = Depends(get_db)):
    db_print = get_print_or_404(print_id, db)
    spools = get_spools_or_404(get_print_spool_ids(print_id, db), db)

    release_inventory(spools, float(db_print.weight_g), db_print.status)

    validate_spool_capacity(spools, float(db_print.weight_g), status_update.status)
    validate_single_printing_per_printer(db_print.printer_id, status_update.status, db, exclude_print_id=print_id)

    apply_inventory(spools, float(db_print.weight_g), status_update.status)

    db_print.status = status_update.status
    db.commit()
    db.refresh(db_print)
    return serialize_print(db_print, db)


@router.delete("/{print_id}", status_code=204)
def delete_print(print_id: int, db: Session = Depends(get_db)):
    db_print = get_print_or_404(print_id, db)

    spools = get_spools_or_404(get_print_spool_ids(print_id, db), db)
    release_inventory(spools, float(db_print.weight_g), db_print.status)

    db.query(PrintSpool).filter(PrintSpool.print_id == print_id).delete()
    db.delete(db_print)
    db.commit()
