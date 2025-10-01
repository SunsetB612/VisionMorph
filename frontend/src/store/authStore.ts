/**
 * 用户认证状态管理
 */
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface User {
  id: number;
  username: string;
  email: string;
  avatar_path?: string;
  created_at: string;
}

interface LoginRequest {
  email: string;
  password: string;
}

interface RegisterRequest {
  username: string;
  email: string;
  password: string;
}

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

const API_BASE_URL = 'http://localhost:8000/api/auth';

interface AuthStore extends AuthState {
  // Actions
  login: (credentials: LoginRequest) => Promise<void>;
  register: (userData: RegisterRequest) => Promise<void>;
  logout: () => void;
  updateUser: (userData: Partial<User>) => Promise<void>;
  checkAuth: () => Promise<void>;
  setLoading: (loading: boolean) => void;
}

export const useAuthStore = create<AuthStore>()(
  persist(
    (set, get) => ({
      // Initial state
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,

      // Actions
      setLoading: (loading: boolean) => {
        set({ isLoading: loading });
      },

      login: async (credentials: LoginRequest) => {
        set({ isLoading: true });
        try {
          const response = await fetch(`${API_BASE_URL}/login`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify(credentials),
          });

          if (!response.ok) {
            let errorMessage = '登录失败';
            try {
              const errorData = await response.json();
              console.log('后端错误响应:', errorData);
              errorMessage = errorData.detail || errorMessage;
              console.log('提取的错误信息:', errorMessage);
            } catch (parseError) {
              console.error('解析错误响应失败:', parseError);
              errorMessage = `登录失败 (${response.status})`;
            }
            console.log('抛出错误:', errorMessage);
            throw new Error(errorMessage);
          }

          const data = await response.json();
          
          // 保存token到localStorage
          localStorage.setItem('auth_token', data.access_token);
          
          set({
            user: data.user,
            token: data.access_token,
            isAuthenticated: true,
            isLoading: false,
          });
        } catch (error) {
          console.error('登录错误:', error);
          // 只重置isLoading状态，不触发其他状态更新
          set({ isLoading: false });
          throw error;
        }
      },

      register: async (userData: RegisterRequest) => {
        set({ isLoading: true });
        try {
          const response = await fetch(`${API_BASE_URL}/register`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify(userData),
          });

          if (!response.ok) {
            let errorMessage = '注册失败';
            try {
              const errorData = await response.json();
              errorMessage = errorData.detail || errorMessage;
            } catch (parseError) {
              console.error('解析错误响应失败:', parseError);
              errorMessage = `注册失败 (${response.status})`;
            }
            throw new Error(errorMessage);
          }

          set({ isLoading: false });
          // 注册成功后自动登录
          await get().login({
            email: userData.email,
            password: userData.password,
          });
        } catch (error) {
          console.error('注册错误:', error);
          // 只重置isLoading状态，不触发其他状态更新
          set({ isLoading: false });
          throw error;
        }
      },

      logout: () => {
        localStorage.removeItem('auth_token');
        set({
          user: null,
          token: null,
          isAuthenticated: false,
          isLoading: false,
        });
      },

      updateUser: async (userData: Partial<User>) => {
        const { token } = get();
        if (!token) {
          throw new Error('未登录');
        }

        set({ isLoading: true });
        try {
          const response = await fetch(`${API_BASE_URL}/me`, {
            method: 'PUT',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${token}`,
            },
            body: JSON.stringify(userData),
          });

          if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || '更新用户信息失败');
          }

          const updatedUser = await response.json();
          set({
            user: updatedUser,
            isLoading: false,
          });
        } catch (error) {
          set({ isLoading: false });
          throw error;
        }
      },

      checkAuth: async () => {
        const token = localStorage.getItem('auth_token');
        if (!token) {
          set({
            user: null,
            token: null,
            isAuthenticated: false,
            isLoading: false,
          });
          return;
        }

        set({ isLoading: true });
        try {
          const response = await fetch(`${API_BASE_URL}/me`, {
            method: 'GET',
            headers: {
              'Authorization': `Bearer ${token}`,
            },
          });

          if (!response.ok) {
            if (response.status === 401) {
              // Token过期或无效，清除本地存储
              localStorage.removeItem('auth_token');
              get().logout();
              return;
            }
            throw new Error('获取用户信息失败');
          }

          const user = await response.json();
          set({
            user,
            token,
            isAuthenticated: true,
            isLoading: false,
          });
        } catch (error) {
          console.error('检查认证状态失败:', error);
          // 认证失败，清除状态
          get().logout();
        }
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        token: state.token,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);