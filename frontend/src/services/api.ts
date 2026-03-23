import { getApiBaseUrl } from '../config/apiBase';

// 通用API请求函数
const apiRequest = async (endpoint: string, options: RequestInit = {}) => {
  const url = `${getApiBaseUrl()}${endpoint}`;
  
  // 获取认证token
  const token = localStorage.getItem('auth_token');
  
  const defaultOptions: RequestInit = {
    headers: {
      'Content-Type': 'application/json',
      ...(token && { 'Authorization': `Bearer ${token}` }),
    },
  };

  const response = await fetch(url, { ...defaultOptions, ...options });
  
  if (!response.ok) {
    throw new Error(`API请求失败: ${response.status}`);
  }

  return response.json();
};

export default apiRequest;
