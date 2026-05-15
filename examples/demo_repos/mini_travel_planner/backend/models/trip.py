from pydantic import BaseModel


class TripCreate(BaseModel):
    """Schema for creating a new trip."""
    destination: str
    description: str
    duration: int


class Trip(TripCreate):
    """Schema for a trip with ID."""
    id: str

# Made with Bob
