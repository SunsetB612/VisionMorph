// 结果模块类型定义
export interface ResultState {
  results: Result[];
  isLoading: boolean;
  selectedResult: Result | null;
  error: string | null;
}

export interface ResultAction {
  type: 'SET_RESULTS' | 'SET_LOADING' | 'SET_SELECTED' | 'ADD_RESULT' | 'REMOVE_RESULT' | 'SET_ERROR';
  payload?: any;
}
