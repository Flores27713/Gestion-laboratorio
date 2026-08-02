from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class Item(Base):
    __tablename__ = "item"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    location = Column(String, nullable=False)
    stock = Column(Integer, default=0, nullable=False)
    in_use = Column(Integer, default=0, nullable=False)
    damaged = Column(Integer, default=0, nullable=False)
    avail = Column(Integer, default=0, nullable=False)
    cost_center = Column(String, nullable=False, default="Industrial")
    category = Column(String, nullable=False, default="General")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "location": self.location,
            "stock": self.stock,
            "in_use": self.in_use,
            "damaged": self.damaged,
            "avail": self.avail,
            "cost_center": self.cost_center,
            "category": self.category
        }

class Requisition(Base):
    __tablename__ = "requisition"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True, nullable=False)
    applicant = Column(String, nullable=False)
    rut = Column(String, nullable=False)
    career = Column(String, nullable=False)
    course = Column(String, nullable=False)
    professor = Column(String, nullable=True)
    date = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    return_date = Column(String, nullable=False)
    status = Column(String, default="ACTIVO", nullable=False) # ACTIVO, DEVUELTO

    items = relationship("RequisitionItem", back_populates="requisition", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "code": self.code,
            "applicant": self.applicant,
            "rut": self.rut,
            "career": self.career,
            "course": self.course,
            "professor": self.professor,
            "date": self.date.strftime("%Y-%m-%d") if self.date else "",
            "return_date": self.return_date,
            "status": self.status,
            "items": [item.to_dict() for item in self.items]
        }

class RequisitionItem(Base):
    __tablename__ = "requisition_item"

    id = Column(Integer, primary_key=True, index=True)
    requisition_id = Column(Integer, ForeignKey("requisition.id"), nullable=False)
    item_id = Column(Integer, ForeignKey("item.id"), nullable=False)
    item_name = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)

    requisition = relationship("Requisition", back_populates="items")
    item = relationship("Item")

    def to_dict(self):
        return {
            "id": self.id,
            "item_id": self.item_id,
            "item_name": self.item_name,
            "quantity": self.quantity
        }
