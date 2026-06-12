from sqlalchemy import Boolean, Column, Date, ForeignKey, Integer, Numeric, String, Text

from database import Base


class Printer(Base):
    __tablename__ = "printers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    brand = Column(String(100), nullable=False)
    hourly_cost = Column(Numeric(10, 2), nullable=False)
    active = Column(Boolean, nullable=False, default=True)


class FilamentType(Base):
    __tablename__ = "filament_types"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String(50), nullable=False)
    brand = Column(String(100), nullable=False)
    cost_per_kg = Column(Numeric(10, 2), nullable=False)


class SpoolModel(Base):
    __tablename__ = "spool_models"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    weight_g = Column(Numeric(10, 2), nullable=False)


class Spool(Base):
    __tablename__ = "spools"

    id = Column(Integer, primary_key=True, index=True)
    number = Column(Integer, nullable=False)
    type_id = Column(Integer, ForeignKey("filament_types.id"), nullable=False)
    color = Column(String(50), nullable=False)
    spool_model_id = Column(Integer, ForeignKey("spool_models.id"), nullable=False)
    total_weight_g = Column(Numeric(10, 2), nullable=False)
    remaining_weight_g = Column(Numeric(10, 2), nullable=False)
    reserved_weight_g = Column(Numeric(10, 2), nullable=False, default=0)


class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    email = Column(String(150), nullable=False)
    cnpj = Column(String(20), nullable=False)
    address = Column(String(255))
    mobile = Column(String(20), nullable=False)
    phone = Column(String(20))


class Print(Base):
    __tablename__ = "prints"

    id = Column(Integer, primary_key=True, index=True)
    part_name = Column(String(150), nullable=False)
    printer_id = Column(Integer, ForeignKey("printers.id"), nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    weight_g = Column(Numeric(10, 2), nullable=False)
    time_h = Column(Numeric(10, 2), nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    date = Column(Date, nullable=False)
    notes = Column(Text)
    status = Column(String(20), nullable=False, default="queued")
    queue_position = Column(Integer, nullable=False, default=0)


class PrintSpool(Base):
    __tablename__ = "print_spools"

    print_id = Column(Integer, ForeignKey("prints.id"), primary_key=True)
    spool_id = Column(Integer, ForeignKey("spools.id"), primary_key=True)
