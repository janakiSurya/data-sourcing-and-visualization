#!/bin/bash

# Function to handle termination signals
function cleanup {
  echo "Stopping servers..."
  kill -TERM $FRONTEND_PID $BACKEND_PID 2>/dev/null
  exit 0
}

# Register the cleanup function for SIGINT and SIGTERM
trap cleanup SIGINT SIGTERM

# Start backend server
echo "Starting backend server..."
cd backend
source venv/bin/activate
uvicorn app:app --reload &
BACKEND_PID=$!
cd ..

# Start frontend server
echo "Starting frontend server..."
cd frontend
npm start &
FRONTEND_PID=$!
cd ..

echo "Servers started successfully!"
echo "Frontend: http://localhost:3000"
echo "Backend: http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
echo "Press Ctrl+C to stop both servers"

# Wait for both processes to finish
wait $FRONTEND_PID $BACKEND_PID 