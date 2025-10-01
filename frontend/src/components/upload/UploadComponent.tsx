import React, { useRef, useState } from 'react';
import { useUpload } from '../../hooks/useUpload';
import CameraComponent from '../camera/CameraComponent';
import './UploadComponent.css';

interface UploadComponentProps {
  onFilesSelected?: (files: File[]) => void;
  accept?: string;
  multiple?: boolean;
  disabled?: boolean;
  className?: string;
}

const UploadComponent: React.FC<UploadComponentProps> = ({
  onFilesSelected,
  accept = 'image/*',
  multiple = true,
  disabled = false,
  className = ''
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [showCamera, setShowCamera] = useState(false);
  const {
    isUploading,
    isDragOver,
    error,
    handleDragOver,
    handleDragLeave,
    handleDrop,
    uploadMultipleFiles
  } = useUpload();

  const handleFileSelect = (files: File[]) => {
    if (onFilesSelected) {
      onFilesSelected(files);
    } else {
      uploadMultipleFiles(files);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    if (files.length > 0) {
      handleFileSelect(files);
    }
  };

  const handleClick = () => {
    if (!disabled && fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  const handleDropWrapper = (e: React.DragEvent) => {
    handleDrop(e, handleFileSelect);
  };

  const handleCameraClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    setShowCamera(true);
  };

  const handlePhotoCaptured = (file: File) => {
    setShowCamera(false);
    handleFileSelect([file]);
  };

  const handleCameraClose = () => {
    setShowCamera(false);
  };

  return (
    <div className={`upload-component ${className}`}>
      <div
        className={`upload-area ${isDragOver ? 'drag-over' : ''} ${disabled ? 'disabled' : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDropWrapper}
        onClick={handleClick}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept={accept}
          multiple={multiple}
          onChange={handleInputChange}
          style={{ display: 'none' }}
          disabled={disabled}
        />
        
        <div className="upload-content">
          <div className="upload-icon">
            📸
          </div>
          <div className="upload-text">
            {isDragOver ? (
              <p>释放文件以上传</p>
            ) : (
              <>
                <p>拖拽图片到这里或点击选择文件</p>
                <p className="upload-hint">支持 JPG、PNG、WebP 格式</p>
              </>
            )}
          </div>
        </div>
      </div>
      
      {/* 拍照按钮移出拖拽区域 */}
      <div className="upload-actions">
        <button
          className="camera-btn"
          onClick={handleCameraClick}
          disabled={disabled}
          title="使用摄像头拍照"
        >
          📷 拍照
        </button>
      </div>

      {error && (
        <div className="upload-error">
          <p>❌ {error}</p>
        </div>
      )}

      {isUploading && (
        <div className="upload-loading">
          <p>⏳ 正在上传...</p>
        </div>
      )}

      {showCamera && (
        <CameraComponent
          onPhotoCaptured={handlePhotoCaptured}
          onClose={handleCameraClose}
        />
      )}
    </div>
  );
};

export default UploadComponent;
