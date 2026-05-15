const API_BASE = '/api';

export interface Trip {
  id: string;
  destination: string;
  description: string;
  duration: number;
}

export async function getTrips(): Promise<Trip[]> {
  const response = await fetch(`${API_BASE}/trips`);
  if (!response.ok) {
    throw new Error('Failed to fetch trips');
  }
  return response.json();
}

export async function createTrip(trip: Omit<Trip, 'id'>): Promise<Trip> {
  const response = await fetch(`${API_BASE}/trips`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(trip),
  });
  if (!response.ok) {
    throw new Error('Failed to create trip');
  }
  return response.json();
}

export async function deleteTrip(tripId: string): Promise<void> {
  const response = await fetch(`${API_BASE}/trips/${tripId}`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    throw new Error('Failed to delete trip');
  }
}

// Made with Bob
