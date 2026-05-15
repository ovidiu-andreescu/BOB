import { useState, useEffect } from 'react';
import TripCard from '../components/TripCard';
import SearchForm from '../components/SearchForm';
import { getTrips, deleteTrip } from '../services/api';

interface Trip {
  id: string;
  destination: string;
  description: string;
  duration: number;
}

function TripsPage() {
  const [trips, setTrips] = useState<Trip[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadTrips();
  }, []);

  const loadTrips = async () => {
    try {
      setLoading(true);
      const data = await getTrips();
      setTrips(data);
    } catch (error) {
      console.error('Failed to load trips:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (tripId: string) => {
    try {
      await deleteTrip(tripId);
      setTrips(trips.filter(trip => trip.id !== tripId));
    } catch (error) {
      console.error('Failed to delete trip:', error);
    }
  };

  return (
    <div className="trips-page">
      <SearchForm onSearch={loadTrips} />
      
      <div className="trips-list">
        <h2>Your Saved Trips</h2>
        {loading ? (
          <p>Loading trips...</p>
        ) : trips.length === 0 ? (
          <p>No trips saved yet. Search for destinations above!</p>
        ) : (
          trips.map(trip => (
            <TripCard
              key={trip.id}
              trip={trip}
              onDelete={handleDelete}
            />
          ))
        )}
      </div>
    </div>
  );
}

export default TripsPage;

// Made with Bob
