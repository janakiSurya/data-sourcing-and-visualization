# app.py
from fastapi import FastAPI, BackgroundTasks, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import models, schemas, database, queue_manager
from typing import List, Optional
import time
import pandas as pd
import json
import csv
import random
import datetime
import os
from pathlib import Path

# Initialize FastAPI app
app = FastAPI(title="Real Estate Data Hub")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database initialization
models.Base.metadata.create_all(bind=database.engine)

# Get DB session
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Task queue initialization
task_queue = queue_manager.TaskQueue()


@app.post("/tasks/", response_model=schemas.TaskResponse)
async def create_task(task: schemas.TaskCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Create a new data retrieval task with specified filters"""
    
    
    db_task = models.Task(
        name=task.name,
        status="pending",
        source_a_enabled=task.source_a_enabled,
        source_b_enabled=task.source_b_enabled,
        source_a_filters=task.source_a_filters.dict() if task.source_a_filters else None,
        source_b_filters=task.source_b_filters.dict() if task.source_b_filters else None,
        created_at=datetime.datetime.now()
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    
    
    background_tasks.add_task(
        task_queue.process_task, 
        db_task.id, 
        task.source_a_enabled,
        task.source_b_enabled,
        task.source_a_filters.dict() if task.source_a_filters else None,
        task.source_b_filters.dict() if task.source_b_filters else None
    )
    
    return schemas.TaskResponse(
        id=db_task.id,
        name=db_task.name,
        status=db_task.status,
        created_at=db_task.created_at
    )

@app.get("/tasks/", response_model=List[schemas.TaskResponse])
async def get_tasks(db: Session = Depends(get_db)):
    """Get all tasks"""
    tasks = db.query(models.Task).all()
    return tasks

@app.get("/tasks/{task_id}", response_model=schemas.TaskResponse)
async def get_task(task_id: int, db: Session = Depends(get_db)):
    """Get a specific task by ID"""
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@app.delete("/tasks/{task_id}", response_model=schemas.TaskResponse)
async def delete_task(task_id: int, db: Session = Depends(get_db)):
    """Delete a task and its associated property listings"""
    
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    
    
    db.query(models.PropertyListing).filter(models.PropertyListing.task_id == task_id).delete()
    
    
    task_data = {
        "id": task.id,
        "name": task.name,
        "status": task.status,
        "created_at": task.created_at,
        "completed_at": task.completed_at
    }
    
    
    db.delete(task)
    db.commit()
    
    return schemas.TaskResponse(**task_data)

@app.get("/tasks/{task_id}/data", response_model=List[schemas.PropertyListing])
async def get_task_data(
    task_id: int, 
    db: Session = Depends(get_db),
    limit: Optional[int] = 100,
    property_type: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    location: Optional[str] = None
):
   
    
  
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.status != "completed":
        raise HTTPException(status_code=400, detail="Task not yet completed")
    
 
    query = db.query(models.PropertyListing).filter(models.PropertyListing.task_id == task_id)
    
    if property_type:
        query = query.filter(models.PropertyListing.property_type == property_type)
    if min_price:
        query = query.filter(models.PropertyListing.price >= min_price)
    if max_price:
        query = query.filter(models.PropertyListing.price <= max_price)
    if location:
        query = query.filter(models.PropertyListing.location.like(f"%{location}%"))
    
    listings = query.limit(limit).all()
    return listings

@app.get("/tasks/{task_id}/analytics")
async def get_task_analytics(task_id: int, db: Session = Depends(get_db)):
   
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.status != "completed":
        raise HTTPException(status_code=400, detail="Task not yet completed")
    
   
    listings = db.query(models.PropertyListing).filter(models.PropertyListing.task_id == task_id).all()
    
    if not listings:
        return {
            "task_id": task_id,
            "count": 0,
            "analytics": {}
        }
    
    
    price_by_location = {}
    price_by_type = {}
    listings_by_month = {}
    bedroom_distribution = {1: 0, 2: 0, 3: 0, 4: 0, "5+": 0}
    
    for listing in listings:
      
        if listing.location in price_by_location:
            price_by_location[listing.location].append(listing.price)
        else:
            price_by_location[listing.location] = [listing.price]
        
       
        if listing.property_type in price_by_type:
            price_by_type[listing.property_type].append(listing.price)
        else:
            price_by_type[listing.property_type] = [listing.price]
        
      
        listing_date = datetime.datetime.strptime(listing.listing_date, "%Y-%m-%d")
        month_key = f"{listing_date.year}-{listing_date.month:02d}"
        if month_key in listings_by_month:
            listings_by_month[month_key] += 1
        else:
            listings_by_month[month_key] = 1
        
       
        bedrooms = listing.bedrooms
        if bedrooms >= 5:
            bedroom_distribution["5+"] += 1
        else:
            bedroom_distribution[bedrooms] += 1
    
    
    avg_price_by_location = {loc: sum(prices)/len(prices) for loc, prices in price_by_location.items()}
    avg_price_by_type = {t: sum(prices)/len(prices) for t, prices in price_by_type.items()}
    

    sorted_listings_by_month = {k: listings_by_month[k] for k in sorted(listings_by_month.keys())}
    
    return {
        "task_id": task_id,
        "count": len(listings),
        "analytics": {
            "avg_price_by_location": avg_price_by_location,
            "avg_price_by_type": avg_price_by_type,
            "listings_by_month": sorted_listings_by_month,
            "bedroom_distribution": bedroom_distribution
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)