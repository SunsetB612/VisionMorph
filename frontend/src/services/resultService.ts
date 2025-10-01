import apiRequest from './api';

export interface ResultInfo {
  generated_image_id: number;
  filename: string;
  file_path: string;
  overall_score: number;
  highlights: string;
  ai_comment: string;
  shooting_guidance: string;
  created_at: string;
}

export interface GeneratedImageWithResult {
  id: number;
  filename: string;
  created_at: string;
  result?: ResultInfo;
}

export interface OriginalImageResults {
  original_image_id: number;
  original_filename: string;
  generated_images: GeneratedImageWithResult[];
}

export interface UserResults {
  user_id: number;
  results: OriginalImageResults[];
}

export interface ResultStatistics {
  total_results: number;
  average_score: number;
  score_distribution: Record<string, number>;
}

class ResultService {
  /**
   * 获取生成图片的评分结果
   */
  async getResultByGeneratedId(generatedId: number): Promise<ResultInfo> {
    const response = await apiRequest(`/api/result/generated/${generatedId}`);
    // 后端返回的是 { result: ResultDetailInfo } 结构，需要提取 result 字段
    return response.result;
  }

  /**
   * 获取原始图片的所有生成结果
   */
  async getResultsByOriginalId(originalId: number): Promise<OriginalImageResults> {
    const response = await apiRequest(`/api/result/original/${originalId}`);
    return response;
  }

  /**
   * 获取用户的所有结果
   */
  async getUserResults(userId: number): Promise<UserResults> {
    const response = await apiRequest(`/api/result/user/${userId}`);
    return response;
  }

  /**
   * 获取结果统计信息
   */
  async getResultStatistics(): Promise<ResultStatistics> {
    const response = await apiRequest('/api/result/statistics');
    return response;
  }
}

export const resultService = new ResultService();