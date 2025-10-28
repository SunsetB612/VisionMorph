import React, { useState, useEffect } from 'react';
import UploadComponent from '../../components/upload/UploadComponent';
import ViewAngleSelector from '../../components/viewangle/ViewAngleSelector';
import type { ViewAngle } from '../../components/viewangle/ViewAngleSelector';
import { useUpload } from '../../hooks/useUpload';
import { generationService } from '../../services/generationService';
import { resultService } from '../../services/resultService';
import { useAuthStore } from '../../store/authStore';
import type { UploadFile } from '../../types/upload';
import type { GeneratedImageInfo } from '../../types/generation';
import './UploadPage.css';

type WorkflowStep = 'upload' | 'angle-selection' | 'generating' | 'result';

const UploadPage: React.FC = () => {
  const { uploadedFiles, isUploading, uploadMultipleFiles, clearFiles } = useUpload();
  const { user } = useAuthStore();
  const [currentStep, setCurrentStep] = useState<WorkflowStep>('upload');
  const [generationProgress, setGenerationProgress] = useState(0);
  const [generatedImages, setGeneratedImages] = useState<GeneratedImageInfo[]>([]);
  const [error, setError] = useState<string>('');
  const [selectedImageId, setSelectedImageId] = useState<number | null>(null);
  const [selectedAngles, setSelectedAngles] = useState<ViewAngle[]>([]);
  const [uploadedImageId, setUploadedImageId] = useState<number | null>(null);

  const handleFilesSelected = async (files: File[]) => {
    console.log('UploadPage: 选择的文件:', files);
    try {
      console.log('UploadPage: 开始上传文件');
      await uploadMultipleFiles(files);
      console.log('UploadPage: 文件上传完成');
    } catch (error) {
      console.error('UploadPage: 上传失败:', error);
    }
  };

  // 页面加载时清理所有状态
  useEffect(() => {
    console.log('UploadPage: 页面加载，清理所有状态');
    setCurrentStep('upload');
    setGeneratedImages([]);
    setGenerationProgress(0);
    setError('');
    setSelectedImageId(null);
    setSelectedAngles([]);
    setUploadedImageId(null);
    clearFiles();
  }, []);

  // 当上传完成后，跳转到视角选择步骤
  useEffect(() => {
    if (uploadedFiles.length > 0 && uploadedFiles.every(file => file.status === 'success')) {
      const firstSuccessFile = uploadedFiles.find(file => file.status === 'success');
      if (firstSuccessFile && firstSuccessFile.imageId) {
        console.log('UploadPage: 上传完成，进入视角选择步骤');
        setUploadedImageId(firstSuccessFile.imageId);
        setCurrentStep('angle-selection');
      }
    }
  }, [uploadedFiles]);


  const startGeneration = async (imageId: number, angles: ViewAngle[]) => {
    console.log('UploadPage: startGeneration 被调用，imageId:', imageId, '视角:', angles);
    setCurrentStep('generating');
    setGenerationProgress(0);
    setError('');

    try {
      // 使用 SSE 流式接口获取实时进度
      await generationService.createGenerationTaskWithProgress(
        { 
          original_image_id: imageId,
          view_angles: angles 
        },
        (progress) => {
          // 实时更新进度
          console.log('📊 进度更新:', progress);
          
          if (progress.total > 0) {
            // 根据当前/总数计算百分比
            const percentage = Math.round((progress.current / progress.total) * 100);
            setGenerationProgress(percentage);
          }
          
          // 可选：显示进度消息
          if (progress.message) {
            console.log('💬 进度消息:', progress.message);
          }
        }
      );
      
      // SSE 完成后，确保进度为 100%
      setGenerationProgress(100);
      
      // 等待一下让用户看到100%进度
      setTimeout(async () => {
        // 获取生成结果
        const taskResponse = await generationService.getGenerationTask(imageId);
        const imagesWithResults = await Promise.all(
          taskResponse.generated_images.map(async (image: GeneratedImageInfo) => {
            try {
              // 尝试获取评分结果
              const result = await resultService.getResultByGeneratedId(image.id);
              return { ...image, result };
            } catch (error) {
              // 如果评分结果不存在，返回原始图片信息
              console.warn(`No result found for generated image ${image.id}:`, error);
              return image;
            }
          })
        );
        
        // 按照评分从高到低排序
        const sortedImages = imagesWithResults.sort((a, b) => {
          const scoreA = a.result?.overall_score || 0;
          const scoreB = b.result?.overall_score || 0;
          return scoreB - scoreA; // 从高到低排序
        });
        
        setGeneratedImages(sortedImages);
        setCurrentStep('result');
      }, 1000);
      
    } catch (err) {
      setError('生成失败: ' + (err instanceof Error ? err.message : '未知错误'));
      setCurrentStep('upload');
    }
  };

  const handleAngleConfirm = (angles: ViewAngle[]) => {
    console.log('用户选择的视角:', angles);
    setSelectedAngles(angles);
    if (uploadedImageId) {
      startGeneration(uploadedImageId, angles);
    }
  };

  const handleAngleCancel = () => {
    // 取消视角选择，返回上传步骤
    setCurrentStep('upload');
    setUploadedImageId(null);
  };

  const resetWorkflow = () => {
    setCurrentStep('upload');
    setGenerationProgress(0);
    setGeneratedImages([]);
    setError('');
    setSelectedImageId(null);
    setSelectedAngles([]);
    setUploadedImageId(null);
    clearFiles(); // 清理上传的文件列表
  };

  const openImageModal = (imageId: number) => {
    setSelectedImageId(imageId);
  };

  const closeImageModal = () => {
    setSelectedImageId(null);
  };

  return (
    <div className="upload-page">
      <div className="upload-container">
        {currentStep === 'upload' && (
          <>
            <h2>智能构图分析</h2>
            <p className="upload-description">
              上传您的图片，我们将为您提供专业的智能构图分析和优化建议
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

        {currentStep === 'angle-selection' && (
          <ViewAngleSelector
            onConfirm={handleAngleConfirm}
            onCancel={handleAngleCancel}
          />
        )}

        {currentStep === 'generating' && (
          <div className="generation-progress">
            <h2>🎨 正在生成图片</h2>
            <p className="generation-description">
              我们的AI正在为您生成多种构图方案，请稍候...
            </p>
            
            {selectedAngles.length > 0 && (
              <div className="selected-angles-display">
                <span className="angles-label">📐 已选择的视角：</span>
                <span className="angles-values">{selectedAngles.join('、')}</span>
              </div>
            )}
            
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
                <span>智能构图分析</span>
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
              <div className="result-title">
                <h2>🎉 生成完成</h2>
                <span className="result-count">共 {generatedImages.length} 种方案</span>
              </div>
              <button 
                className="reset-btn"
                onClick={resetWorkflow}
              >
                🔄 重新开始
              </button>
            </div>
            
            <div className="generated-images">
              <div className="image-grid">
                {generatedImages.map((image, index) => (
                  <div key={image.id} className="image-item">
                    <div 
                      className="image-container clickable"
                      onClick={() => openImageModal(image.id)}
                    >
                      <img 
                        src={`http://localhost:8000/static/user${user?.id || 1}/results/${image.filename}`}
                        alt={`生成图片 ${index + 1}`}
                        onError={(e) => {
                          // 如果生成图片不存在，显示原始图片
                          const target = e.target as HTMLImageElement;
                          target.src = `http://localhost:8000/static/user${user?.id || 1}/original/${uploadedFiles[0]?.file.name}`;
                        }}
                      />
                      {image.result && (
                        <div className="score-badge">
                          <span className="score-value">{image.result.overall_score}</span>
                          <span className="score-label">分</span>
                        </div>
                      )}
                      <div className="click-hint">
                        <span>点击查看详情</span>
                      </div>
                    </div>
                    <div className="image-info">
                      <span className="image-name">方案 {index + 1}</span>
                      <span className="image-date">
                        {new Date(image.created_at).toLocaleString()}
                      </span>
                    </div>
                    
                    {/* 默认显示的评分和亮点 */}
                    {image.result && (
                      <div className="result-summary">
                        <div className="score-section">
                          <div className="score-display">
                            <span className="score-number">{image.result.overall_score}</span>
                            <span className="score-text">综合评分</span>
                          </div>
                        </div>
                        {image.result.highlights && (
                          <div className="highlights-section">
                            <h4>✨ 亮点分析</h4>
                            <p className="highlights-text">{image.result.highlights}</p>
                          </div>
                        )}
                      </div>
                    )}

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

        {/* 图片详情模态对话框 */}
        {selectedImageId && (
          <div className="modal-overlay" onClick={closeImageModal}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
              {(() => {
                const selectedImage = generatedImages.find(img => img.id === selectedImageId);
                if (!selectedImage) return null;
                
                return (
                  <>
                    <div className="modal-header">
                      <h3>图片详情</h3>
                      <button className="modal-close" onClick={closeImageModal}>×</button>
                    </div>
                    <div className="modal-body">
                      <div className="modal-image">
                        <img 
                          src={`http://localhost:8000/static/user${user?.id || 1}/results/${selectedImage.filename}`}
                          alt="生成图片"
                          onError={(e) => {
                            const target = e.target as HTMLImageElement;
                            target.src = `http://localhost:8000/static/user${user?.id || 1}/original/${uploadedFiles[0]?.file.name}`;
                          }}
                        />
                      </div>
                      {selectedImage.result && (
                        <div className="modal-details">
                          {selectedImage.result.ai_comment && (
                            <div className="evaluation-section">
                              <h4>🤖 AI评价</h4>
                              <p className="evaluation-text">{selectedImage.result.ai_comment}</p>
                            </div>
                          )}
                          {selectedImage.result.shooting_guidance && (
                            <div className="guidance-section">
                              <h4>📸 拍摄指导</h4>
                              <p className="guidance-text">{selectedImage.result.shooting_guidance}</p>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  </>
                );
              })()}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default UploadPage;
