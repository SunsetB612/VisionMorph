// 生成服务API调用
const API_BASE_URL = '/api';

export interface GenerationRequest {
  original_image_id: number;
}

export interface GenerationResponse {
  original_image_id: number;
  generated_count: number;
  message: string;
}

export interface GeneratedImageInfo {
  id: number;
  filename: string;
  file_path: string;
  created_at: string;
}

class GenerationService {
  /**
   * 创建图片生成任务
   */
  async createGenerationTask(request: GenerationRequest): Promise<GenerationResponse> {
    const response = await fetch(`${API_BASE_URL}/generate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || '创建生成任务失败');
    }

    return response.json();
  }

  /**
   * 获取生成的图片列表
   */
  async getGeneratedImages(originalImageId: number): Promise<GeneratedImageInfo[]> {
    const response = await fetch(`${API_BASE_URL}/generate/images/${originalImageId}`);

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || '获取生成图片失败');
    }

    return response.json();
  }

  /**
   * 获取生成任务状态（兼容性方法）
   * 实际上直接返回生成的图片列表
   */
  async getGenerationTask(originalImageId: number): Promise<{ generated_images: GeneratedImageInfo[] }> {
    const generatedImages = await this.getGeneratedImages(originalImageId);
    return {
      generated_images: generatedImages
    };
  }
}

export const generationService = new GenerationService();