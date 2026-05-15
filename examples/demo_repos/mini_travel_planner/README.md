# Mini Travel Planner

A small full-stack web application for searching and saving trip recommendations.

## Tech Stack

**Frontend:**
- React 18
- Vite
- TypeScript

**Backend:**
- FastAPI
- Python 3.11+
- Pydantic

## Features

- Search for trip destinations
- View trip recommendations
- Save favorite trips
- Delete saved trips

## Getting Started

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## API Endpoints

- `GET /trips` - List all saved trips
- `POST /trips` - Save a new trip
- `DELETE /trips/{trip_id}` - Delete a trip
- `GET /recommendations` - Get trip recommendations