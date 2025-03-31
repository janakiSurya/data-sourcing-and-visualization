# models.py
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Float, DateTime, JSON
from sqlalchemy.orm import relationship
from database import Base
import datetime

class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    status = Column(String, default="pending")  # pending, in_progress, completed, failed
    source_a_enabled = Column(Boolean, default=True)
    source_b_enabled = Column(Boolean, default=True)
    source_a_filters = Column(JSON, nullable=True)
    source_b_filters = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    property_listings = relationship("PropertyListing", back_populates="task")

class PropertyListing(Base):
    __tablename__ = "property_listings"
    
    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(String, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"))
    data_source = Column(String)  # "source_a" or "source_b"
    
    # Common fields from both sources
    location = Column(String, index=True)
    property_type = Column(String, index=True)
    price = Column(Float, index=True)
    bedrooms = Column(Integer)
    bathrooms = Column(Float)
    square_feet = Column(Float)
    listing_date = Column(String, index=True)
    description = Column(String, nullable=True)
    
    task = relationship("Task", back_populates="property_listings")