import React, { useEffect, useId, useState } from 'react';
import UploadComponent from '../../components/upload/UploadComponent';
import { useUpload } from '../../hooks/useUpload';
import { generationService } from '../../services/generationService';
import { resultService } from '../../services/resultService';
import type { UploadFile } from '../../types/upload';
import type { StaticImageResult } from '../../services/resultService';
import { getApiBaseUrl } from '../../config/apiBase';
import './UploadPage.css';

type WorkflowStep = 'upload' | 'generating' | 'result';
type ViewAngle = '俯视' | '仰视' | '平视' | '右前方' | '左前方' | '不限';

const sortResultsByScore = (results: StaticImageResult[]) =>
  [...results].sort((a, b) => b.overall_score - a.overall_score);

const SUPPORTED_DEMO_INPUTS = new Set(['1', '2', '3']);

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

/** 多行文本拆条：换行优先；若整段仅一行且含「；」则再拆分（构图亮点 / 操作指南共用） */
const splitIntoDisplayLines = (raw: string): string[] => {
  const normalized = raw.replace(/\r\n/g, '\n').trim();
  if (!normalized) return [];
  let parts = normalized
    .split(/\n/)
    .map((l) => l.trim())
    .filter(Boolean);
  if (parts.length === 1 && parts[0].includes('；')) {
    parts = parts[0]
      .split('；')
      .map((s) => s.trim())
      .filter(Boolean);
  }
  return parts;
};

/** 「小标题：正文」优先识别全角冒号，否则半角（仅首次冒号处拆分） */
const parseCompositionHighlightLine = (
  line: string
): { title: string | null; body: string } => {
  const fw = line.indexOf('：');
  const hw = line.indexOf(':');
  let at = fw >= 0 ? fw : -1;
  let sepLen = 1;
  if (fw >= 0 && hw >= 0) {
    at = Math.min(fw, hw);
  } else if (fw < 0 && hw >= 0) {
    at = hw;
  }
  if (at > 0 && at < line.length - 1) {
    const title = line.slice(0, at).trim();
    const body = line.slice(at + sepLen).trim();
    if (title && body) {
      return { title, body };
    }
  }
  return { title: null, body: line };
};

/**
 * 操作指南单行：优先「小标题：正文」冒号；否则「首句 + 句末标点」为小标题，后面为正文
 * 例：「定位水边拍摄点。移动到距离…」→ 小标题「定位水边拍摄点」，正文「移动到距离…」
 */
const parseOperationGuideLine = (normalized: string): { title: string | null; body: string } => {
  const colon = parseCompositionHighlightLine(normalized);
  if (colon.title) {
    return colon;
  }
  const s = normalized.trim();
  if (!s) {
    return { title: null, body: '' };
  }
  const m = s.match(/^(.+?[。！？．])([\s\S]*)$/);
  if (!m) {
    return { title: null, body: s };
  }
  const first = m[1].trim();
  const rest = m[2].trim();
  if (!rest) {
    return { title: null, body: s };
  }
  const title = first.replace(/[。！？．]+$/u, '').trim();
  if (!title) {
    return { title: null, body: s };
  }
  return { title, body: rest };
};

const CompositionHighlightsBlock: React.FC<{ text: string }> = ({ text }) => {
  const lines = splitIntoDisplayLines(text);
  return (
    <div className="composition-highlights-list">
      {lines.map((line, i) => {
        const { title, body } = parseCompositionHighlightLine(line);
        return (
          <div key={i} className="composition-highlight-item">
            {title ? (
              <>
                <span className="composition-highlight-title">{title}</span>
                <p className="composition-highlight-body">{body}</p>
              </>
            ) : (
              <p className="composition-highlight-body">{body}</p>
            )}
          </div>
        );
      })}
    </div>
  );
};

/** 行首可选：emoji 簇 + 空白（Excel 里常在「第N步」前加图标） */
const RE_LEADING_EMOJI_SPACES =
  /^(?:(?:\p{Extended_Pictographic}(?:\uFE0F|\u200D\p{Extended_Pictographic})*)\s*)+/u;

/** 去掉行首「第N步：」等与左侧序号重复的标记（支持 emoji 在「第」之前） */
const normalizeOperationStepText = (line: string, stepIndex: number): string => {
  let s = line.trim();
  const n = stepIndex + 1;
  const mNum = s.match(/^(\d+)[\.、\)\）]\s*(.*)$/s);
  if (mNum && parseInt(mNum[1], 10) === n) {
    s = mNum[2].trim();
  }
  const stripCnStep = (t: string): string => {
    let u = t;
    for (let k = 0; k < 6; k++) {
      const before = u;
      u = u
        .replace(
          new RegExp(
            `${RE_LEADING_EMOJI_SPACES.source}第[一二三四五六七八九十百千万两零\\d]+步\\s*[：:、,.，．]\\s*`,
            'u'
          ),
          ''
        )
        .replace(
          new RegExp(
            `${RE_LEADING_EMOJI_SPACES.source}第[一二三四五六七八九十百千万两零\\d]+步\\s+`,
            'u'
          ),
          ''
        )
        .replace(/^第[一二三四五六七八九十百千万两零\d]+步\s*[：:、,.，．]\s*/, '')
        .replace(/^第[一二三四五六七八九十百千万两零\d]+步\s+/, '')
        .replace(
          new RegExp(
            `${RE_LEADING_EMOJI_SPACES.source}步骤\\s*[一二三四五六七八九十百千万两零\\d]+\\s*[：:、,.，．]\\s*`,
            'u'
          ),
          ''
        )
        .replace(/^步骤\s*[一二三四五六七八九十百千万两零\d]+\s*[：:、,.，．]\s*/, '')
        .replace(
          new RegExp(
            `${RE_LEADING_EMOJI_SPACES.source}步骤\\s*\\d+\\s*[：:、,.，．]\\s*`,
            'u'
          ),
          ''
        )
        .replace(/^步骤\s*\d+\s*[：:、,.，．]\s*/, '')
        .replace(
          new RegExp(`${RE_LEADING_EMOJI_SPACES.source}[Ss]tep\\s*\\d+\\s*[：:.]\\s*`, 'u'),
          ''
        )
        .replace(/^[Ss]tep\s*\d+\s*[：:.]\s*/, '');
      if (u === before) break;
    }
    return u.trim();
  };
  return stripCnStep(s);
};

/** 竖线 + 底部三角箭头（一体 SVG，无圆钮） */
const OperationGuideConnector: React.FC<{ stepIndex: number }> = ({ stepIndex }) => {
  const uid = useId().replace(/:/g, '');
  const gradId = `opg-${uid}-grad-${stepIndex}`;
  return (
    <div className="operation-guide-connector" aria-hidden="true">
      <svg
        className="operation-guide-flow-svg"
        viewBox="0 0 12 36"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <defs>
          <linearGradient id={gradId} x1="6" y1="0" x2="6" y2="36" gradientUnits="userSpaceOnUse">
            <stop offset="0%" stopColor="#bae6fd" />
            <stop offset="55%" stopColor="#0ea5e9" />
            <stop offset="100%" stopColor="#0284c7" />
          </linearGradient>
        </defs>
        <line
          x1="6"
          y1="1"
          x2="6"
          y2="23"
          stroke={`url(#${gradId})`}
          strokeWidth="2"
          strokeLinecap="round"
        />
        <path d="M2 24 L10 24 L6 31 Z" fill={`url(#${gradId})`} />
      </svg>
    </div>
  );
};

const OperationGuideBlock: React.FC<{ text: string }> = ({ text }) => {
  const steps = splitIntoDisplayLines(text);
  return (
    <div className="operation-guide-list" role="list">
      {steps.map((line, i) => {
        const normalized = normalizeOperationStepText(line, i);
        const { title, body } = parseOperationGuideLine(normalized);
        return (
        <div
          key={i}
          className={
            i < steps.length - 1
              ? 'operation-guide-step operation-guide-step--has-connector'
              : 'operation-guide-step'
          }
          role="listitem"
        >
          <div className="operation-guide-marker" aria-hidden="true">
            <span className="operation-guide-index">{i + 1}</span>
          </div>
          <div className="operation-guide-body">
            {title ? (
              <>
                <span className="operation-guide-subtitle">{title}</span>
                <p className="operation-guide-text">{body}</p>
              </>
            ) : (
              <p className="operation-guide-text">{body}</p>
            )}
          </div>
          {i < steps.length - 1 && <OperationGuideConnector stepIndex={i} />}
        </div>
        );
      })}
    </div>
  );
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

  const handleFilesSelected = async (files: File[]) => {
    try {
      await uploadMultipleFiles(files);
      if (files.length > 0) {
        setError('');
      }
    } catch (uploadError) {
      console.error('UploadPage: 上传失败:', uploadError);
      setError('上传失败，请稍后再试');
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
    const fileForImage = uploadedFiles.find(
      (f) => f.status === 'success' && f.imageId === imageId
    );
    const demoKey =
      fileForImage?.demoInputKey ??
      extractDemoInputKey(fileForImage?.file.name) ??
      '1';

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
          const staticResponse = await resultService.getStaticResults(demoKey);
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
                          src={`${getApiBaseUrl()}${image.relative_path}`}
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
      </div>

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
                          src={`${getApiBaseUrl()}${selectedImage.relative_path}`}
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
                          <div className="guidance-section composition-highlights-section">
                            <h4>构图亮点</h4>
                            <CompositionHighlightsBlock text={selectedImage.composition_highlights} />
                          </div>
                        )}
                        {selectedImage.operation_guide && (
                          <div className="guidance-section operation-guide-section">
                            <h4>操作指南</h4>
                            <OperationGuideBlock text={selectedImage.operation_guide} />
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
  );
};

export default UploadPage;
