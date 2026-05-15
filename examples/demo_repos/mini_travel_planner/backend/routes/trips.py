from fastapi import APIRouter, HTTPException
from models.trip import Trip, TripCreate
from services.recommendations import get_recommendations

router = APIRouter()

# In-memory storage for demo purposes
trips_db: dict[str, Trip] = {}


@router.get("/trips")
async def list_trips():
    """Get all saved trips."""
    return list(trips_db.values())


@router.post("/trips")
async def create_trip(trip: TripCreate):
    """Save a new trip."""
    trip_id = f"trip_{len(trips_db) + 1}"
    new_trip = Trip(id=trip_id, **trip.model_dump())
    trips_db[trip_id] = new_trip
    return new_trip


@router.delete("/trips/{trip_id}")
async def delete_trip(trip_id: str):
    """Delete a saved trip."""
    if trip_id not in trips_db:
        raise HTTPException(status_code=404, detail="Trip not found")
    del trips_db[trip_id]
    return {"message": "Trip deleted successfully"}


@router.get("/recommendations")
async def get_trip_recommendations(destination: str | None = None):
    """Get trip recommendations based on destination."""
    recommendations = get_recommendations(destination)
    return recommendations

# Made with Bob
