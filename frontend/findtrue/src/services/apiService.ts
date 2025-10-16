// frontend/findtrue/src/services/apiService.ts

import axios, { AxiosError } from 'axios';
import type {
  // 基础响应类型
  ApiResponse,
  OperationResponse,
  
  // 核心基础类型
  Author,
  User,
  UserProfileUpdatePayload,
  
  // 认证模块类型
  LoginResponse,
  RegisterData,
  LoginData,
  PasswordResetRequest,
  PasswordResetConfirm,
  
  // 课程模块类型
  Course,
  CourseDetail,
  Chapter,
  Exercise,
  ExerciseAnswer,
  Progress,
  SubmissionResult,
  
  // 画廊模块类型
  GalleryItem,
  GalleryItemDetail,
  
  // 社群模块类型
  Community,
  CommunityPost,
  CommunityReply,
  CommunityPostListItem,
  
  // 站内信模块类型
  Message,
  MessageThread,
  MessageThreadDetail,
  
  // 个人中心模块类型
  MyCollections,
  MySupported,
  MyCreations,
  MyParticipations,
  
  // VIP套餐类型
  VipPlan,
  
  // 错误处理类型
  AxiosErrorResponse,
  CustomAxiosError
} from '../types'; 


  

const apiClient = axios.create({
  baseURL: 'http://127.0.0.1:8000/v1/',
  headers: {
    'Content-Type': 'application/json',
  },
});

// --- 智能拦截器 ---
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('accessToken');
    
    if (token) {
      try {
        const parts = token.split('.');
        const [header, payloadString, signature] = parts;
        // 关键检查：确保 token 至少有 payload 部分
        if (!payloadString) {
          throw new Error("Invalid token format");
        }
        const payload = JSON.parse(atob(payloadString));
        const isExpired = Date.now() >= payload.exp * 1000;

        if (isExpired) {
          localStorage.removeItem('accessToken');
          localStorage.removeItem('refreshToken');
          console.warn("Access token has expired. Request is being sent without authentication.");
        } else {
          // Token 有效，添加到请求头
          config.headers.Authorization = `Bearer ${token}`;
        }
      } catch (e) {
        // 解码失败或格式错误，都移除它
        localStorage.removeItem('accessToken');
        localStorage.removeItem('refreshToken');
        console.error("Failed to decode token. Removing token.", e);
        // 强制重新登录
        window.location.href = '/login'; 
      }
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 处理API错误的辅助函数
const handleApiError = (error: CustomAxiosError): ApiResponse<never> => {
  console.error('API Error:', error);
  
  if (error.response) {
    // 服务器返回了错误状态码
    const errorData = error.response.data || {};
    const errorMessage = errorData.detail || 
                         errorData.error || 
                         errorData.message || 
                         `请求失败: ${error.response.status || '未知状态码'}`;
    return {
      success: false,
      error: errorMessage
    };
  } else if (error.request) {
    // 请求已发送但没有收到响应
    return {
      success: false,
      error: '网络错误，请检查您的网络连接'
    };
  } else {
    // 其他错误
    return {
      success: false,
      error: `请求配置错误: ${error.message || '未知错误'}`
    };
  }
};

// --- API 函数 ---
// 认证相关API
export const authService = {
  // 用户注册
  register: async (data: RegisterData): Promise<ApiResponse<OperationResponse>> => {
    try {
      const response = await apiClient.post('/auth/register/', data);
      return { success: true, data: response.data };
    } catch (error) {
      return handleApiError(error as CustomAxiosError);
    }
  },
  
  // 用户登录 - 支持用户名、邮箱或手机号
  login: async (data: LoginData): Promise<ApiResponse<LoginResponse>> => {
    try {
      const response = await apiClient.post('/auth/login/', data);
      
      // 保存token到localStorage
      if (response.data.tokens) {
        localStorage.setItem('accessToken', response.data.tokens.access);
        localStorage.setItem('refreshToken', response.data.tokens.refresh);
        localStorage.setItem('userData', JSON.stringify(response.data.user));
        
        // 更新axios默认headers
        apiClient.defaults.headers.Authorization = `Bearer ${response.data.tokens.access}`;
      }
      
      return { success: true, data: response.data };
    } catch (error) {
      return handleApiError(error as CustomAxiosError);
    }
  },
  
  // 密码重置请求
  resetPasswordRequest: async (data: PasswordResetRequest): Promise<ApiResponse<OperationResponse>> => {
    try {
      const response = await apiClient.post('/auth/forgot-password/send-code/', data);
      return { success: true, data: response.data };
    } catch (error) {
      return handleApiError(error as CustomAxiosError);
    }
  },
  
  // 密码重置确认
  resetPasswordConfirm: async (data: PasswordResetConfirm): Promise<ApiResponse<OperationResponse>> => {
    try {
      const response = await apiClient.post('/auth/reset-password/', data);
      return { success: true, data: response.data };
    } catch (error) {
      return handleApiError(error as CustomAxiosError);
    }
  },
  
  // 退出登录
  logout: (): void => {
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
    localStorage.removeItem('userData');
    delete apiClient.defaults.headers.Authorization;
  },
  
  // 更新用户资料
  updateProfile: async (data: UserProfileUpdatePayload): Promise<ApiResponse<User>> => {
    try {
      const response = await apiClient.put('/auth/profile/', data);
      // 更新本地存储的用户数据
      if (response.data) {
        localStorage.setItem('userData', JSON.stringify(response.data));
      }
      return { success: true, data: response.data };
    } catch (error) {
      return handleApiError(error as CustomAxiosError);
    }
  },
  
  // 获取当前登录用户信息
  getCurrentUser: (): User | null => {
    const userData = localStorage.getItem('userData');
    return userData ? JSON.parse(userData) : null;
  },
  
  // 检查用户是否已登录
  isLoggedIn: (): boolean => {
    return !!localStorage.getItem('accessToken');
  }
};

export const getCourses = async (): Promise<ApiResponse<Course[]>> => {
  try {
    const response = await apiClient.get<Course[]>('/courses/');
    return { success: true, data: response.data };
  } catch (error) {
    return handleApiError(error as CustomAxiosError);
  }
};

export const getCourseDetail = async (id: string): Promise<ApiResponse<CourseDetail>> => {
  try {
    const response = await apiClient.get<CourseDetail>(`/courses/${id}/`);
    return { success: true, data: response.data };
  } catch (error) {
    return handleApiError(error as CustomAxiosError);
  }
};

export const subscribeCourse = async (courseId: string): Promise<ApiResponse<OperationResponse>> => {
  try {
    const response = await apiClient.post(`/courses/${courseId}/subscribe/`);
    return { success: true, data: response.data };
  } catch (error) {
    return handleApiError(error as CustomAxiosError);
  }
};

export const unsubscribeCourse = async (courseId: string): Promise<ApiResponse<OperationResponse>> => {
  try {
    const response = await apiClient.delete(`/courses/${courseId}/subscribe/`);
    return { success: true, data: response.data };
  } catch (error) {
    return handleApiError(error as CustomAxiosError);
  }
};

export const collectCourse = async (courseId: string): Promise<ApiResponse<OperationResponse>> => {
  try {
    const response = await apiClient.post(`/courses/${courseId}/collect/`);
    return { success: true, data: response.data };
  } catch (error) {
    return handleApiError(error as CustomAxiosError);
  }
};

export const uncollectCourse = async (courseId: string): Promise<ApiResponse<OperationResponse>> => {
  try {
    const response = await apiClient.delete(`/courses/${courseId}/collect/`);
    return { success: true, data: response.data };
  } catch (error) {
    return handleApiError(error as CustomAxiosError);
  }
};

export const getCourseProgress = async (courseId: string): Promise<ApiResponse<Progress>> => {
  try {
    const response = await apiClient.get<Progress>(`/courses/${courseId}/progress/`);
    return { success: true, data: response.data };
  } catch (error) {
    return handleApiError(error as CustomAxiosError);
  }
};

export const submitChapterExercises = async (courseId: string, chapterId: string, answers: ExerciseAnswer[]): Promise<ApiResponse<SubmissionResult>> => {
  try {
    const response = await apiClient.post<SubmissionResult>(`/courses/${courseId}/chapters/${chapterId}/submit/`, { answers });
    return { success: true, data: response.data };
  } catch (error) {
    return handleApiError(error as CustomAxiosError);
  }
};


export const getGalleryWorks = async (): Promise<ApiResponse<GalleryItem[]>> => {
  try {
    const response = await apiClient.get<GalleryItem[]>('/gallery/works/');
    return { success: true, data: response.data };
  } catch (error) {
    return handleApiError(error as CustomAxiosError);
  }
};

export const getGalleryWorkDetail = async (id: string): Promise<ApiResponse<GalleryItemDetail>> => {
  try {
    const response = await apiClient.get<GalleryItemDetail>(`/gallery/works/${id}/`);
    return { success: true, data: response.data };
  } catch (error) {
    return handleApiError(error as CustomAxiosError);
  }
};

export const collectGalleryWork = async (workId: string): Promise<ApiResponse<OperationResponse>> => {
  try {
    const response = await apiClient.post(`/gallery/works/${workId}/collect/`);
    return { success: true, data: response.data };
  } catch (error) {
    return handleApiError(error as CustomAxiosError);
  }
};

export const uncollectGalleryWork = async (workId: string): Promise<ApiResponse<OperationResponse>> => {
  try {
    const response = await apiClient.delete(`/gallery/works/${workId}/collect/`);
    return { success: true, data: response.data };
  } catch (error) {
    return handleApiError(error as CustomAxiosError);
  }
};

export const downloadGalleryWork = async (workId: string, confirmDeduction: boolean = false): Promise<ApiResponse<OperationResponse>> => {
  try {
    const response = await apiClient.post(`/gallery/works/${workId}/`, { confirmDeduction });
    return { success: true, data: response.data };
  } catch (error) {
    return handleApiError(error as CustomAxiosError);
  }
};

export const getCommunities = async (): Promise<ApiResponse<Community[]>> => {
  try {
    const response = await apiClient.get<Community[]>('/communities/');
    return { success: true, data: response.data };
  } catch (error) {
    return handleApiError(error as CustomAxiosError);
  }
};

export const getCommunityDetail = async (communityId: string): Promise<ApiResponse<Community>> => {
  try {
    const response = await apiClient.get<Community>(`/communities/${communityId}/`);
    return { success: true, data: response.data };
  } catch (error) {
    return handleApiError(error as CustomAxiosError);
  }
};

export const getPostsForCommunity = async (communityId: string): Promise<ApiResponse<CommunityPostListItem[]>> => {
  try {
    const response = await apiClient.get<CommunityPostListItem[]>(`/communities/${communityId}/posts/`);
    return { success: true, data: response.data };
  } catch (error) {
    return handleApiError(error as CustomAxiosError);
  }
};

export const getCommunityPostDetail = async (communityId: string, postId: string): Promise<ApiResponse<CommunityPost>> => {
  try {
    const response = await apiClient.get<CommunityPost>(`/communities/${communityId}/posts/${postId}/`);
    return { success: true, data: response.data };
  } catch (error) {
    return handleApiError(error as CustomAxiosError);
  }
};

export const createCommunityPost = async (communityId: string, postData: { title: string; content: string; rewardPoints?: number }): Promise<ApiResponse<CommunityPost>> => {
  try {
    const response = await apiClient.post<CommunityPost>(`/communities/${communityId}/posts/`, postData);
    return { success: true, data: response.data };
  } catch (error) {
    return handleApiError(error as CustomAxiosError);
  }
};

export const createCommunityReply = async (postId: string, replyData: { content: string }): Promise<ApiResponse<CommunityReply>> => {
  try {
    const response = await apiClient.post<CommunityReply>(`/posts/${postId}/replies/`, replyData);
    return { success: true, data: response.data };
  } catch (error) {
    return handleApiError(error as CustomAxiosError);
  }
};

export const likeCommunityPost = async (postId: string): Promise<ApiResponse<OperationResponse>> => {
  try {
    const response = await apiClient.post(`/posts/${postId}/like/`);
    return { success: true, data: response.data };
  } catch (error) {
    return handleApiError(error as CustomAxiosError);
  }
};

export const uploadEditorImage = async (file: File): Promise<ApiResponse<{ imageUrl: string }>> => {
  try {
    const formData = new FormData();
    formData.append('image', file);
    
    const response = await apiClient.post<{ imageUrl: string }>('/uploads/editor-image/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return { success: true, data: response.data };
  } catch (error) {
    return handleApiError(error as CustomAxiosError);
  }
};
export const getMessageThreads = async (): Promise<ApiResponse<MessageThread[]>> => {
  try {
    const response = await apiClient.get<MessageThread[]>('/my/messages/');
    return { success: true, data: response.data };
  } catch (error) {
    return handleApiError(error as CustomAxiosError);
  }
};

export const getMessageThreadDetail = async (threadId: string): Promise<ApiResponse<MessageThreadDetail>> => {
  try {
    const response = await apiClient.get<MessageThreadDetail>(`/my/messages/${threadId}/`);
    return { success: true, data: response.data };
  } catch (error) {
    return handleApiError(error as CustomAxiosError);
  }
};

export const createMessageThread = async (data: { subject: string; content: string; recipient_id: number }): Promise<ApiResponse<OperationResponse>> => {
  try {
    const response = await apiClient.post('/my/messages/', data);
    return { success: true, data: response.data };
  } catch (error) {
    return handleApiError(error as CustomAxiosError);
  }
};

export const deleteMessageThread = async (threadId: string): Promise<ApiResponse<OperationResponse>> => {
  try {
    const response = await apiClient.delete(`/my/messages/${threadId}/`);
    return { success: true, data: response.data };
  } catch (error) {
    return handleApiError(error as CustomAxiosError);
  }
};

export const searchUsers = async (query: string): Promise<ApiResponse<Author[]>> => {
  try {
    const response = await apiClient.get<Author[]>(`/users/search/?q=${query}`);
    return { success: true, data: response.data };
  } catch (error) {
    return handleApiError(error as CustomAxiosError);
  }
};
export const getMyCollections = async (): Promise<ApiResponse<MyCollections>> => {
  try {
    const response = await apiClient.get<MyCollections>('/my/collections/');
    return { success: true, data: response.data };
  } catch (error) {
    return handleApiError(error as CustomAxiosError);
  }
};

export const getMySupported = async (): Promise<ApiResponse<MySupported>> => {
  try {
    const response = await apiClient.get<MySupported>('/my/supported/');
    return { success: true, data: response.data };
  } catch (error) {
    return handleApiError(error as CustomAxiosError);
  }
};

export const getMyCreations = async (): Promise<ApiResponse<MyCreations>> => {
  try {
    const response = await apiClient.get<MyCreations>('/my/creations/');
    return { success: true, data: response.data };
  } catch (error) {
    return handleApiError(error as CustomAxiosError);
  }
};

export const getMyParticipations = async (): Promise<ApiResponse<MyParticipations>> => {
  try {
    const response = await apiClient.get<MyParticipations>('/my/participations/');
    return { success: true, data: response.data };
  } catch (error) {
    return handleApiError(error as CustomAxiosError);
  }
};

export const getMyProfile = async (): Promise<ApiResponse<User>> => {
  try {
    const response = await apiClient.get<User>('/my/profile/');
    return { success: true, data: response.data };
  } catch (error) {
    return handleApiError(error as CustomAxiosError);
  }
};

export const updateMyProfile = async (payload: UserProfileUpdatePayload): Promise<ApiResponse<User>> => {
  try {
    const response = await apiClient.post<User>('/auth/profile', payload);
    return { success: true, data: response.data };
  } catch (error) {
    return handleApiError(error as CustomAxiosError);
  }
};

export const createCourse = async (courseData: FormData): Promise<ApiResponse<OperationResponse>> => {
  try {
    const response = await apiClient.post('/creator/courses/', courseData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return { success: true, data: response.data };
  } catch (error) {
    return handleApiError(error as CustomAxiosError);
  }
};

export const createGalleryItem = async (itemData: FormData): Promise<ApiResponse<OperationResponse>> => {
  try {
    const response = await apiClient.post('/creator/gallery/', itemData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return { success: true, data: response.data };
  } catch (error) {
    return handleApiError(error as CustomAxiosError);
  }
};

export const createCommunity = async (communityData: FormData): Promise<ApiResponse<OperationResponse>> => {
  try {
    const response = await apiClient.post('/creator/communities/', communityData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return { success: true, data: response.data };
  } catch (error) {
    return handleApiError(error as CustomAxiosError);
  }
};
export const updateCourse = async (courseId: string, courseData: FormData): Promise<ApiResponse<OperationResponse>> => {
  try {
    const response = await apiClient.put(`/creator/courses/${courseId}/`, courseData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return { success: true, data: response.data };
  } catch (error) {
    return handleApiError(error as CustomAxiosError);
  }
};

export const updateGalleryItem = async (itemId: string, itemData: FormData): Promise<ApiResponse<OperationResponse>> => {
  try {
    const response = await apiClient.put(`/creator/gallery/${itemId}/`, itemData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return { success: true, data: response.data };
  } catch (error) {
    return handleApiError(error as CustomAxiosError);
  }
};
export const updateCommunity = async (communityId: string, communityData: FormData): Promise<ApiResponse<OperationResponse>> => {
  try {
    const response = await apiClient.put(`/creator/communities/${communityId}/`, communityData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return { success: true, data: response.data };
  } catch (error) {
    return handleApiError(error as CustomAxiosError);
  }
};