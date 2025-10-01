import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useUploadStore } from '../../store/uploadStore';
import './HomePage.css';

const HomePage: React.FC = () => {
  const navigate = useNavigate();
  const { clearFiles } = useUploadStore();

  const handleStartUpload = () => {
    // 清理所有上传相关的状态，确保重新开始
    clearFiles();
    navigate('/upload');
  };

  return (
    <div className="home-page">
      <div className="hero-section">
        <h1 className="hero-title">VisionMorph 智能构图系统</h1>
        <p className="hero-subtitle">
          AI智能构图生成新视角图片，提供专业评分与拍摄指导
        </p>
        <div className="hero-features">
          <div className="feature-item">
            <div className="feature-icon">📸</div>
            <h3>上传图片</h3>
            <p>支持多种格式的图片上传</p>
          </div>
          <div className="feature-item">
            <div className="feature-icon">🎨</div>
            <h3>AI智能构图</h3>
            <p>AI生成新视角的构图图片</p>
          </div>
          <div className="feature-item">
            <div className="feature-icon">⭐</div>
            <h3>评分指导</h3>
            <p>专业评分、亮点分析与拍摄建议</p>
          </div>
        </div>
        <button className="cta-button" onClick={handleStartUpload}>
          开始智能构图
        </button>
      </div>
    </div>
  );
};

export default HomePage;