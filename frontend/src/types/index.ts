// 通用类型定义
export interface ApiResponse<T = any> {
  success: boolean;
  data: T;
  message?: string;
}

// 上传相关类型
export interface UploadFile {
  id: string;
  name: string;
  size: number;
  type: string;
  url: string;
  uploadTime: string;
}

export interface UploadProgress {
  loaded: number;
  total: number;
  percentage: number;
}

// 生成相关类型
export interface GenerationOptions {
  style?: string;
  quality?: 'low' | 'medium' | 'high';
  count?: number;
}

export interface GeneratedImage {
  id: string;
  originalImageId: string;
  url: string;
  style: string;
  score: number;
  createdAt: string;
}

// 结果相关类型
export interface Result {
  id: string;
  originalImage: UploadFile;
  generatedImages: GeneratedImage[];
  analysis: AnalysisResult;
  createdAt: string;
}

// 分析相关类型
export interface AnalysisResult {
  composition: string;
  colorHarmony: number;
  balance: number;
  focus: number;
  overallScore: number;
  suggestions: string[];
}
