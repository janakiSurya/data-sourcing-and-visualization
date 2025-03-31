# schemas.py
from pydantic import BaseModel
from typing import Optional, List, Dict, Any, Union
from datetime import datetime

# Source filters
class SourceAFilter(BaseModel):
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    property_types: Optional[List[str]] = None
    locations: Optional[List[str]] = None
    min_listing_date: Optional[str] = None
    max_listing_date: Optional[str] = None

class SourceBFilter(BaseModel):
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    property_types: Optional[List[str]] = None
    locations: Optional[List[str]] = None
    min_bedrooms: Optional[int] = None
    max_bedrooms: Optional[int] = None

# Task schemas
class TaskCreate(BaseModel):
    name: str
    source_a_enabled: bool = True
    source_b_enabled: bool = True
    source_a_filters: Optional[SourceAFilter] = None
    source_b_filters: Optional[SourceBFilter] = None

class TaskResponse(BaseModel):
    id: int
    name: str
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True

# Property listing schema
class PropertyListing(BaseModel):
    id: int
    property_id: str
    task_id: int
    data_source: str
    location: str
    property_type: str
    price: float
    bedrooms: int
    bathrooms: float
    square_feet: float
    listing_date: str
    description: Optional[str] = None
    
    class Config:
        orm_mode = True