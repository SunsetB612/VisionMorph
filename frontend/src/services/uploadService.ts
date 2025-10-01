import apiRequest from './api';

export const uploadService = {
  // 上传图片
  uploadImage: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch('http://localhost:8000/api/upload', {
      method: 'POST',
      body: formData,
    });
    
    if (!response.ok) {
      throw new Error(`上传失败: ${response.status}`);
    }
    
    return response.json();
  },

  // 获取上传状态
  getUploadStatus: async (uploadId: string) => {
    return apiRequest(`/api/upload/status/${uploadId}`);
  },

  // 批量上传图片
  uploadMultipleImages: async (files: File[]) => {
    const uploadPromises = files.map(file => uploadService.uploadImage(file));
    return Promise.all(uploadPromises);
  }
};
