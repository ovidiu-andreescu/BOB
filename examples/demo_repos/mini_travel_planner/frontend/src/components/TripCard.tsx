interface TripCardProps {
  trip: {
    id: string;
    destination: string;
    description: string;
    duration: number;
  };
  onDelete: (id: string) => void;
}

function TripCard({ trip, onDelete }: TripCardProps) {
  return (
    <div className="trip-card">
      <h3>{trip.destination}</h3>
      <p>{trip.description}</p>
      <p className="duration">{trip.duration} days</p>
      <button onClick={() => onDelete(trip.id)} className="delete-btn">
        Delete
      </button>
    </div>
  );
}

export default TripCard;

// Made with Bob
