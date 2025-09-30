import { create } from 'zustand';

interface UploadState {
  isUploading: boolean;
  uploadProgress: number;
  uploadedFiles: File[];
  setUploading: (uploading: boolean) => void;
  setProgress: (progress: number) => void;
  addFile: (file: File) => void;
  clearFiles: () => void;
}

export const useUploadStore = create<UploadState>((set) => ({
  isUploading: false,
  uploadProgress: 0,
  uploadedFiles: [],
  setUploading: (uploading) => set({ isUploading: uploading }),
  setProgress: (progress) => set({ uploadProgress: progress }),
  addFile: (file) => set((state) => ({ 
    uploadedFiles: [...state.uploadedFiles, file] 
  })),
  clearFiles: () => set({ uploadedFiles: [] }),
}));
