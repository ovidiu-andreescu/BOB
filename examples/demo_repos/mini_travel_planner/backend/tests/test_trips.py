"""Tests for trip routes."""

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_list_trips_empty():
    """Test listing trips when none exist."""
    response = client.get("/api/trips")
    assert response.status_code == 200
    assert response.json() == []


def test_create_trip():
    """Test creating a new trip."""
    trip_data = {
        "destination": "Paris",
        "description": "City of lights",
        "duration": 5
    }
    response = client.post("/api/trips", json=trip_data)
    assert response.status_code == 200
    data = response.json()
    assert data["destination"] == "Paris"
    assert data["description"] == "City of lights"
    assert data["duration"] == 5
    assert "id" in data


def test_delete_trip():
    """Test deleting a trip."""
    # First create a trip
    trip_data = {
        "destination": "Tokyo",
        "description": "Modern metropolis",
        "duration": 7
    }
    create_response = client.post("/api/trips", json=trip_data)
    trip_id = create_response.json()["id"]
    
    # Then delete it
    delete_response = client.delete(f"/api/trips/{trip_id}")
    assert delete_response.status_code == 200
    assert delete_response.json()["message"] == "Trip deleted successfully"


def test_delete_nonexistent_trip():
    """Test deleting a trip that doesn't exist."""
    response = client.delete("/api/trips/nonexistent_id")
    assert response.status_code == 404
    assert response.json()["detail"] == "Trip not found"


def test_get_recommendations():
    """Test getting trip recommendations."""
    response = client.get("/api/recommendations")
    assert response.status_code == 200
    recommendations = response.json()
    assert isinstance(recommendations, list)
    assert len(recommendations) > 0


def test_get_recommendations_with_filter():
    """Test getting filtered trip recommendations."""
    response = client.get("/api/recommendations?destination=Paris")
    assert response.status_code == 200
    recommendations = response.json()
    assert isinstance(recommendations, list)

# Made with Bob
