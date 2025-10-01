// 上传模块类型定义
export interface UploadFile {
  id: string;
  file: File;
  preview?: string;
  status: 'pending' | 'uploading' | 'success' | 'error';
  progress: number;
  error?: string;
  imageId?: number;
}

export interface UploadState {
  isUploading: boolean;
  uploadProgress: number;
  uploadedFiles: UploadFile[];
  error: string | null;
  isDragOver: boolean;
}

export interface UploadAction {
  type: 'SET_UPLOADING' | 'SET_PROGRESS' | 'ADD_FILE' | 'CLEAR_FILES' | 'SET_ERROR' | 'SET_DRAG_OVER';
  payload?: any;
}

// 拖拽相关类型
export interface DragDropProps {
  onFilesSelected: (files: File[]) => void;
  accept?: string;
  multiple?: boolean;
  disabled?: boolean;
  className?: string;
  children?: React.ReactNode;
}
