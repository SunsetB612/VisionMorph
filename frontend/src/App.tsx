import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import { useEffect } from 'react';
import HomePage from './pages/home/HomePage';
import UploadPage from './pages/upload/UploadPage';
import AuthPage from './pages/auth/AuthPage';
import NavLink from './components/navigation/NavLink';
import ProtectedRoute from './components/auth/ProtectedRoute';
import PublicRoute from './components/auth/PublicRoute';
import { useAuthStore } from './store/authStore';
import './App.css';

function AppContent() {
  const { user, isAuthenticated, logout, checkAuth } = useAuthStore();
  const location = useLocation();

  // 检查认证状态，但不在认证页面调用
  useEffect(() => {
    if (location.pathname !== '/auth') {
      checkAuth();
    }
  }, [checkAuth, location.pathname]);

  return (
    <div className="App">
      <nav className="navbar">
        <div className="nav-container">
          <Link to="/" className="nav-logo">
            VisionMorph
          </Link>
          <div className="nav-menu">
            <Link to="/" className="nav-link">首页</Link>
            {isAuthenticated && (
              <NavLink to="/upload" className="nav-link">智能构图</NavLink>
            )}
            {isAuthenticated ? (
              <div className="user-menu">
                <span className="user-name">欢迎，{user?.username}</span>
                <button onClick={logout} className="logout-btn">退出</button>
              </div>
            ) : (
              <div className="auth-menu">
                <Link to="/auth" className="nav-link">登录/注册</Link>
              </div>
            )}
          </div>
        </div>
      </nav>
      
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route 
          path="/upload" 
          element={
            <ProtectedRoute>
              <UploadPage />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/auth" 
          element={
            <PublicRoute>
              <AuthPage />
            </PublicRoute>
          } 
        />
      </Routes>
    </div>
  );
}

function App() {
  return (
    <Router>
      <AppContent />
    </Router>
  );
}

export default App;