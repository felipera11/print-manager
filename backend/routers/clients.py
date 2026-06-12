from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from database import get_db
from models import Client

router = APIRouter()


class ClientBase(BaseModel):
    name: str
    email: str
    cnpj: str
    address: str | None = None
    mobile: str
    phone: str | None = None


class ClientResponse(ClientBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


def get_client_or_404(client_id: int, db: Session) -> Client:
    client = db.get(Client, client_id)
    if client is None:
        raise HTTPException(status_code=404, detail="Client not found")
    return client


@router.get("/", response_model=list[ClientResponse])
def list_clients(db: Session = Depends(get_db)):
    return db.query(Client).all()


@router.get("/{client_id}", response_model=ClientResponse)
def get_client(client_id: int, db: Session = Depends(get_db)):
    return get_client_or_404(client_id, db)


@router.post("/", response_model=ClientResponse, status_code=201)
def create_client(client: ClientBase, db: Session = Depends(get_db)):
    db_client = Client(**client.model_dump())
    db.add(db_client)
    db.commit()
    db.refresh(db_client)
    return db_client


@router.put("/{client_id}", response_model=ClientResponse)
def update_client(client_id: int, client: ClientBase, db: Session = Depends(get_db)):
    db_client = get_client_or_404(client_id, db)
    for field, value in client.model_dump().items():
        setattr(db_client, field, value)
    db.commit()
    db.refresh(db_client)
    return db_client


@router.delete("/{client_id}", status_code=204)
def delete_client(client_id: int, db: Session = Depends(get_db)):
    db_client = get_client_or_404(client_id, db)
    db.delete(db_client)
    db.commit()
