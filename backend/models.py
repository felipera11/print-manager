from sqlalchemy import Boolean, Column, ForeignKey, Integer, Numeric, String

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
