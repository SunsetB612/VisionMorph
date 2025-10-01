import apiRequest from './api';

// API基础配置
const API_BASE_URL = 'http://localhost:8000';

export const uploadService = {
  // 上传图片
  uploadImage: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    
    // 获取认证token
    const token = localStorage.getItem('auth_token');
    if (!token) {
      throw new Error('未登录，请先登录');
    }
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/upload`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
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
