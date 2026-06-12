from datetime import date as date_type
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from database import get_db
from models import Client, FilamentType, Printer, Quote, QuoteItem
from quote_pdf import build_quote_pdf

router = APIRouter()

QuoteStatus = Literal["pending", "sent", "approved", "declined"]


class QuoteItemInput(BaseModel):
    part_name: str
    quantity: int
    weight_g: float
    time_h: float
    margin: float
    printer_id: int
    filament_type_id: int


class QuoteItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    quote_id: int
    part_name: str
    quantity: int
    weight_g: float
    time_h: float
    margin: float
    printer_id: int
    filament_type_id: int
    unit_price: float
    total: float


class QuoteBase(BaseModel):
    client_id: int
    issuer_client_id: int
    discount: float = 0
    status: QuoteStatus = "pending"
    items: list[QuoteItemInput] = Field(min_length=1)


class QuoteResponse(BaseModel):
    id: int
    client_id: int
    issuer_client_id: int
    discount: float
    total: float
    date: date_type
    status: QuoteStatus
    items: list[QuoteItemResponse]


def get_quote_or_404(quote_id: int, db: Session) -> Quote:
    quote = db.get(Quote, quote_id)
    if quote is None:
        raise HTTPException(status_code=404, detail="Quote not found")
    return quote


def get_client_or_404(client_id: int, db: Session) -> Client:
    client = db.get(Client, client_id)
    if client is None:
        raise HTTPException(status_code=404, detail="Client not found")
    return client


def get_printers_or_404(printer_ids: set[int], db: Session) -> dict[int, Printer]:
    printers_by_id = {printer.id: printer for printer in db.query(Printer).filter(Printer.id.in_(printer_ids)).all()}
    if len(printers_by_id) != len(printer_ids):
        raise HTTPException(status_code=404, detail="One or more printers not found")
    return printers_by_id


def get_filament_types_or_404(filament_type_ids: set[int], db: Session) -> dict[int, FilamentType]:
    filament_types_by_id = {
        filament_type.id: filament_type
        for filament_type in db.query(FilamentType).filter(FilamentType.id.in_(filament_type_ids)).all()
    }
    if len(filament_types_by_id) != len(filament_type_ids):
        raise HTTPException(status_code=404, detail="One or more filament types not found")
    return filament_types_by_id


def calculate_item_pricing(item: QuoteItemInput, printer: Printer, filament_type: FilamentType) -> tuple[float, float]:
    filament_cost = (item.weight_g / 1000) * float(filament_type.cost_per_kg)
    printing_cost = item.time_h * float(printer.hourly_cost)
    unit_price = round((filament_cost + printing_cost) * (1 + item.margin / 100), 2)
    total = round(unit_price * item.quantity, 2)
    return unit_price, total


def calculate_quote_total(item_totals: list[float], discount: float) -> float:
    subtotal = sum(item_totals)
    return round(subtotal * (1 - discount / 100), 2)


def build_quote_items(items: list[QuoteItemInput], db: Session) -> list[QuoteItem]:
    printers_by_id = get_printers_or_404({item.printer_id for item in items}, db)
    filament_types_by_id = get_filament_types_or_404({item.filament_type_id for item in items}, db)

    quote_items = []
    for item in items:
        unit_price, total = calculate_item_pricing(
            item, printers_by_id[item.printer_id], filament_types_by_id[item.filament_type_id]
        )
        quote_items.append(
            QuoteItem(
                part_name=item.part_name,
                quantity=item.quantity,
                weight_g=item.weight_g,
                time_h=item.time_h,
                margin=item.margin,
                printer_id=item.printer_id,
                filament_type_id=item.filament_type_id,
                unit_price=unit_price,
                total=total,
            )
        )
    return quote_items


def replace_quote_items(quote_id: int, items: list[QuoteItemInput], db: Session) -> list[QuoteItem]:
    db.query(QuoteItem).filter(QuoteItem.quote_id == quote_id).delete()
    quote_items = build_quote_items(items, db)
    for quote_item in quote_items:
        quote_item.quote_id = quote_id
        db.add(quote_item)
    return quote_items


def serialize_quote(db_quote: Quote, db: Session) -> dict:
    items = db.query(QuoteItem).filter(QuoteItem.quote_id == db_quote.id).all()
    return {
        "id": db_quote.id,
        "client_id": db_quote.client_id,
        "issuer_client_id": db_quote.issuer_client_id,
        "discount": db_quote.discount,
        "total": db_quote.total,
        "date": db_quote.date,
        "status": db_quote.status,
        "items": items,
    }


@router.get("/", response_model=list[QuoteResponse])
def list_quotes(db: Session = Depends(get_db)):
    return [serialize_quote(quote, db) for quote in db.query(Quote).all()]


@router.get("/{quote_id}", response_model=QuoteResponse)
def get_quote(quote_id: int, db: Session = Depends(get_db)):
    return serialize_quote(get_quote_or_404(quote_id, db), db)


@router.post("/", response_model=QuoteResponse, status_code=201)
def create_quote(quote_data: QuoteBase, db: Session = Depends(get_db)):
    get_client_or_404(quote_data.client_id, db)
    get_client_or_404(quote_data.issuer_client_id, db)
    quote_items = build_quote_items(quote_data.items, db)

    db_quote = Quote(
        client_id=quote_data.client_id,
        issuer_client_id=quote_data.issuer_client_id,
        discount=quote_data.discount,
        status=quote_data.status,
        total=calculate_quote_total([item.total for item in quote_items], quote_data.discount),
        date=date_type.today(),
    )
    db.add(db_quote)
    db.flush()

    for quote_item in quote_items:
        quote_item.quote_id = db_quote.id
        db.add(quote_item)

    db.commit()
    db.refresh(db_quote)
    return serialize_quote(db_quote, db)


@router.put("/{quote_id}", response_model=QuoteResponse)
def update_quote(quote_id: int, quote_data: QuoteBase, db: Session = Depends(get_db)):
    db_quote = get_quote_or_404(quote_id, db)
    get_client_or_404(quote_data.client_id, db)
    get_client_or_404(quote_data.issuer_client_id, db)

    quote_items = replace_quote_items(quote_id, quote_data.items, db)

    db_quote.client_id = quote_data.client_id
    db_quote.issuer_client_id = quote_data.issuer_client_id
    db_quote.discount = quote_data.discount
    db_quote.status = quote_data.status
    db_quote.total = calculate_quote_total([item.total for item in quote_items], quote_data.discount)

    db.commit()
    db.refresh(db_quote)
    return serialize_quote(db_quote, db)


@router.get("/{quote_id}/pdf")
def get_quote_pdf(quote_id: int, db: Session = Depends(get_db)):
    db_quote = get_quote_or_404(quote_id, db)
    recipient = get_client_or_404(db_quote.client_id, db)
    issuer = get_client_or_404(db_quote.issuer_client_id, db)
    items = db.query(QuoteItem).filter(QuoteItem.quote_id == quote_id).all()

    pdf_bytes = build_quote_pdf(db_quote, issuer, recipient, items)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=quote_{quote_id}.pdf"},
    )


@router.delete("/{quote_id}", status_code=204)
def delete_quote(quote_id: int, db: Session = Depends(get_db)):
    db_quote = get_quote_or_404(quote_id, db)
    db.query(QuoteItem).filter(QuoteItem.quote_id == quote_id).delete()
    db.delete(db_quote)
    db.commit()
