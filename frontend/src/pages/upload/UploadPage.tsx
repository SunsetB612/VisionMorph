import React, { useEffect, useState } from 'react';
import UploadComponent from '../../components/upload/UploadComponent';
import { useUpload } from '../../hooks/useUpload';
import { generationService } from '../../services/generationService';
import { resultService } from '../../services/resultService';
import type { UploadFile } from '../../types/upload';
import type { StaticImageResult } from '../../services/resultService';
import './UploadPage.css';

type WorkflowStep = 'upload' | 'generating' | 'result';
type ViewAngle = '俯视' | '仰视' | '平视' | '右前方' | '左前方' | '不限';

const sortResultsByScore = (results: StaticImageResult[]) =>
  [...results].sort((a, b) => b.overall_score - a.overall_score);

const SUPPORTED_DEMO_INPUTS = new Set(['1', '2', '3']);
const DEMO_INPUT_HINT = '当前仅支持 input/1.jpg、input/2.jpg、input/3.jpg 示例图片';

const extractDemoInputKey = (filename?: string): string | null => {
  if (!filename) return null;
  const dotIndex = filename.lastIndexOf('.');
  const baseName = dotIndex > 0 ? filename.slice(0, dotIndex) : filename;
  const matches = baseName.match(/\d+/g);
  if (!matches || matches.length === 0) {
    return null;
  }
  const candidate = matches[matches.length - 1];
  return candidate && SUPPORTED_DEMO_INPUTS.has(candidate) ? candidate : null;
};

const UploadPage: React.FC = () => {
  const { uploadedFiles, isUploading, uploadMultipleFiles, clearFiles } = useUpload();
  const [currentStep, setCurrentStep] = useState<WorkflowStep>('upload');
  const [generationProgress, setGenerationProgress] = useState(0);
  const [staticResults, setStaticResults] = useState<StaticImageResult[]>([]);
  const [error, setError] = useState<string>('');
  const [selectedImageId, setSelectedImageId] = useState<string | null>(null);
  const [selectedViewAngles, setSelectedViewAngles] = useState<ViewAngle[]>([]);
  const [showViewAngleModal, setShowViewAngleModal] = useState(false);
  const [demoInputKey, setDemoInputKey] = useState<string | null>(null);

  const handleFilesSelected = async (files: File[]) => {
    try {
      await uploadMultipleFiles(files);
      if (files.length > 0) {
        const derivedKey = extractDemoInputKey(files[0]?.name);
        setDemoInputKey(derivedKey);
        if (!derivedKey) {
          setError(DEMO_INPUT_HINT);
        } else {
          setError('');
        }
      } else {
        setDemoInputKey(null);
      }
    } catch (uploadError) {
      console.error('UploadPage: 上传失败:', uploadError);
      setError('上传失败，请稍后再试');
      setDemoInputKey(null);
    }
  };

  useEffect(() => {
    setCurrentStep('upload');
    setStaticResults([]);
    setGenerationProgress(0);
    setError('');
    setSelectedImageId(null);
    setSelectedViewAngles([]);
    setShowViewAngleModal(false);
    setDemoInputKey(null);
    clearFiles();
  }, []);

  useEffect(() => {
    if (
      uploadedFiles.length > 0 &&
      uploadedFiles.every(file => file.status === 'success') &&
      currentStep === 'upload' &&
      !showViewAngleModal
    ) {
      const timer = setTimeout(() => {
        setShowViewAngleModal(true);
      }, 500);
      return () => clearTimeout(timer);
    }
  }, [uploadedFiles, currentStep, showViewAngleModal]);

  const handleViewAngleChange = (angle: ViewAngle) => {
    setSelectedViewAngles(prev => {
      if (prev.includes(angle)) {
        return prev.filter(a => a !== angle);
      }
      if (angle === '不限') {
        return ['不限'];
      }
      const filtered = prev.filter(a => a !== '不限');
      return [...filtered, angle];
    });
  };

  const startGeneration = async (imageId: number) => {
    if (!demoInputKey) {
      setError(DEMO_INPUT_HINT);
      return;
    }
    setShowViewAngleModal(false);
    setCurrentStep('generating');
    setGenerationProgress(0);
    setError('');
    setStaticResults([]);

    try {
      const progressInterval = setInterval(() => {
        setGenerationProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return prev;
          }
          return prev + Math.random() * 10;
        });
      }, 500);

      await generationService.createGenerationTask({
        original_image_id: imageId,
        view_angles: selectedViewAngles.length > 0 ? selectedViewAngles : undefined
      });

      clearInterval(progressInterval);
      setGenerationProgress(100);

      setTimeout(async () => {
        try {
          const staticResponse = await resultService.getStaticResults(demoInputKey);
          setStaticResults(sortResultsByScore(staticResponse.results));
          setCurrentStep('result');
        } catch (fetchError) {
          console.error('获取固定结果失败:', fetchError);
          setError('获取固定结果失败，请稍后再试');
          setCurrentStep('upload');
        }
      }, 1000);
    } catch (err) {
      setError('生成失败: ' + (err instanceof Error ? err.message : '未知错误'));
      setCurrentStep('upload');
    }
  };

  const resetWorkflow = () => {
    setCurrentStep('upload');
    setGenerationProgress(0);
    setStaticResults([]);
    setError('');
    setSelectedImageId(null);
    setSelectedViewAngles([]);
    setShowViewAngleModal(false);
    setDemoInputKey(null);
    clearFiles();
  };

  const openImageModal = (imageId: string) => {
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
                <span className="result-count">共 {staticResults.length} 种方案</span>
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
                {staticResults.map((image, index) => {
                  const displayName = `方案 ${index + 1}`;
                  return (
                    <div key={image.id} className="image-item">
                      <div 
                        className="image-container clickable"
                        onClick={() => openImageModal(image.id)}
                      >
                        <img 
                          src={`http://localhost:8000${image.relative_path}`}
                          alt={displayName}
                        />
                        <div className="score-badge">
                          <span className="score-value">{image.overall_score.toFixed(1)}</span>
                          <span className="score-label">分</span>
                        </div>
                        <div className="click-hint">
                          <span>点击查看详情</span>
                        </div>
                      </div>
                      <div className="image-info">
                        <span className="image-name">{displayName}</span>
                      </div>
                      
                      <div className="result-summary">
                        <div className="score-section">
                          <div className="score-display">
                            <span className="score-number">{image.overall_score.toFixed(1)}</span>
                            <span className="score-text">综合评分</span>
                          </div>
                        </div>
                      </div>

                    </div>
                  );
                })}
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

        {showViewAngleModal && (
          <div className="modal-overlay view-angle-modal" onClick={() => setShowViewAngleModal(false)}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
              <div className="modal-header">
                <h3>选择视角</h3>
                <button className="modal-close" onClick={() => setShowViewAngleModal(false)}>×</button>
              </div>
              <div className="modal-body">
                <p className="view-angle-hint">请选择您希望生成的视角方向（可多选）</p>
                <div className="view-angle-options">
                  {([
                    { name: '俯视', icon: '⬇️' },
                    { name: '仰视', icon: '⬆️' },
                    { name: '平视', icon: '➡️' },
                    { name: '右前方', icon: '↘️' },
                    { name: '左前方', icon: '↙️' },
                    { name: '不限', icon: '🔄' }
                  ] as { name: ViewAngle; icon: string }[]).map(({ name, icon }) => (
                    <label 
                      key={name} 
                      className={`view-angle-option ${selectedViewAngles.includes(name) ? 'checked' : ''}`}
                    >
                      <input
                        type="checkbox"
                        checked={selectedViewAngles.includes(name)}
                        onChange={() => handleViewAngleChange(name)}
                      />
                      <span className="view-angle-icon">{icon}</span>
                      <span className="view-angle-label">{name}</span>
                    </label>
                  ))}
                </div>
                <div className="modal-actions">
                  <button
                    className="start-generation-btn"
                    onClick={() => {
                      const firstSuccessFile = uploadedFiles.find(file => file.status === 'success');
                      if (firstSuccessFile && firstSuccessFile.imageId) {
                        startGeneration(firstSuccessFile.imageId);
                      }
                    }}
                    disabled={isUploading}
                  >
                    🚀 开始智能构图生成
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {selectedImageId && (
          <div className="modal-overlay" onClick={closeImageModal}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
              {(() => {
                const selectedImageIndex = staticResults.findIndex(img => img.id === selectedImageId);
                if (selectedImageIndex === -1) return null;
                const selectedImage = staticResults[selectedImageIndex];
                const displayName = `方案 ${selectedImageIndex + 1}`;
                return (
                  <>
                    <div className="modal-header">
                      <h3>{displayName}</h3>
                      <button className="modal-close" onClick={closeImageModal}>×</button>
                    </div>
                    <div className="modal-body">
                      <div className="modal-image">
                        <img 
                          src={`http://localhost:8000${selectedImage.relative_path}`}
                          alt={displayName}
                        />
                      </div>
                      <div className="modal-details">
                        <div className="score-section">
                          <div className="score-display">
                            <span className="score-number">{selectedImage.overall_score.toFixed(1)}</span>
                            <span className="score-text">综合评分</span>
                          </div>
                        </div>
                        {selectedImage.viewpoint_feature && (
                          <div className="guidance-section">
                            <h4>视角特色</h4>
                            <p className="guidance-text">{selectedImage.viewpoint_feature}</p>
                          </div>
                        )}
                        {selectedImage.composition_highlights && (
                          <div className="guidance-section">
                            <h4>构图亮点</h4>
                            <p className="guidance-text">{selectedImage.composition_highlights}</p>
                          </div>
                        )}
                        {selectedImage.operation_guide && (
                          <div className="guidance-section">
                            <h4>操作指南</h4>
                            <p className="guidance-text">{selectedImage.operation_guide}</p>
                          </div>
                        )}
                      </div>
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
