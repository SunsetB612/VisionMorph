import apiRequest from './api';

// API基础配置
const API_BASE_URL = 'http://localhost:8000';

export const uploadService = {
  // 上传图片
  uploadImage: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/upload`, {
        method: 'POST',
        body: formData,
      });
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('Upload error response:', errorText);
        throw new Error(`上传失败: ${response.status} - ${errorText}`);
      }
      
      const result = await response.json();
      console.log('Upload success:', result);
      return result;
    } catch (error) {
      console.error('Upload error:', error);
      throw error;
    }
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
