from datetime import date as date_type

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import get_db
from models import Client, FilamentType, Print, Quote, Spool

router = APIRouter()

RECENT_PRINTS_LIMIT = 5
CRITICAL_SPOOL_RATIO = 0.2


class CriticalSpoolResponse(BaseModel):
    id: int
    number: int
    type: str
    color: str
    remaining_weight_g: float
    total_weight_g: float


class RecentPrintResponse(BaseModel):
    part_name: str
    client: str
    date: date_type
    price: float


class DashboardResponse(BaseModel):
    critical_spools: list[CriticalSpoolResponse]
    recent_prints: list[RecentPrintResponse]
    monthly_spend: float
    open_quotes: int


def get_critical_spools(db: Session) -> list[CriticalSpoolResponse]:
    spools = db.query(Spool).filter(Spool.remaining_weight_g < Spool.total_weight_g * CRITICAL_SPOOL_RATIO).all()
    filament_types_by_id = {filament_type.id: filament_type for filament_type in db.query(FilamentType).all()}
    return [
        CriticalSpoolResponse(
            id=spool.id,
            number=spool.number,
            type=filament_types_by_id[spool.type_id].type,
            color=spool.color,
            remaining_weight_g=spool.remaining_weight_g,
            total_weight_g=spool.total_weight_g,
        )
        for spool in spools
    ]


def get_recent_prints(db: Session) -> list[RecentPrintResponse]:
    rows = (
        db.query(Print, Client.name)
        .join(Client, Print.client_id == Client.id)
        .order_by(Print.date.desc(), Print.id.desc())
        .limit(RECENT_PRINTS_LIMIT)
        .all()
    )
    return [
        RecentPrintResponse(part_name=print_.part_name, client=client_name, date=print_.date, price=print_.price)
        for print_, client_name in rows
    ]


def get_monthly_spend(db: Session) -> float:
    today = date_type.today()
    total = (
        db.query(func.coalesce(func.sum(Print.cost), 0))
        .filter(func.extract("year", Print.date) == today.year, func.extract("month", Print.date) == today.month)
        .scalar()
    )
    return float(total)


def get_open_quotes_count(db: Session) -> int:
    return db.query(Quote).filter(Quote.status.in_(["pending", "sent"])).count()


@router.get("/", response_model=DashboardResponse)
def get_dashboard(db: Session = Depends(get_db)):
    return DashboardResponse(
        critical_spools=get_critical_spools(db),
        recent_prints=get_recent_prints(db),
        monthly_spend=get_monthly_spend(db),
        open_quotes=get_open_quotes_count(db),
    )
