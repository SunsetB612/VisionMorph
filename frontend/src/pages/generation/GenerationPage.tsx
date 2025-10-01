import React, { useState } from 'react';
import GenerationComponent from '../../components/generation/GenerationComponent';
import './GenerationPage.css';

const GenerationPage: React.FC = () => {
  const [selectedImageId, setSelectedImageId] = useState<number | null>(null);
  const [generationResult, setGenerationResult] = useState<any>(null);

  // 模拟已上传的图片列表
  const mockImages = [
    { id: 1, filename: 'sample1.jpg', url: '/static/original/sample1.jpg' },
    { id: 2, filename: 'sample2.jpg', url: '/static/original/sample2.jpg' },
    { id: 3, filename: 'sample3.jpg', url: '/static/original/sample3.jpg' }
  ];

  const handleImageSelect = (imageId: number) => {
    setSelectedImageId(imageId);
    setGenerationResult(null);
  };

  const handleGenerationComplete = (result: any) => {
    setGenerationResult(result);
  };

  return (
    <div className="generation-page">
      <div className="page-header">
        <h1>AI 图片生成</h1>
        <p>选择一张图片，输入提示词，让AI为您生成新的效果</p>
      </div>

      <div className="generation-content">
        <div className="image-selection">
          <h3>选择原始图片</h3>
          <div className="image-grid">
            {mockImages.map(image => (
              <div
                key={image.id}
                className={`image-card ${selectedImageId === image.id ? 'selected' : ''}`}
                onClick={() => handleImageSelect(image.id)}
              >
                <div className="image-placeholder">
                  <span>📷</span>
                  <p>{image.filename}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {selectedImageId && (
          <div className="generation-section">
            <GenerationComponent
              originalImageId={selectedImageId}
              onGenerationComplete={handleGenerationComplete}
            />
          </div>
        )}

        {generationResult && (
          <div className="result-section">
            <h3>生成结果</h3>
            <div className="result-card">
              <div className="result-info">
                <p><strong>任务ID:</strong> {generationResult.id}</p>
                <p><strong>状态:</strong> {generationResult.message}</p>
                <p><strong>创建时间:</strong> {new Date(generationResult.created_at).toLocaleString()}</p>
              </div>
              <div className="result-actions">
                <button className="view-result-btn">查看结果</button>
                <button className="download-btn">下载图片</button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default GenerationPage;
