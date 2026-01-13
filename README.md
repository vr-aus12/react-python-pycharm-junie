# Todo List Application

A simple Todo List application with a FastAPI backend and a React + TypeScript frontend.

## Prerequisites

- Python 3.7+
- Node.js and npm

## Setup and Running

### Backend

1. Navigate to the `backend` directory:
   ```bash
   cd backend
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the backend server:
   ```bash
   python main.py
   ```
   The backend will be available at `http://localhost:8000`.

### Frontend

1. Navigate to the `frontend` directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Run the frontend development server:
   ```bash
   npm run dev
   ```
   The frontend will be available at the URL shown in your terminal (usually `http://localhost:5173`).

## Features

- Add new todos
- Mark todos as completed/uncompleted
- Delete todos
- Persistent state (while the backend is running)
