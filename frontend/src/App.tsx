import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import HomePage from './pages/home/HomePage';
import UploadPage from './pages/upload/UploadPage';
import NavLink from './components/navigation/NavLink';
import './App.css';

function App() {
  return (
    <Router>
      <div className="App">
        <nav className="navbar">
          <div className="nav-container">
            <Link to="/" className="nav-logo">
              VisionMorph
            </Link>
            <div className="nav-menu">
              <Link to="/" className="nav-link">首页</Link>
              <NavLink to="/upload" className="nav-link">智能构图</NavLink>
            </div>
          </div>
        </nav>
        
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/upload" element={<UploadPage />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;