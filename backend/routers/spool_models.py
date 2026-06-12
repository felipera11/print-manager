from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from database import get_db
from models import SpoolModel

router = APIRouter()


class SpoolModelBase(BaseModel):
    name: str
    weight_g: float


class SpoolModelResponse(SpoolModelBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


def get_spool_model_or_404(spool_model_id: int, db: Session) -> SpoolModel:
    spool_model = db.get(SpoolModel, spool_model_id)
    if spool_model is None:
        raise HTTPException(status_code=404, detail="Spool model not found")
    return spool_model


@router.get("/", response_model=list[SpoolModelResponse])
def list_spool_models(db: Session = Depends(get_db)):
    return db.query(SpoolModel).all()


@router.get("/{spool_model_id}", response_model=SpoolModelResponse)
def get_spool_model(spool_model_id: int, db: Session = Depends(get_db)):
    return get_spool_model_or_404(spool_model_id, db)


@router.post("/", response_model=SpoolModelResponse, status_code=201)
def create_spool_model(spool_model: SpoolModelBase, db: Session = Depends(get_db)):
    db_spool_model = SpoolModel(**spool_model.model_dump())
    db.add(db_spool_model)
    db.commit()
    db.refresh(db_spool_model)
    return db_spool_model


@router.put("/{spool_model_id}", response_model=SpoolModelResponse)
def update_spool_model(spool_model_id: int, spool_model: SpoolModelBase, db: Session = Depends(get_db)):
    db_spool_model = get_spool_model_or_404(spool_model_id, db)
    for field, value in spool_model.model_dump().items():
        setattr(db_spool_model, field, value)
    db.commit()
    db.refresh(db_spool_model)
    return db_spool_model


@router.delete("/{spool_model_id}", status_code=204)
def delete_spool_model(spool_model_id: int, db: Session = Depends(get_db)):
    db_spool_model = get_spool_model_or_404(spool_model_id, db)
    db.delete(db_spool_model)
    db.commit()
