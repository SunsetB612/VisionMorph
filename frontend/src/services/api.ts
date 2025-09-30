// API基础配置
const API_BASE_URL = 'http://localhost:8000';

// 通用API请求函数
const apiRequest = async (endpoint: string, options: RequestInit = {}) => {
  const url = `${API_BASE_URL}${endpoint}`;
  
  const defaultOptions: RequestInit = {
    headers: {
      'Content-Type': 'application/json',
    },
  };

  const response = await fetch(url, { ...defaultOptions, ...options });
  
  if (!response.ok) {
    throw new Error(`API请求失败: ${response.status}`);
  }

  return response.json();
};

export default apiRequest;
