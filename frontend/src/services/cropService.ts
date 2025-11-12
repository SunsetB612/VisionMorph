import apiRequest from './api';

export interface CropRequest {
  original_image_id: number;
  top_n?: number;
  method?: string | null;
  use_generated_images?: boolean;
}

export interface CropResponse {
  original_image_id: number;
  cropped_count: number;
  message: string;
}

export interface CroppedImageInfo {
  id: number;
  temp_image_id: number;
  filename: string;
  file_path: string;
  created_at: string;
}

export interface CropListResponse {
  original_image_id: number;
  total_count: number;
  crops: CroppedImageInfo[];
}

class CropService {
  async createCropTask(request: CropRequest): Promise<CropResponse> {
    return apiRequest('/api/crop', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async getCropsByOriginalId(originalImageId: number): Promise<CropListResponse> {
    return apiRequest(`/api/crop/${originalImageId}`);
  }
}

export const cropService = new CropService();

