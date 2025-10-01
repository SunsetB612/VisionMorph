/**
 * 用户认证相关的TypeScript类型定义
 */

export interface User {
  id: number;
  username: string;
  email: string;
  avatar_path?: string;
  created_at: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

export interface AuthContextType {
  authState: AuthState;
  login: (credentials: LoginRequest) => Promise<void>;
  register: (userData: RegisterRequest) => Promise<void>;
  logout: () => void;
  updateUser: (userData: Partial<User>) => Promise<void>;
}

// 确保所有导出都被正确识别
export type {
  User,
  LoginRequest,
  RegisterRequest,
  LoginResponse,
  AuthState,
  AuthContextType
};
