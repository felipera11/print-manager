from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from database import get_db
from models import FilamentType

router = APIRouter()


class FilamentTypeBase(BaseModel):
    name: str
    temp_min: int
    temp_max: int


class FilamentTypeResponse(FilamentTypeBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


def get_filament_type_or_404(type_id: int, db: Session) -> FilamentType:
    filament_type = db.get(FilamentType, type_id)
    if filament_type is None:
        raise HTTPException(status_code=404, detail="Filament type not found")
    return filament_type


@router.get("/", response_model=list[FilamentTypeResponse])
def list_filament_types(db: Session = Depends(get_db)):
    return db.query(FilamentType).all()


@router.get("/{type_id}", response_model=FilamentTypeResponse)
def get_filament_type(type_id: int, db: Session = Depends(get_db)):
    return get_filament_type_or_404(type_id, db)


@router.post("/", response_model=FilamentTypeResponse, status_code=201)
def create_filament_type(filament_type: FilamentTypeBase, db: Session = Depends(get_db)):
    db_filament_type = FilamentType(**filament_type.model_dump())
    db.add(db_filament_type)
    db.commit()
    db.refresh(db_filament_type)
    return db_filament_type


@router.put("/{type_id}", response_model=FilamentTypeResponse)
def update_filament_type(type_id: int, filament_type: FilamentTypeBase, db: Session = Depends(get_db)):
    db_filament_type = get_filament_type_or_404(type_id, db)
    for field, value in filament_type.model_dump().items():
        setattr(db_filament_type, field, value)
    db.commit()
    db.refresh(db_filament_type)
    return db_filament_type


@router.delete("/{type_id}", status_code=204)
def delete_filament_type(type_id: int, db: Session = Depends(get_db)):
    db_filament_type = get_filament_type_or_404(type_id, db)
    db.delete(db_filament_type)
    db.commit()
