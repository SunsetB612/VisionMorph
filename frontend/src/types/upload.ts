// 上传模块类型定义
export interface UploadState {
  isUploading: boolean;
  uploadProgress: number;
  uploadedFiles: UploadFile[];
  error: string | null;
}

export interface UploadAction {
  type: 'SET_UPLOADING' | 'SET_PROGRESS' | 'ADD_FILE' | 'CLEAR_FILES' | 'SET_ERROR';
  payload?: any;
}
