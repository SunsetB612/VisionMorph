import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import HomePage from './pages/home/HomePage';
import UploadPage from './pages/upload/UploadPage';
import GenerationPage from './pages/generation/GenerationPage';
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
              <Link to="/upload" className="nav-link">上传</Link>
              <Link to="/generate" className="nav-link">生成</Link>
            </div>
          </div>
        </nav>
        
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/upload" element={<UploadPage />} />
          <Route path="/generate" element={<GenerationPage />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;