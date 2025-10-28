// 生成服务API调用
// 注意：API_BASE_URL 应该是 http://localhost:8000，端点路径会添加 /api/generate
const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000') + '/api';

export interface GenerationRequest {
  original_image_id: number;
  view_angles?: string[];
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

export interface GenerationProgressUpdate {
  status: 'started' | 'generating' | 'completed' | 'failed';
  current: number;
  total: number;
  message: string;
}

export type ProgressCallback = (progress: GenerationProgressUpdate) => void;

class GenerationService {
  private getAuthHeaders() {
    const token = localStorage.getItem('auth_token');
    if (!token) {
      throw new Error('未登录，请先登录');
    }
    return {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    };
  }

  /**
   * 创建图片生成任务
   */
  async createGenerationTask(request: GenerationRequest): Promise<GenerationResponse> {
    const response = await fetch(`${API_BASE_URL}/generate`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
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
    const response = await fetch(`${API_BASE_URL}/generate/images/${originalImageId}`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('auth_token')}`,
      },
    });

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

  /**
   * 创建图片生成任务（SSE 流式版本，支持实时进度）
   * @param request 生成请求
   * @param onProgress 进度回调函数
   * @returns Promise，在任务完成或失败时 resolve
   */
  async createGenerationTaskWithProgress(
    request: GenerationRequest,
    onProgress: ProgressCallback
  ): Promise<void> {
    const token = localStorage.getItem('auth_token');
    if (!token) {
      throw new Error('未登录，请先登录');
    }

    return new Promise<void>((resolve, reject) => {
      // 使用 fetch + ReadableStream 处理 SSE
      fetch(`${API_BASE_URL}/generate/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(request),
      })
        .then(async (response) => {
          if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || '创建生成任务失败');
          }

          const reader = response.body?.getReader();
          if (!reader) {
            throw new Error('无法读取响应流');
          }

          const decoder = new TextDecoder();
          let buffer = '';

          // 读取流数据
          while (true) {
            const { done, value } = await reader.read();

            if (done) {
              break;
            }

            // 解码数据块
            buffer += decoder.decode(value, { stream: true });

            // 处理完整的 SSE 消息
            const lines = buffer.split('\n');
            buffer = lines.pop() || ''; // 保留最后一个不完整的行

            for (const line of lines) {
              if (line.startsWith('data: ')) {
                try {
                  const data = JSON.parse(line.substring(6));
                  const progress: GenerationProgressUpdate = {
                    status: data.status,
                    current: data.current,
                    total: data.total,
                    message: data.message,
                  };

                  // 调用进度回调
                  onProgress(progress);

                  // 如果完成或失败，结束 Promise
                  if (progress.status === 'completed') {
                    resolve();
                  } else if (progress.status === 'failed') {
                    reject(new Error(progress.message));
                  }
                } catch (e) {
                  console.error('解析 SSE 数据失败:', e, line);
                }
              }
            }
          }
        })
        .catch((error) => {
          reject(error);
        });
    });
  }

  /**
   * 使用 EventSource 创建生成任务（备选方案，仅支持 GET）
   * 注意：EventSource 不支持 POST 和自定义 body，所以需要后端额外支持 GET 接口
   * 这个方法作为参考，实际使用 createGenerationTaskWithProgress
   */
  createGenerationTaskWithEventSource(
    request: GenerationRequest,
    onProgress: ProgressCallback
  ): Promise<void> {
    const token = localStorage.getItem('auth_token');
    if (!token) {
      return Promise.reject(new Error('未登录，请先登录'));
    }

    return new Promise<void>((resolve, reject) => {
      // 注意：EventSource 不支持 POST，这里仅作示例
      // 实际应用中建议使用 createGenerationTaskWithProgress
      const eventSource = new EventSource(
        `${API_BASE_URL}/generate/stream?original_image_id=${request.original_image_id}&view_angles=${request.view_angles?.join(',') || ''}`,
        {
          // EventSource 不支持自定义 headers，需要通过 URL 参数传递 token
          // 或者使用 createGenerationTaskWithProgress
        }
      );

      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          const progress: GenerationProgressUpdate = {
            status: data.status,
            current: data.current,
            total: data.total,
            message: data.message,
          };

          onProgress(progress);

          if (progress.status === 'completed') {
            eventSource.close();
            resolve();
          } else if (progress.status === 'failed') {
            eventSource.close();
            reject(new Error(progress.message));
          }
        } catch (e) {
          console.error('解析进度数据失败:', e);
        }
      };

      eventSource.onerror = (error) => {
        console.error('SSE 连接错误:', error);
        eventSource.close();
        reject(new Error('SSE 连接失败'));
      };
    });
  }
}

export const generationService = new GenerationService();