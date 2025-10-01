import React from 'react';
import { useNavigate } from 'react-router-dom';
import './HomePage.css';

const HomePage: React.FC = () => {
  const navigate = useNavigate();

  const handleStartUpload = () => {
    navigate('/upload');
  };

  return (
    <div className="home-page">
      <div className="hero-section">
        <h1 className="hero-title">VisionMorph 智能构图系统</h1>
        <p className="hero-subtitle">
          基于AI的智能图像构图分析与优化平台
        </p>
        <div className="hero-features">
          <div className="feature-item">
            <div className="feature-icon">🎨</div>
            <h3>智能构图分析</h3>
            <p>AI驱动的图像构图质量评估</p>
          </div>
          <div className="feature-item">
            <div className="feature-icon">⚡</div>
            <h3>实时处理</h3>
            <p>快速上传和处理您的图像</p>
          </div>
          <div className="feature-item">
            <div className="feature-icon">📊</div>
            <h3>详细报告</h3>
            <p>获得专业的构图分析报告</p>
          </div>
        </div>
        <button className="cta-button" onClick={handleStartUpload}>
          开始上传图片
        </button>
      </div>
      
      <div className="info-section">
        <h2>如何使用</h2>
        <div className="steps">
          <div className="step">
            <div className="step-number">1</div>
            <h3>上传图片</h3>
            <p>选择或拖拽您的图片文件</p>
          </div>
          <div className="step">
            <div className="step-number">2</div>
            <h3>AI分析</h3>
            <p>系统自动分析构图质量</p>
          </div>
          <div className="step">
            <div className="step-number">3</div>
            <h3>查看结果</h3>
            <p>获得详细的构图分析报告</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default HomePage;