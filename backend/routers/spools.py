from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from database import get_db
from models import Spool, SpoolModel

router = APIRouter()


class SpoolBase(BaseModel):
    type_id: int
    number: int
    color: str
    spool_model_id: int
    total_weight_g: float


class SpoolResponse(SpoolBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    remaining_weight_g: float


def get_spool_or_404(spool_id: int, db: Session) -> Spool:
    spool = db.get(Spool, spool_id)
    if spool is None:
        raise HTTPException(status_code=404, detail="Spool not found")
    return spool


def get_spool_model_weight(spool_model_id: int, db: Session) -> float:
    spool_model = db.get(SpoolModel, spool_model_id)
    if spool_model is None:
        raise HTTPException(status_code=404, detail="Spool model not found")
    return float(spool_model.weight_g)


@router.get("/", response_model=list[SpoolResponse])
def list_spools(db: Session = Depends(get_db)):
    return db.query(Spool).all()


@router.get("/suggest", response_model=list[SpoolResponse])
def suggest_spools(weight_g: float, type_id: int, db: Session = Depends(get_db)):
    return (
        db.query(Spool)
        .filter(Spool.type_id == type_id, Spool.remaining_weight_g >= weight_g)
        .order_by(Spool.remaining_weight_g.asc())
        .all()
    )


@router.get("/{spool_id}", response_model=SpoolResponse)
def get_spool(spool_id: int, db: Session = Depends(get_db)):
    return get_spool_or_404(spool_id, db)


@router.post("/", response_model=SpoolResponse, status_code=201)
def create_spool(spool: SpoolBase, db: Session = Depends(get_db)):
    spool_model_weight_g = get_spool_model_weight(spool.spool_model_id, db)
    db_spool = Spool(
        **spool.model_dump(),
        remaining_weight_g=spool.total_weight_g - spool_model_weight_g,
    )
    db.add(db_spool)
    db.commit()
    db.refresh(db_spool)
    return db_spool


@router.put("/{spool_id}", response_model=SpoolResponse)
def update_spool(spool_id: int, spool: SpoolBase, db: Session = Depends(get_db)):
    db_spool = get_spool_or_404(spool_id, db)
    spool_model_weight_g = get_spool_model_weight(spool.spool_model_id, db)
    for field, value in spool.model_dump().items():
        setattr(db_spool, field, value)
    db_spool.remaining_weight_g = spool.total_weight_g - spool_model_weight_g
    db.commit()
    db.refresh(db_spool)
    return db_spool


@router.delete("/{spool_id}", status_code=204)
def delete_spool(spool_id: int, db: Session = Depends(get_db)):
    db_spool = get_spool_or_404(spool_id, db)
    db.delete(db_spool)
    db.commit()
