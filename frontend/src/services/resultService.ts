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

export interface StaticImageResult {
  id: string;
  group: string;
  image_name: string;
  filename: string;
  relative_path: string;
  overall_score: number;
  shooting_guidance?: string;
  /** Excel：一句话概括优势特征 */
  viewpoint_feature?: string;
  /** Excel：推荐视角优点 */
  composition_highlights?: string;
  /** Excel：操作指南 */
  operation_guide?: string;
  orientation?: string;
  crop_type?: string;
}

export interface StaticResultResponse {
  total_count: number;
  results: StaticImageResult[];
}

export interface ShowcaseEvolutionItem {
  input_key: string;
  original_relative_path: string | null;
  best_result: StaticImageResult | null;
}

export interface ShowcaseEvolutionResponse {
  items: ShowcaseEvolutionItem[];
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

  /**
   * 获取固定输出目录中的图片结果
   */
  async getStaticResults(inputKey?: string): Promise<StaticResultResponse> {
    const query = inputKey ? `?input_key=${encodeURIComponent(inputKey)}` : '';
    const response = await apiRequest(`/api/result/static${query}`);
    return response;
  }

  /** 构图进化论：input 1/2/3 与各 output 下评分最高的一张 */
  async getShowcaseEvolution(): Promise<ShowcaseEvolutionResponse> {
    return apiRequest('/api/result/static/showcase');
  }
}

export const resultService = new ResultService();