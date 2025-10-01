import { useCallback } from 'react';
import { useUploadStore } from '../store/uploadStore';
import { uploadService } from '../services/uploadService';
import type { UploadFile } from '../types/upload';

export const useUpload = () => {
  const {
    isUploading,
    uploadProgress,
    uploadedFiles,
    isDragOver,
    error,
    setUploading,
    addFile,
    updateFile,
    setDragOver,
    setError
  } = useUploadStore();

  const uploadFile = async (file: File) => {
    const fileId = Math.random().toString(36).substr(2, 9);
    const uploadFile: UploadFile = {
      id: fileId,
      file,
      status: 'pending',
      progress: 0
    };

    addFile(uploadFile);
    setUploading(true);
    setError(null);

    try {
      updateFile(fileId, { status: 'uploading', progress: 0 });
      
      const response = await uploadService.uploadImage(file);
      
      updateFile(fileId, { 
        status: 'success', 
        progress: 100,
        imageId: response.image_id
      });
      
      return response;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : '上传失败';
      updateFile(fileId, { 
        status: 'error', 
        error: errorMessage 
      });
      setError(errorMessage);
      throw error;
    } finally {
      setUploading(false);
    }
  };

  const uploadMultipleFiles = async (files: File[]) => {
    setUploading(true);
    setError(null);

    try {
      const uploadPromises = files.map(file => uploadFile(file));
      return await Promise.all(uploadPromises);
    } finally {
      setUploading(false);
    }
  };

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragOver(true);
  }, [setDragOver]);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragOver(false);
  }, [setDragOver]);

  const handleDrop = useCallback((e: React.DragEvent, onFilesSelected?: (files: File[]) => void) => {
    e.preventDefault();
    e.stopPropagation();
    setDragOver(false);

    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      if (onFilesSelected) {
        onFilesSelected(files);
      } else {
        uploadMultipleFiles(files);
      }
    }
  }, [setDragOver, uploadMultipleFiles]);

  return {
    isUploading,
    uploadProgress,
    uploadedFiles,
    isDragOver,
    error,
    uploadFile,
    uploadMultipleFiles,
    handleDragOver,
    handleDragLeave,
    handleDrop,
    setError
  };
};
