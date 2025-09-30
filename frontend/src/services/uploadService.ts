import apiRequest from './api';

export const uploadService = {
  // 上传图片
  uploadImage: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    
    // TODO: 实现上传API调用
    return apiRequest('/upload', {
      method: 'POST',
      body: formData,
    });
  },

  // 获取上传状态
  getUploadStatus: async (uploadId: string) => {
    // TODO: 实现获取上传状态API调用
    return apiRequest(`/upload/status/${uploadId}`);
  }
};
