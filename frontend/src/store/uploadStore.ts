import { create } from 'zustand';
import type { UploadFile } from '../types/upload';

interface UploadState {
  isUploading: boolean;
  uploadProgress: number;
  uploadedFiles: UploadFile[];
  isDragOver: boolean;
  error: string | null;
  setUploading: (uploading: boolean) => void;
  setProgress: (progress: number) => void;
  addFile: (file: UploadFile) => void;
  updateFile: (id: string, updates: Partial<UploadFile>) => void;
  clearFiles: () => void;
  setDragOver: (isDragOver: boolean) => void;
  setError: (error: string | null) => void;
}

export const useUploadStore = create<UploadState>((set) => ({
  isUploading: false,
  uploadProgress: 0,
  uploadedFiles: [],
  isDragOver: false,
  error: null,
  setUploading: (uploading) => set({ isUploading: uploading }),
  setProgress: (progress) => set({ uploadProgress: progress }),
  addFile: (file) => set((state) => ({ 
    uploadedFiles: [...state.uploadedFiles, file] 
  })),
  updateFile: (id, updates) => set((state) => ({
    uploadedFiles: state.uploadedFiles.map(file => 
      file.id === id ? { ...file, ...updates } : file
    )
  })),
  clearFiles: () => set({ 
    uploadedFiles: [],
    isUploading: false,
    uploadProgress: 0,
    error: null
  }),
  setDragOver: (isDragOver) => set({ isDragOver }),
  setError: (error) => set({ error }),
}));
