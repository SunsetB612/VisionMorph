import React, { useState } from 'react';
import { generationService, type GenerationRequest, type GeneratedImageInfo } from '../../services/generationService';
import { uploadService } from '../../services/uploadService';
import UploadComponent from '../upload/UploadComponent';
import './GenerationComponent.css';

interface GenerationComponentProps {
  originalImageId?: number;
  onGenerationComplete?: (result: any) => void;
}

type WorkflowStep = 'upload' | 'generate' | 'result';

const GenerationComponent: React.FC<GenerationComponentProps> = ({
  originalImageId,
  onGenerationComplete
}) => {
  const [currentStep, setCurrentStep] = useState<WorkflowStep>(originalImageId ? 'generate' : 'upload');
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [uploadedImageId, setUploadedImageId] = useState<number | null>(originalImageId || null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedImages, setGeneratedImages] = useState<GeneratedImageInfo[]>([]);
  const [error, setError] = useState<string>('');
  const [progress, setProgress] = useState(0);

  const handleFileUpload = async (files: File[]) => {
    if (files.length === 0) return;
    
    const file = files[0];
    setUploadedFile(file);
    setError('');
    
    try {
      // 使用上传服务上传文件
      const result = await uploadService.uploadImage(file);
      setUploadedImageId(result.image_id);
      setCurrentStep('generate');
    } catch (err) {
      setError('上传失败: ' + (err instanceof Error ? err.message : '未知错误'));
    }
  };

  const handleGenerate = async () => {
    const imageId = uploadedImageId || originalImageId;
    if (!imageId) {
      setError('请先上传图片');
      return;
    }

    setIsGenerating(true);
    setError('');
    setProgress(0);
    setCurrentStep('generate');

    try {
      // 模拟生成进度
      const progressInterval = setInterval(() => {
        setProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return 90;
          }
          return prev + 10;
        });
      }, 200);

      const request: GenerationRequest = {
        original_image_id: imageId
      };

      const data = await generationService.createGenerationTask(request);
      
      // 获取生成的图片
      const generatedImages = await generationService.getGeneratedImages(data.original_image_id);
      setGeneratedImages(generatedImages);
      
      clearInterval(progressInterval);
      setProgress(100);
      
      setTimeout(() => {
        setCurrentStep('result');
        if (onGenerationComplete) {
          onGenerationComplete(data);
        }
      }, 500);
      
    } catch (err) {
      setError(err instanceof Error ? err.message : '生成失败');
      setIsGenerating(false);
    }
  };


  const handleRestart = () => {
    setCurrentStep('upload');
    setUploadedFile(null);
    setUploadedImageId(null);
    setGeneratedImages([]);
    setError('');
    setProgress(0);
    setIsGenerating(false);
  };

  const renderUploadStep = () => (
    <div className="workflow-step upload-step">
      <div className="step-header">
        <h3>📸 上传图片</h3>
        <p>请选择一张图片进行AI生成</p>
      </div>
      
      <div className="upload-area">
        <UploadComponent
          onFilesSelected={handleFileUpload}
          accept="image/*"
          multiple={false}
        />
      </div>
      
      {error && (
        <div className="error-message">
          {error}
        </div>
      )}
    </div>
  );

  const renderGenerateStep = () => (
    <div className="workflow-step generate-step">
      <div className="step-header">
        <h3>🎨 AI 生成中</h3>
        <p>正在为您生成多张不同效果的图片...</p>
      </div>
      
      {uploadedFile && (
        <div className="original-image-preview">
          <img 
            src={URL.createObjectURL(uploadedFile)} 
            alt="原始图片"
            className="preview-image"
          />
          <p className="image-name">{uploadedFile.name}</p>
        </div>
      )}
      
      <div className="generation-progress">
        <div className="progress-bar">
          <div 
            className="progress-fill" 
            style={{ width: `${progress}%` }}
          ></div>
        </div>
        <p className="progress-text">{progress}% 完成</p>
      </div>
      
      {error && (
        <div className="error-message">
          {error}
        </div>
      )}
    </div>
  );

  const renderResultStep = () => (
    <div className="workflow-step result-step">
      <div className="step-header">
        <h3>✨ 生成完成</h3>
        <p>成功生成 {generatedImages.length} 张图片</p>
      </div>
      
      <div className="generated-images">
        {generatedImages.map((image, index) => (
          <div key={image.id} className="generated-image-item">
            <img 
              src={`http://localhost:8000/${image.file_path.replace(/\\/g, '/')}`}
              alt={`生成图片 ${index + 1}`}
              className="generated-image"
            />
            <p className="image-label">生成图片 {index + 1}</p>
          </div>
        ))}
      </div>
      
      <div className="result-actions">
        <button 
          className="btn btn-primary"
          onClick={handleRestart}
        >
          重新生成
        </button>
      </div>
    </div>
  );

  return (
    <div className="generation-component">
      <div className="workflow-container">
        {currentStep === 'upload' && renderUploadStep()}
        {currentStep === 'generate' && renderGenerateStep()}
        {currentStep === 'result' && renderResultStep()}
      </div>
      
      {/* 生成按钮 - 只在上传完成后显示，或者有originalImageId时显示 */}
      {currentStep === 'upload' && uploadedFile && (
        <div className="generate-button-container">
          <button
            className="btn btn-primary btn-large"
            onClick={handleGenerate}
            disabled={isGenerating}
          >
            开始生成图片
          </button>
        </div>
      )}
      
      {/* 如果有originalImageId，直接显示生成按钮 */}
      {originalImageId && currentStep === 'generate' && !isGenerating && (
        <div className="generate-button-container">
          <button
            className="btn btn-primary btn-large"
            onClick={handleGenerate}
            disabled={isGenerating}
          >
            开始生成图片
          </button>
        </div>
      )}
    </div>
  );
};

export default GenerationComponent;