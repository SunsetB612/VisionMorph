// 生成模块类型定义
export interface GeneratedImageInfo {
  id: number;
  filename: string;
  file_path: string;
  created_at: string;
}

export interface GenerationState {
  isGenerating: boolean;
  generationProgress: number;
  generatedImages: GeneratedImageInfo[];
  error: string | null;
}

export interface GenerationAction {
  type: 'SET_GENERATING' | 'SET_PROGRESS' | 'ADD_IMAGE' | 'CLEAR_IMAGES' | 'SET_ERROR';
  payload?: any;
}
