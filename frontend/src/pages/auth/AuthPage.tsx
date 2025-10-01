import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../../store/authStore';
import './AuthPage.css';

const AuthPage: React.FC = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
  });
  const { login, register, isLoading } = useAuthStore();
  const navigate = useNavigate();

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value,
    }));
  };

  const showToast = (message: string, type: 'error' | 'success' = 'error') => {
    // 创建 toast 元素
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    
    // 添加样式
    Object.assign(toast.style, {
      position: 'fixed',
      top: '20px',
      left: '50%',
      transform: 'translateX(-50%)',
      padding: '12px 20px',
      borderRadius: '8px',
      color: 'white',
      fontSize: '14px',
      fontWeight: '500',
      zIndex: '9999',
      maxWidth: '400px',
      wordWrap: 'break-word',
      boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
      backgroundColor: type === 'error' ? '#ef4444' : '#10b981'
    });
    
    // 添加到页面
    document.body.appendChild(toast);
    
    // 3秒后自动消失
    setTimeout(() => {
      if (toast.parentNode) {
        toast.parentNode.removeChild(toast);
      }
    }, 3000);
  };

  const validateForm = () => {
    if (!isLogin) {
      if (formData.password !== formData.confirmPassword) {
        showToast('两次输入的密码不一致');
        return false;
      }
      if (formData.password.length < 6) {
        showToast('密码长度至少6位');
        return false;
      }
      if (formData.username.length < 3) {
        showToast('用户名长度至少3位');
        return false;
      }
      if (!/^[a-zA-Z0-9]+$/.test(formData.username)) {
        showToast('用户名只能包含字母和数字');
        return false;
      }
    }
    return true;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    try {
      if (isLogin) {
        await login({
          email: formData.email,
          password: formData.password,
        });
        // 登录成功，跳转到首页
        navigate('/');
      } else {
        await register({
          username: formData.username,
          email: formData.email,
          password: formData.password,
        });
        // 注册成功，跳转到首页
        navigate('/');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : `${isLogin ? '登录' : '注册'}失败`;
      showToast(errorMessage);
    }
  };

  const switchMode = () => {
    setIsLogin(!isLogin);
    setFormData({
      username: '',
      email: '',
      password: '',
      confirmPassword: '',
    });
  };

  return (
    <div className="auth-page">
      <div className="auth-container">
        <div className="auth-header">
          <h1>{isLogin ? '登录' : '注册'} VisionMorph</h1>
          <p>
            {isLogin 
              ? '欢迎回来！请登录您的账户' 
              : '创建您的账户，开始智能构图之旅'
            }
          </p>
        </div>

        <div className="auth-tabs">
          <button 
            className={`tab-button ${isLogin ? 'active' : ''}`}
            onClick={() => setIsLogin(true)}
          >
            登录
          </button>
          <button 
            className={`tab-button ${!isLogin ? 'active' : ''}`}
            onClick={() => setIsLogin(false)}
          >
            注册
          </button>
        </div>

        <form className="auth-form" onSubmit={handleSubmit}>

          {!isLogin && (
            <div className="form-group">
              <label htmlFor="username">用户名</label>
              <input
                type="text"
                id="username"
                name="username"
                value={formData.username}
                onChange={handleChange}
                required={!isLogin}
                placeholder="请输入用户名（3-20位字母数字）"
              />
            </div>
          )}

          <div className="form-group">
            <label htmlFor="email">邮箱地址</label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              required
              placeholder="请输入您的邮箱"
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">密码</label>
            <input
              type="password"
              id="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              required
              placeholder={isLogin ? "请输入您的密码" : "请输入密码（至少6位）"}
            />
          </div>

          {!isLogin && (
            <div className="form-group">
              <label htmlFor="confirmPassword">确认密码</label>
              <input
                type="password"
                id="confirmPassword"
                name="confirmPassword"
                value={formData.confirmPassword}
                onChange={handleChange}
                required={!isLogin}
                placeholder="请再次输入密码"
              />
            </div>
          )}

          <button 
            type="submit" 
            className="auth-button"
            disabled={isLoading}
          >
            {isLoading 
              ? (isLogin ? '登录中...' : '注册中...') 
              : (isLogin ? '登录' : '注册')
            }
          </button>
        </form>

        <div className="auth-footer">
          <p>
            {isLogin ? '还没有账户？' : '已有账户？'}{' '}
            <button 
              type="button"
              className="auth-link" 
              onClick={switchMode}
            >
              {isLogin ? '立即注册' : '立即登录'}
            </button>
          </p>
          <Link to="/" className="back-link">
            ← 返回首页
          </Link>
        </div>
      </div>
    </div>
  );
};

export default AuthPage;