import React, { useEffect, useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useUploadStore } from '../../store/uploadStore';
import { useAuthStore } from '../../store/authStore';
import { resultService } from '../../services/resultService';
import type { ShowcaseEvolutionItem } from '../../services/resultService';
import { getApiBaseUrl } from '../../config/apiBase';
import './HomePage.css';

/** 核心能力四格（与 test.html 一致；全端共用，断点仅调间距与栅格） */
const MOBILE_FEATURE_PILLS: { key: string; label: string; icon: string }[] = [
  { key: 'score', label: '评分指导', icon: '⭐' },
  { key: 'highlight', label: '亮点分析', icon: '🖌️' },
  { key: 'view', label: '视角重塑', icon: '✨' },
  { key: 'shoot', label: '拍摄建议', icon: '📷' },
];

const HomePage: React.FC = () => {
  const navigate = useNavigate();
  const { clearFiles } = useUploadStore();
  const { isAuthenticated, user } = useAuthStore();
  const [showcaseItems, setShowcaseItems] = useState<ShowcaseEvolutionItem[] | null>(null);

  const handleStartUpload = () => {
    // 清理所有上传相关的状态，确保重新开始
    clearFiles();
    navigate('/upload');
  };

  const goToCompose = () => {
    clearFiles();
    if (isAuthenticated) {
      navigate('/upload');
    } else {
      navigate('/auth');
    }
  };

  useEffect(() => {
    let cancelled = false;
    resultService
      .getShowcaseEvolution()
      .then((res) => {
        if (!cancelled) {
          setShowcaseItems(res.items);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setShowcaseItems([]);
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="home-page">
      {/* 与 test.html 一致：单图 + 左渐变 + 文案（Web 与移动端仅布局不同） */}
      <section className="home-hero-banner" aria-label="VisionMorph 品牌横幅">
        <div className="home-hero-banner-card">
          <div className="home-hero-banner-media">
            <img
              className="home-hero-banner-img"
              src="https://modao.cc/agent-py/media/generated_images/2026-03-22/67970f2603b0412e81881a38275b68c4.jpg"
              alt=""
              decoding="async"
            />
            <div className="home-hero-banner-overlay">
              <h1 className="home-hero-banner-title">
                VisionMorph
                <br />
                智能构图 2.0
              </h1>
              <p className="home-hero-banner-tagline">10秒生成电影感新视角</p>
              <div className="home-hero-banner-tags">
                <span># AI驱动</span>
                <span># 专业评分</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <div className="hero-section">
        <h1 className="hero-title">VisionMorph 智能构图系统</h1>
        <p className="hero-subtitle">
          AI智能构图生成新视角图片，提供专业评分与拍摄指导
        </p>

        {/* test.html 核心功能矩阵：上传图片 + AI智能构图 */}
        <div className="hero-core-matrix">
          <button
            type="button"
            className="hero-core-card"
            onClick={goToCompose}
          >
            <div className="hero-core-card-icon hero-core-card-icon--blue" aria-hidden>
              📸
            </div>
            <span className="hero-core-card-title">上传图片</span>
            <span className="hero-core-card-desc">支持多种格式</span>
          </button>
          <button
            type="button"
            className="hero-core-card hero-core-card--hot"
            onClick={goToCompose}
          >
            <span className="hero-core-card-badge">HOT</span>
            <div className="hero-core-card-icon hero-core-card-icon--orange" aria-hidden>
              🎨
            </div>
            <span className="hero-core-card-title">AI智能构图</span>
            <span className="hero-core-card-desc">寻找最佳视觉视角</span>
          </button>
        </div>

        <div className="hero-pills" aria-label="核心能力">
          {MOBILE_FEATURE_PILLS.map((item) => (
            <div key={item.key} className="hero-feature-pill">
              <div className="hero-feature-pill-icon-wrap">
                <span className="hero-feature-pill-icon" aria-hidden>
                  {item.icon}
                </span>
              </div>
              <span className="hero-feature-pill-label">{item.label}</span>
            </div>
          ))}
        </div>

        <section className="home-showcase" aria-labelledby="home-showcase-heading">
          <div className="home-showcase-head">
            <h2 id="home-showcase-heading" className="home-showcase-title">
              构图进化论
              <span className="home-showcase-badge">BEFORE/AFTER</span>
            </h2>
          </div>
          {showcaseItems === null && (
            <p className="home-showcase-loading">加载示例对比…</p>
          )}
          {showcaseItems && showcaseItems.length === 0 && (
            <p className="home-showcase-empty">暂无示例数据（请配置项目下 input/ 与 output/ 目录）</p>
          )}
          {showcaseItems && showcaseItems.length > 0 && (
            <div className="home-showcase-scroll">
              {showcaseItems.map((item) => {
                const caption =
                  item.best_result?.viewpoint_feature?.trim() ||
                  item.best_result?.image_name?.trim() ||
                  `示例 ${item.input_key}`;
                return (
                  <article key={item.input_key} className="home-showcase-card">
                    <div className="home-showcase-compare">
                      <div className="home-showcase-half">
                        {item.original_relative_path ? (
                          <img
                            src={`${getApiBaseUrl()}${item.original_relative_path}`}
                            alt="原图"
                          />
                        ) : (
                          <div className="home-showcase-placeholder">暂无原图</div>
                        )}
                        <span className="home-showcase-label home-showcase-label--before">原图</span>
                      </div>
                      <div className="home-showcase-half">
                        {item.best_result ? (
                          <img
                            src={`${getApiBaseUrl()}${item.best_result.relative_path}`}
                            alt="AI 生成视角"
                          />
                        ) : (
                          <div className="home-showcase-placeholder">暂无 AI 图</div>
                        )}
                        <span className="home-showcase-label home-showcase-label--after">AI视角</span>
                      </div>
                    </div>
                    <div className="home-showcase-footer">
                      <div className="home-showcase-caption">{caption}</div>
                      {item.best_result && (
                        <div className="home-showcase-meta">
                          <span className="home-showcase-chip">
                            构图评分: {item.best_result.overall_score.toFixed(1)}
                          </span>
                        </div>
                      )}
                    </div>
                  </article>
                );
              })}
            </div>
          )}
        </section>

        <div className="hero-actions">
          {isAuthenticated ? (
            <div className="auth-actions">
              <button className="auth-button primary" onClick={handleStartUpload}>
                开始智能构图
              </button>
              <p className="auth-hint">欢迎回来，{user?.username}！开始您的创作之旅</p>
            </div>
          ) : (
            <div className="auth-actions">
              <Link to="/auth" className="auth-button primary">
                开始使用
              </Link>
              <p className="auth-hint">注册账户，体验AI智能构图生成功能</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default HomePage;