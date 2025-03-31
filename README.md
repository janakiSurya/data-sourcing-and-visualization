A full-stack web application for Data sourcing and visualizing real estate data from multiple sources.

Features

- Created data retrieval tasks with customizable filters
- Sourced data from JSON and CSV files
- Background job queue for task processing
- Interactive data visualizations with D3.js
- Filtering and analytics on retrieved data

Backend

- FastAPI (Python)
- SQLAlchemy ORM
- SQLite Database
- Pandas for data processing

Frontend

- React with TypeScript
- React Router for navigation
- D3.js for data visualization
- TailwindCSS for styling
- Axios for API communication

Project Structure

fullstack-project/
├── backend/ # FastAPI server
│ ├── app.py  
│ ├── database.py  
│ ├── models.py  
│ ├── schemas.py  
│ └── queue_manager.py  
├── data/ # Data storage
│ ├── source_a_listings.json
│ ├── source_b_listings.csv  
│ └── realestate.db  
└── frontend/ # React application
├── public/  
 └── src/  
 ├── components/  
 ├── services/  
 └── types/

Installation and Setup

Automatic Startup (Recommended)
For a simpler startup process, use the provided script:
chmod +x start.sh  
 ./start.sh

Backend

1. Navigate to the backend directory:
   bash: cd backend

2. Create a virtual environment:
   bash: python -m venv venv

3. Activate the virtual environment:
   bash
   On Windows: venv\Scripts\activate
   On macOS/Linux: source venv/bin/activate

4. Install the dependencies:
   bash
   pip install fastapi uvicorn sqlalchemy pandas

5. Start the backend server:
   uvicorn app:app --reload

The backend server will run at http://localhost:8000

Frontend

1. Navigate to the frontend directory:
   cd frontend

2. Install the dependencies:
   npm install

3. Start the development server:
   npm start

The frontend application will run at http://localhost:3000

Usage

1. Open your browser and navigate to http://localhost:3000
2. Create a new data retrieval task with your desired filters
3. Wait for the task to complete (it takes a few seconds to simulate data processing)
4. View the retrieved data and explore the analytics visualizations
5. Apply additional filters on the data view page to narrow down results

More detailed API Documentation:
The backend API documentation is available at http://localhost:8000/docs when the server is running.
