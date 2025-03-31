# test_db.py
from database import engine, Base
import models

def test_database():
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")

if __name__ == "__main__":
    test_database()
    