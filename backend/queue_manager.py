# queue_manager.py
import time
import random
import json
import csv
import datetime
import pandas as pd
from sqlalchemy.orm import Session
from database import SessionLocal
import models
from typing import Dict, Any, List, Optional
import os
from pathlib import Path
import threading
import queue

class TaskQueue:

    
    def __init__(self):
        
        self._ensure_data_files()
        self.task_queue = queue.Queue()
        self.is_processing = False
        self.lock = threading.Lock()
        # Start queue processor thread
        self.processor_thread = threading.Thread(target=self._process_queue, daemon=True)
        self.processor_thread.start()
    
    def _ensure_data_files(self):
       
        data_dir = Path("../data")
        data_dir.mkdir(exist_ok=True)
        
        json_file = data_dir / "source_a_listings.json"
        if not json_file.exists():
            self._create_sample_json_data(json_file)
        
        csv_file = data_dir / "source_b_listings.csv"
        if not csv_file.exists():
            self._create_sample_csv_data(csv_file)
    
    def _create_sample_json_data(self, file_path: Path):
        
        
        locations = ["San Francisco", "New York", "Boston", "Chicago", "Seattle", "Austin", "Denver"]
        property_types = ["Apartment", "House", "Condo", "Townhouse", "Duplex"]
        
        # Generate records
        records = []
        for i in range(1, 501):
            listing_year = random.choice([2022, 2023, 2024, 2025])
            listing_month = random.randint(1, 12)
            listing_day = random.randint(1, 28)
            
            records.append({
                "property_id": f"A-{i:04d}",
                "location": random.choice(locations),
                "property_type": random.choice(property_types),
                "price": round(random.uniform(300000, 2000000), 2),
                "bedrooms": random.randint(1, 6),
                "bathrooms": random.choice([1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]),
                "square_feet": round(random.uniform(500, 4000)),
                "listing_date": f"{listing_year}-{listing_month:02d}-{listing_day:02d}",
                "description": f"Sample property {i} from Source A. This is a great property with amazing features."
            })
        
       
        with open(file_path, 'w') as f:
            json.dump(records, f, indent=2)
    
    def _create_sample_csv_data(self, file_path: Path):
      
        
        locations = ["Los Angeles", "Miami", "Portland", "Dallas", "Atlanta", "San Diego", "Phoenix"]
        property_types = ["Apartment", "House", "Condo", "Townhouse", "Loft"]
        
        
        header = ["property_id", "location", "property_type", "price", "bedrooms", 
                  "bathrooms", "square_feet", "listing_date", "description"]
        
        
        records = []
        for i in range(1, 501):
            listing_year = random.choice([2022, 2023, 2024, 2025])
            listing_month = random.randint(1, 12)
            listing_day = random.randint(1, 28)
            
            records.append([
                f"B-{i:04d}",
                random.choice(locations),
                random.choice(property_types),
                round(random.uniform(250000, 1800000), 2),
                random.randint(1, 6),
                random.choice([1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]),
                round(random.uniform(600, 3800)),
                f"{listing_year}-{listing_month:02d}-{listing_day:02d}",
                f"Sample property {i} from Source B. Located in a prime area with great amenities."
            ])
        
        
        with open(file_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerows(records)
    
    def _fetch_source_a_data(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
       
        
        file_path = "../data/source_a_listings.json"
        with open(file_path, 'r') as f:
            data = json.load(f)
        
    
        if filters:
            filtered_data = []
            for item in data:
                if filters.get('min_price') and item['price'] < filters['min_price']:
                    continue
                if filters.get('max_price') and item['price'] > filters['max_price']:
                    continue
                
                if filters.get('property_types') and item['property_type'] not in filters['property_types']:
                    continue
                
                if filters.get('locations') and item['location'] not in filters['locations']:
                    continue
                
                if filters.get('min_listing_date') and item['listing_date'] < filters['min_listing_date']:
                    continue
                if filters.get('max_listing_date') and item['listing_date'] > filters['max_listing_date']:
                    continue
                
                filtered_data.append(item)
            
            return filtered_data
        
        return data
    
    def _fetch_source_b_data(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Fetch data from Source B (CSV) with optional filtering"""
        
        file_path = "../data/source_b_listings.csv"
        df = pd.read_csv(file_path)
        
       
        if filters:
            if 'min_price' in filters:
                df = df[df['price'] >= filters['min_price']]
            if 'max_price' in filters:
                df = df[df['price'] <= filters['max_price']]
            
            if 'property_types' in filters and filters['property_types']:
                df = df[df['property_type'].isin(filters['property_types'])]
            
            if 'locations' in filters and filters['locations']:
                df = df[df['location'].isin(filters['locations'])]
            
            if 'min_bedrooms' in filters:
                df = df[df['bedrooms'] >= filters['min_bedrooms']]
            if 'max_bedrooms' in filters:
                df = df[df['bedrooms'] <= filters['max_bedrooms']]
        
        # Convert to list of dictionaries
        return df.to_dict('records')
    
    def enqueue_task(
        self, 
        task_id: int, 
        source_a_enabled: bool, 
        source_b_enabled: bool,
        source_a_filters: Optional[Dict[str, Any]], 
        source_b_filters: Optional[Dict[str, Any]]
    ):
        """Add a task to the processing queue"""
        task_data = {
            'task_id': task_id,
            'source_a_enabled': source_a_enabled,
            'source_b_enabled': source_b_enabled,
            'source_a_filters': source_a_filters,
            'source_b_filters': source_b_filters,
            'added_at': datetime.datetime.now()
        }
        
        self.task_queue.put(task_data)
        print(f"Task {task_id} added to the queue. Current queue size: {self.task_queue.qsize()}")
    
    def _process_queue(self):
        while True:
            try:
                # Get the next task from the queue (blocks until a task is available)
                task_data = self.task_queue.get()
                
                # Set processing flag
                with self.lock:
                    self.is_processing = True
                
                # Process the task
                self._process_task(
                    task_data['task_id'],
                    task_data['source_a_enabled'],
                    task_data['source_b_enabled'],
                    task_data['source_a_filters'],
                    task_data['source_b_filters']
                )
                
                # Mark task as done in the queue
                self.task_queue.task_done()
                
                # Reset processing flag
                with self.lock:
                    self.is_processing = False
                
            except Exception as e:
                print(f"Error in queue processor: {str(e)}")
                # Reset processing flag on error
                with self.lock:
                    self.is_processing = False
                
                # Brief pause before continuing
                time.sleep(1)
    
    def process_task(
        self, 
        task_id: int, 
        source_a_enabled: bool, 
        source_b_enabled: bool,
        source_a_filters: Optional[Dict[str, Any]], 
        source_b_filters: Optional[Dict[str, Any]]
    ):
        """Add task to the queue (used by the API endpoint)"""
        self.enqueue_task(
            task_id,
            source_a_enabled,
            source_b_enabled,
            source_a_filters,
            source_b_filters
        )
    
    def _process_task(
        self, 
        task_id: int, 
        source_a_enabled: bool, 
        source_b_enabled: bool,
        source_a_filters: Optional[Dict[str, Any]], 
        source_b_filters: Optional[Dict[str, Any]]
    ):
        """Process a task by fetching data from sources and storing in the database"""
        
        # Get a database session
        db = SessionLocal()
        
        try:
            # Get the task (task already created with 'pending' status in the API endpoint)
            task = db.query(models.Task).filter(models.Task.id == task_id).first()
            if not task:
                print(f"Task {task_id} not found")
                return
            
            # Simulate initial processing delay (1.5 seconds)
            print(f"Task {task_id} is pending, preparing to process...")
            time.sleep(1.5)
            
            task.status = "in_progress"
            db.commit()
            print(f"Task {task_id} is now in progress")
            
            time.sleep(random.uniform(2, 4))
            
            all_listings = []
            
            try:
                if source_a_enabled:
                    print(f"Task {task_id}: Fetching data from Source A...")
                    source_a_data = self._fetch_source_a_data(source_a_filters)
                    for item in source_a_data:
                        all_listings.append({
                            **item,
                            "data_source": "source_a",
                            "task_id": task_id
                        })
                    print(f"Task {task_id}: Retrieved {len(source_a_data)} listings from Source A")
            except Exception as e:
                print(f"Error fetching data from Source A: {str(e)}")
                raise
            
            try:
                if source_b_enabled:
                    print(f"Task {task_id}: Fetching data from Source B...")
                    source_b_data = self._fetch_source_b_data(source_b_filters)
                    for item in source_b_data:
                        all_listings.append({
                            **item,
                            "data_source": "source_b",
                            "task_id": task_id
                        })
                    print(f"Task {task_id}: Retrieved {len(source_b_data)} listings from Source B")
            except Exception as e:
                print(f"Error fetching data from Source B: {str(e)}")
                raise
            
            # Simulate data processing delay (1-3 seconds)
            print(f"Task {task_id}: Processing {len(all_listings)} listings...")
            time.sleep(random.uniform(1, 3))
            
            # Insert listings into the database
            try:
                for listing in all_listings:
                    db_listing = models.PropertyListing(
                        property_id=listing["property_id"],
                        task_id=task_id,
                        data_source=listing["data_source"],
                        location=listing["location"],
                        property_type=listing["property_type"],
                        price=listing["price"],
                        bedrooms=listing["bedrooms"],
                        bathrooms=listing["bathrooms"],
                        square_feet=listing["square_feet"],
                        listing_date=listing["listing_date"],
                        description=listing["description"]
                    )
                    db.add(db_listing)
                
                # Commit all listings
                db.commit()
            except Exception as e:
                print(f"Error inserting listings: {str(e)}")
                db.rollback()
                raise
            
            # Update task status to completed
            task.status = "completed"
            task.completed_at = datetime.datetime.now()
            db.commit()
            
            print(f"Task {task_id} completed successfully with {len(all_listings)} listings")
            
        except Exception as e:
            print(f"Error processing task {task_id}: {str(e)}")
            try:
                task = db.query(models.Task).filter(models.Task.id == task_id).first()
                if task:
                    task.status = "failed"
                    db.commit()
            except Exception as inner_e:
                print(f"Error updating task status to failed: {str(inner_e)}")
        finally:
            db.close()