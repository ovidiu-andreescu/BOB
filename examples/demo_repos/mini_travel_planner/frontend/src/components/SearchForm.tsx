import { useState } from 'react';

interface SearchFormProps {
  onSearch: () => void;
}

function SearchForm({ onSearch }: SearchFormProps) {
  const [destination, setDestination] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (destination.trim()) {
      onSearch();
    }
  };

  return (
    <form onSubmit={handleSubmit} className="search-form">
      <input
        type="text"
        value={destination}
        onChange={(e) => setDestination(e.target.value)}
        placeholder="Search for a destination..."
        className="search-input"
      />
      <button type="submit" className="search-btn">
        Search
      </button>
    </form>
  );
}

export default SearchForm;

// Made with Bob
