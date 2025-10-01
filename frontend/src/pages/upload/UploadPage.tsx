import React, { useState, useEffect } from 'react';
import UploadComponent from '../../components/upload/UploadComponent';
import { useUpload } from '../../hooks/useUpload';
import { generationService } from '../../services/generationService';
import type { UploadFile } from '../../types/upload';
import type { GeneratedImageInfo } from '../../types/generation';
import './UploadPage.css';

type WorkflowStep = 'upload' | 'generating' | 'result';

const UploadPage: React.FC = () => {
  const { uploadedFiles, isUploading, uploadMultipleFiles } = useUpload();
  const [currentStep, setCurrentStep] = useState<WorkflowStep>('upload');
  const [generationProgress, setGenerationProgress] = useState(0);
  const [generatedImages, setGeneratedImages] = useState<GeneratedImageInfo[]>([]);
  const [error, setError] = useState<string>('');

  const handleFilesSelected = async (files: File[]) => {
    console.log('选择的文件:', files);
    try {
      await uploadMultipleFiles(files);
    } catch (error) {
      console.error('上传失败:', error);
    }
  };

  // 当上传完成后，自动开始生成流程
  useEffect(() => {
    if (uploadedFiles.length > 0 && uploadedFiles.every(file => file.status === 'success')) {
      const firstSuccessFile = uploadedFiles.find(file => file.status === 'success');
      if (firstSuccessFile && firstSuccessFile.imageId) {
        startGeneration(firstSuccessFile.imageId);
      }
    }
  }, [uploadedFiles]);

  const startGeneration = async (imageId: number) => {
    setCurrentStep('generating');
    setGenerationProgress(0);
    setError('');

    try {
      // 模拟生成进度
      const progressInterval = setInterval(() => {
        setGenerationProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return prev;
          }
          return prev + Math.random() * 10;
        });
      }, 500);

      // 调用生成API
      const response = await generationService.createGenerationTask({ original_image_id: imageId });
      
      // 完成进度
      clearInterval(progressInterval);
      setGenerationProgress(100);
      
      // 等待一下让用户看到100%进度
      setTimeout(async () => {
        // 获取生成结果
        const taskResponse = await generationService.getGenerationTask(response.original_image_id);
        setGeneratedImages(taskResponse.generated_images);
        setCurrentStep('result');
      }, 1000);
      
    } catch (err) {
      setError('生成失败: ' + (err instanceof Error ? err.message : '未知错误'));
      setCurrentStep('upload');
    }
  };

  const resetWorkflow = () => {
    setCurrentStep('upload');
    setGenerationProgress(0);
    setGeneratedImages([]);
    setError('');
  };

  return (
    <div className="upload-page">
      <div className="upload-container">
        {currentStep === 'upload' && (
          <>
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
          </>
        )}

        {currentStep === 'generating' && (
          <div className="generation-progress">
            <h2>🎨 正在生成图片</h2>
            <p className="generation-description">
              我们的AI正在为您生成多种构图方案，请稍候...
            </p>
            
            <div className="progress-container">
              <div className="progress-bar">
                <div 
                  className="progress-fill" 
                  style={{ width: `${generationProgress}%` }}
                ></div>
              </div>
              <div className="progress-text">
                {Math.round(generationProgress)}%
              </div>
            </div>
            
            <div className="generation-steps">
              <div className="step active">
                <span className="step-icon">🔍</span>
                <span>分析图片构图</span>
              </div>
              <div className="step active">
                <span className="step-icon">🎨</span>
                <span>生成优化方案</span>
              </div>
              <div className={`step ${generationProgress > 80 ? 'active' : ''}`}>
                <span className="step-icon">✨</span>
                <span>完成生成</span>
              </div>
            </div>
          </div>
        )}

        {currentStep === 'result' && (
          <div className="generation-result">
            <div className="result-header">
              <h2>🎉 生成完成</h2>
              <p className="result-description">
                我们为您生成了 {generatedImages.length} 种构图方案
              </p>
              <button 
                className="reset-btn"
                onClick={resetWorkflow}
              >
                🔄 重新开始
              </button>
            </div>
            
            <div className="generated-images">
              <h3>生成的图片</h3>
              <div className="image-grid">
                {generatedImages.map((image, index) => (
                  <div key={image.id} className="image-item">
                    <div className="image-container">
                      <img 
                        src={`http://localhost:8000/static/generated/${image.filename}`}
                        alt={`生成图片 ${index + 1}`}
                        onError={(e) => {
                          // 如果生成图片不存在，显示原始图片
                          const target = e.target as HTMLImageElement;
                          target.src = `http://localhost:8000/static/original/${uploadedFiles[0]?.file.name}`;
                        }}
                      />
                    </div>
                    <div className="image-info">
                      <span className="image-name">方案 {index + 1}</span>
                      <span className="image-date">
                        {new Date(image.created_at).toLocaleString()}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {error && (
          <div className="error-message">
            <p>❌ {error}</p>
            <button 
              className="retry-btn"
              onClick={resetWorkflow}
            >
              重试
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default UploadPage;
