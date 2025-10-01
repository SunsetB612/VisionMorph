import React, { useState } from 'react';
import { useCamera } from '../../hooks/useCamera';
import './CameraComponent.css';

interface CameraComponentProps {
  onPhotoCaptured: (file: File) => void;
  onClose: () => void;
}

const CameraComponent: React.FC<CameraComponentProps> = ({
  onPhotoCaptured,
  onClose
}) => {
  const [isFlipping, setIsFlipping] = useState(false);
  
  const {
    isActive,
    isCapturing,
    error,
    isVideoReady,
    facingMode,
    videoRef,
    canvasRef,
    startCamera,
    stopCamera,
    capturePhoto,
    flipCamera
  } = useCamera();

  const handleStartCamera = async () => {
    try {
      await startCamera();
    } catch (error) {
      console.error('启动摄像头失败:', error);
    }
  };

  const handleCapture = async () => {
    try {
      const file = await capturePhoto();
      onPhotoCaptured(file);
    } catch (error) {
      console.error('拍照失败:', error);
      alert(`拍照失败: ${error instanceof Error ? error.message : '未知错误'}`);
    }
  };

  const handleClose = () => {
    stopCamera();
    onClose();
  };

  const handleFlipCamera = async () => {
    setIsFlipping(true);
    try {
      await flipCamera();
    } catch (error) {
      console.error('切换摄像头失败:', error);
    } finally {
      // 延迟重置切换状态，给用户足够时间看到反馈
      setTimeout(() => {
        setIsFlipping(false);
      }, 500);
    }
  };


  return (
    <div className="camera-overlay">
      <div className="camera-container">
        <div className="camera-header">
          <h3>拍照上传</h3>
          <button className="close-btn" onClick={handleClose}>
            ✕
          </button>
        </div>

        <div className="camera-content">
          {!isActive ? (
            <div className="camera-placeholder">
              <div className="camera-icon">📷</div>
              <p>点击开始使用摄像头</p>
              <button 
                className="start-camera-btn"
                onClick={handleStartCamera}
                disabled={isCapturing}
              >
                启动摄像头
              </button>
            </div>
          ) : (
            <div className="camera-preview">
              <video
                ref={videoRef}
                className="camera-video"
                autoPlay
                playsInline
                muted
                style={{ 
                  width: '100%', 
                  height: 'auto',
                  backgroundColor: '#000',
                  display: 'block'
                }}
              />
              <canvas
                ref={canvasRef}
                className="camera-canvas"
                style={{ display: 'none' }}
              />
              <div className="camera-status">
                {isFlipping ? (
                  <div className="status-flipping">🔄 切换摄像头中...</div>
                ) : isVideoReady ? (
                  <div className="status-ready">✅ 摄像头已准备好</div>
                ) : (
                  <div className="status-loading">⏳ 摄像头启动中...</div>
                )}
              </div>
            </div>
          )}

          {error && (
            <div className="camera-error">
              <p>❌ {error}</p>
              <p className="error-hint">
                请确保已授权摄像头权限，或尝试使用其他浏览器
              </p>
            </div>
          )}
        </div>
      </div>
      
      {isActive && (
        <div className="camera-capture-outer">
          <div className="camera-controls">
            <button
              className="flip-btn"
              onClick={handleFlipCamera}
              disabled={isFlipping}
              title={`切换到${facingMode === 'environment' ? '前置' : '后置'}摄像头`}
            >
              {isFlipping ? '🔄 切换中...' : `🔄 ${facingMode === 'environment' ? '前置' : '后置'}`}
            </button>
            <button
              className="capture-btn-outer"
              onClick={handleCapture}
              disabled={isCapturing}
            >
              {isCapturing ? '拍照中...' : '📸 拍照'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default CameraComponent;
