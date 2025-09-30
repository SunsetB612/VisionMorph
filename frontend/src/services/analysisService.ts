import apiRequest from './api';

export const analysisService = {
  // 分析图片
  analyzeImage: async (imageId: string) => {
    // TODO: 实现分析API调用
    return apiRequest('/analyze', {
      method: 'POST',
      body: JSON.stringify({ imageId }),
    });
  },

  // 获取分析结果
  getAnalysisResult: async (analysisId: string) => {
    // TODO: 实现获取分析结果API调用
    return apiRequest(`/analyze/${analysisId}`);
  }
};
