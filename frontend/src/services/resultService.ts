import apiRequest from './api';

export const resultService = {
  // 获取结果列表
  getResults: async () => {
    // TODO: 实现获取结果API调用
    return apiRequest('/results');
  },

  // 获取单个结果
  getResult: async (resultId: string) => {
    // TODO: 实现获取单个结果API调用
    return apiRequest(`/results/${resultId}`);
  },

  // 下载结果
  downloadResult: async (resultId: string) => {
    // TODO: 实现下载结果API调用
    return apiRequest(`/results/${resultId}/download`);
  }
};
