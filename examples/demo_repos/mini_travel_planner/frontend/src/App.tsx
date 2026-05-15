import { BrowserRouter, Routes, Route } from 'react-router-dom';
import TripsPage from './pages/TripsPage';
import './App.css';

function App() {
  return (
    <BrowserRouter>
      <div className="app">
        <header className="app-header">
          <h1>Mini Travel Planner</h1>
        </header>
        <main className="app-main">
          <Routes>
            <Route path="/" element={<TripsPage />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;

// Made with Bob
