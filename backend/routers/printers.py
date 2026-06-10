from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from database import get_db
from models import Printer

router = APIRouter()


class PrinterBase(BaseModel):
    name: str
    brand: str
    hourly_cost: float
    active: bool = True


class PrinterResponse(PrinterBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


def get_printer_or_404(printer_id: int, db: Session) -> Printer:
    printer = db.get(Printer, printer_id)
    if printer is None:
        raise HTTPException(status_code=404, detail="Printer not found")
    return printer


@router.get("/", response_model=list[PrinterResponse])
def list_printers(db: Session = Depends(get_db)):
    return db.query(Printer).all()


@router.get("/{printer_id}", response_model=PrinterResponse)
def get_printer(printer_id: int, db: Session = Depends(get_db)):
    return get_printer_or_404(printer_id, db)


@router.post("/", response_model=PrinterResponse, status_code=201)
def create_printer(printer: PrinterBase, db: Session = Depends(get_db)):
    db_printer = Printer(**printer.model_dump())
    db.add(db_printer)
    db.commit()
    db.refresh(db_printer)
    return db_printer


@router.put("/{printer_id}", response_model=PrinterResponse)
def update_printer(printer_id: int, printer: PrinterBase, db: Session = Depends(get_db)):
    db_printer = get_printer_or_404(printer_id, db)
    for field, value in printer.model_dump().items():
        setattr(db_printer, field, value)
    db.commit()
    db.refresh(db_printer)
    return db_printer


@router.delete("/{printer_id}", status_code=204)
def delete_printer(printer_id: int, db: Session = Depends(get_db)):
    db_printer = get_printer_or_404(printer_id, db)
    db.delete(db_printer)
    db.commit()
