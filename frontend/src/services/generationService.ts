import apiRequest from './api';

export const generationService = {
  // 生成图片
  generateImages: async (imageId: string, options?: any) => {
    // TODO: 实现生成API调用
    return apiRequest('/generate', {
      method: 'POST',
      body: JSON.stringify({ imageId, options }),
    });
  },

  // 获取生成状态
  getGenerationStatus: async (generationId: string) => {
    // TODO: 实现获取生成状态API调用
    return apiRequest(`/generate/status/${generationId}`);
  }
};
