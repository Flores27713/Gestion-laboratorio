from typing import List, Optional
from pydantic import BaseModel, Field

class ItemBase(BaseModel):
    name: str
    location: str
    stock: int
    in_use: int = 0
    damaged: int = 0
    avail: int
    cost_center: str
    category: str

class ItemResponse(ItemBase):
    id: int

class RequisitionItemCreate(BaseModel):
    item_id: int
    quantity: int = Field(..., gt=0)

class RequisitionCreate(BaseModel):
    applicant: str
    rut: str
    career: str
    course: str
    professor: Optional[str] = None
    return_date: str
    items: List[RequisitionItemCreate]

class RequisitionItemResponse(BaseModel):
    id: int
    item_id: int
    item_name: str
    quantity: int

class RequisitionResponse(BaseModel):
    id: int
    code: str
    applicant: str
    rut: str
    career: str
    course: str
    professor: Optional[str] = None
    date: str
    return_date: str
    status: str
    items: List[RequisitionItemResponse]
