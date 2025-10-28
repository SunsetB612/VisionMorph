import React, { useState } from 'react';
import './ViewAngleSelector.css';

export type ViewAngle = '俯视' | '仰视' | '平视' | '右前方' | '左前方' | '不限';

interface ViewAngleSelectorProps {
  onConfirm: (selectedAngles: ViewAngle[]) => void;
  onCancel?: () => void;
}

const ViewAngleSelector: React.FC<ViewAngleSelectorProps> = ({ onConfirm, onCancel }) => {
  const [selectedAngles, setSelectedAngles] = useState<ViewAngle[]>([]);

  const angles: ViewAngle[] = ['俯视', '仰视', '平视', '右前方', '左前方', '不限'];

  const angleEmojis: Record<ViewAngle, string> = {
    '俯视': '🔽',
    '仰视': '🔼',
    '平视': '↔️',
    '右前方': '↗️',
    '左前方': '↖️',
    '不限': '🎯'
  };

  const angleDescriptions: Record<ViewAngle, string> = {
    '俯视': '从上往下拍摄',
    '仰视': '从下往上拍摄',
    '平视': '水平角度拍摄',
    '右前方': '右前方角度',
    '左前方': '左前方角度',
    '不限': '不限制视角'
  };

  const handleAngleToggle = (angle: ViewAngle) => {
    setSelectedAngles(prev => {
      if (prev.includes(angle)) {
        // 如果已选中，则取消选择
        return prev.filter(a => a !== angle);
      } else {
        // 如果选择了"不限"，则清除其他选项
        if (angle === '不限') {
          return ['不限'];
        }
        // 如果之前选择了"不限"，现在选择具体角度，则移除"不限"
        const filtered = prev.filter(a => a !== '不限');
        return [...filtered, angle];
      }
    });
  };

  const handleConfirm = () => {
    if (selectedAngles.length === 0) {
      alert('请至少选择一个视角方向');
      return;
    }
    onConfirm(selectedAngles);
  };

  const handleSkip = () => {
    // 跳过选择，默认为"不限"
    onConfirm(['不限']);
  };

  return (
    <div className="view-angle-selector">
      <div className="selector-header">
        <h2>📐 选择拍摄视角</h2>
        <p className="selector-description">
          请选择您期望的拍摄视角方向（可多选），我们将生成符合这些视角的构图方案
        </p>
      </div>

      <div className="angle-grid">
        {angles.map(angle => (
          <button
            key={angle}
            className={`angle-option ${selectedAngles.includes(angle) ? 'selected' : ''}`}
            onClick={() => handleAngleToggle(angle)}
          >
            <span className="angle-emoji">{angleEmojis[angle]}</span>
            <span className="angle-name">{angle}</span>
            <span className="angle-desc">{angleDescriptions[angle]}</span>
            {selectedAngles.includes(angle) && (
              <span className="check-mark">✓</span>
            )}
          </button>
        ))}
      </div>

      <div className="selected-summary">
        {selectedAngles.length > 0 ? (
          <p>
            已选择 <strong>{selectedAngles.length}</strong> 个视角：
            <span className="selected-list">
              {selectedAngles.join('、')}
            </span>
          </p>
        ) : (
          <p className="hint">请选择至少一个视角方向</p>
        )}
      </div>

      <div className="selector-actions">
        <button
          className="skip-btn"
          onClick={handleSkip}
        >
          跳过选择（不限）
        </button>
        <button
          className="confirm-btn"
          onClick={handleConfirm}
          disabled={selectedAngles.length === 0}
        >
          确认并生成
        </button>
      </div>
    </div>
  );
};

export default ViewAngleSelector;

