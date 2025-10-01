import React from 'react';
import UploadComponent from '../components/upload/UploadComponent';
import { useUpload } from '../hooks/useUpload';
import type { UploadFile } from '../types/upload';
import './UploadPage.css';

const UploadPage: React.FC = () => {
  const { uploadedFiles, isUploading, uploadMultipleFiles } = useUpload();

  const handleFilesSelected = async (files: File[]) => {
    console.log('选择的文件:', files);
    try {
      await uploadMultipleFiles(files);
    } catch (error) {
      console.error('上传失败:', error);
    }
  };

  return (
    <div className="upload-page">
      <div className="upload-container">
        <h2>图片上传</h2>
        <p className="upload-description">
          上传您的图片，我们将为您提供智能构图分析和优化建议
        </p>
        
        <UploadComponent
          onFilesSelected={handleFilesSelected}
          accept="image/*"
          multiple={true}
        />

        {uploadedFiles.length > 0 && (
          <div className="uploaded-files">
            <h3>已上传文件 ({uploadedFiles.length})</h3>
            <div className="file-list">
              {uploadedFiles.map((file: UploadFile) => (
                <div key={file.id} className="file-item">
                  <div className="file-info">
                    <span className="file-name">{file.file.name}</span>
                    <span className="file-size">
                      {(file.file.size / 1024 / 1024).toFixed(2)} MB
                    </span>
                  </div>
                  <div className="file-status">
                    <span className={`status-${file.status}`}>
                      {file.status === 'pending' && '⏳ 等待中'}
                      {file.status === 'uploading' && '📤 上传中'}
                      {file.status === 'success' && '✅ 成功'}
                      {file.status === 'error' && '❌ 失败'}
                    </span>
                    {file.error && (
                      <span className="error-message">{file.error}</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {isUploading && (
          <div className="upload-progress">
            <p>正在处理上传...</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default UploadPage;
