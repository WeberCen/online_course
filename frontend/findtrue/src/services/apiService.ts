// frontend/findtrue/src/services/apiService.ts

import axios from 'axios';
import type {
  // 基础响应类型
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
  SubmissionReport,

  // 画廊模块类型
  GalleryItem,
  GalleryItemDetail,
  DownloadLinkPayload,
  
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
  AxiosErrorResponse
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

// --- API 函数 ---

// 认证相关API
export const authService = {
  // 用户注册
  register: async (data: RegisterData): Promise<OperationResponse> => {
    const response = await apiClient.post('/auth/register/', data);
    return response.data;
  },
  
  // 用户登录 - 支持用户名、邮箱或手机号
  login: async (data: LoginData): Promise<LoginResponse> => {
    const response = await apiClient.post<LoginResponse>('/auth/login/', data);
    
    // 保存token到localStorage
    if (response.data && response.data.tokens) {
      
      localStorage.setItem('accessToken', response.data.tokens.access);
      localStorage.setItem('refreshToken', response.data.tokens.refresh);
      localStorage.setItem('userData', JSON.stringify(response.data.user));
      
      // 更新 axios 預設 headers，使用 access Token
      apiClient.defaults.headers.Authorization = `Bearer ${response.data.tokens.access}`;
    }
    
    return response.data;
  },
  
  // 密码重置请求
  resetPasswordRequest: async (data: PasswordResetRequest): Promise<OperationResponse> => {
    const response = await apiClient.post('/auth/forgot-password/send-code/', data);
    return response.data;
  },
  
  // 密码重置确认
  resetPasswordConfirm: async (data: PasswordResetConfirm): Promise<OperationResponse> => {
    const response = await apiClient.post('/auth/reset-password/', data);
    return response.data;
  },
  
  // 退出登录
  logout: (): void => {
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
    localStorage.removeItem('userData');
    delete apiClient.defaults.headers.Authorization;
  },
  
  // 更新用户资料
  updateProfile: async (data: UserProfileUpdatePayload): Promise<User> => {
    const response = await apiClient.put<User>('/auth/profile/', data);
    // 更新本地存储的用户数据
    if (response.data) {
      localStorage.setItem('userData', JSON.stringify(response.data));
    }
    return response.data;
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

export const getCourses = async (): Promise<Course[]> => {
  const response = await apiClient.get<Course[]>('/courses/');
  return response.data;
};

export const getCourseDetail = async (id: string): Promise<CourseDetail> => {
  const response = await apiClient.get<CourseDetail>(`/courses/${id}/`);
  return response.data;
};

export const subscribeCourse = async (courseId: string): Promise<OperationResponse> => {
  const response = await apiClient.post(`/courses/${courseId}/subscribe/`);
  return response.data;
};

export const unsubscribeCourse = async (courseId: string): Promise<OperationResponse> => {
  const response = await apiClient.delete(`/courses/${courseId}/unsubscribe/`);
  return response.data;
};

export const collectCourse = async (courseId: string): Promise<OperationResponse> => {
  const response = await apiClient.post(`/courses/${courseId}/collect/`);
  return response.data;
};

export const uncollectCourse = async (courseId: string): Promise<OperationResponse> => {
  const response = await apiClient.delete(`/courses/${courseId}/uncollect/`);
  return response.data;
};

export const getCourseProgress = async (courseId: string): Promise<Progress> => {
  const response = await apiClient.get<Progress>(`/courses/${courseId}/progress/`);
  return response.data;
};

export const submitChapterExercises = async (chapterId: string, answers: ExerciseAnswer[]): Promise<SubmissionReport> => {
  const response = await apiClient.post<SubmissionReport>(`/chapters/${chapterId}/submit/`, { answers });
  return response.data;
};

export const getGalleryWorks = async (): Promise<GalleryItem[]> => {
  const response = await apiClient.get<GalleryItem[]>('/gallery/items/');
  return response.data;
};

export const getGalleryWorkDetail = async (id: string): Promise<GalleryItemDetail> => {
  const response = await apiClient.get<GalleryItemDetail>(`/gallery/items/${id}/`);
  return response.data;
};

export const collectGalleryWork = async (workId: string): Promise<OperationResponse> => {
  const response = await apiClient.post(`/gallery/items/${workId}/collect/`);
  return response.data;
};

export const uncollectGalleryWork = async (workId: string): Promise<OperationResponse> => {
  const response = await apiClient.delete(`/gallery/items/${workId}/uncollect/`);
  return response.data;
};

export const downloadGalleryWork = async (workId: string, isConfirmed: boolean): Promise<DownloadLinkPayload> => {
  const response = await apiClient.post<DownloadLinkPayload>(`/gallery/items/${workId}/download/`, { confirm_cost: isConfirmed });
  return response.data;
};

export const getCommunities = async (): Promise<Community[]> => {
  const response = await apiClient.get<Community[]>('/communities/');
  return response.data;
};

export const getCommunityDetail = async (communityId: string): Promise<Community> => {
  const response = await apiClient.get<Community>(`/communities/${communityId}/`);
  return response.data;
};

export const getPostsForCommunity = async (communityId: string): Promise<CommunityPostListItem[]> => {
  const response = await apiClient.get<CommunityPostListItem[]>(`/communities/${communityId}/posts/`);
  return response.data;
};

export const getCommunityPostDetail = async (communityId: string, postId: string): Promise<CommunityPost> => {
  const response = await apiClient.get<CommunityPost>(`/communities/${communityId}/posts/${postId}/`);
  return response.data;
};

export const createCommunityPost = async (communityId: string, postData: { title: string; content: string; rewardPoints?: number }): Promise<CommunityPost> => {
  const response = await apiClient.post<CommunityPost>(`/communities/${communityId}/posts/`, postData);
  return response.data;
};

export const createCommunityReply = async (communityId: string,postId: string, replyData: { content: string }
): Promise<CommunityReply> => {
  const response = await apiClient.post<CommunityReply>(`/communities/${communityId}/posts/${postId}/replies/`, replyData);
  return response.data;
};

export const likeCommunityPost = async (communityId: string,postId: string): Promise<OperationResponse> => {
  const response = await apiClient.post(`/communities/${communityId}/posts/${postId}/like/`);
  return response.data;
};

export const uploadEditorImage = async (file: File): Promise<{ imageUrl: string }> => {
  const formData = new FormData();
  formData.append('image', file);
  
  const response = await apiClient.post<{ imageUrl: string }>('/uploads/editor-image/', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export const getMessageThreads = async (): Promise<MessageThread[]> => {
  const response = await apiClient.get<MessageThread[]>('/my/messages/');
  return response.data;
};

export const getMessageThreadDetail = async (threadId: string): Promise<MessageThreadDetail> => {
  const response = await apiClient.get<MessageThreadDetail>(`/my/messages/${threadId}/`);
  return response.data;
};

export const createMessageThread = async (data: { subject: string; content: string; recipient_id: number }): Promise<OperationResponse> => {
  const response = await apiClient.post('/my/messages/', data);
  return response.data;
};

export const deleteMessageThread = async (threadId: string): Promise<OperationResponse> => {
  const response = await apiClient.delete(`/my/messages/${threadId}/`);
  return response.data;
};

export const searchUsers = async (query: string): Promise<Author[]> => {
  const response = await apiClient.get<Author[]>(`/users/search/?q=${query}`);
  return response.data;
};

export const getMyCollections = async (): Promise<MyCollections> => {
  const response = await apiClient.get<MyCollections>('/my/collections/');
  return response.data;
};

export const getMySupported = async (): Promise<MySupported> => {
  const response = await apiClient.get<MySupported>('/my/supported/');
  return response.data;
};

export const getMyCreations = async (): Promise<MyCreations> => {
  const response = await apiClient.get<MyCreations>('/my/creations/');
  return response.data;
};

export const getMyParticipations = async (): Promise<MyParticipations> => {
  const response = await apiClient.get<MyParticipations>('/my/participations/');
  return response.data;
};

export const getMyProfile = async (): Promise<User> => {
  const response = await apiClient.get<User>('/my/profile/');
  return response.data;
};

export const updateMyProfile = async (payload: UserProfileUpdatePayload): Promise<User> => {
  const response = await apiClient.post<User>('/auth/profile', payload);
  return response.data;
};


// -----------------------------------------------------------------
// 课程 (Course)
// -----------------------------------------------------------------
/** GET /creator/courses/ - 获取创作者的所有课程 (仪表盘) */
export const getMyCourses = async (): Promise<Course[]> => {
  const response = await apiClient.get<Course[]>('/creator/courses/');
  return response.data;
};

/** POST /creator/courses/new/ - 创建新课程 (你已提供) */
export const createMyCourse = async (courseData: FormData): Promise<OperationResponse> => {
  const response = await apiClient.post('/creator/courses/new/', courseData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

/** GET /creator/courses/{pk}/ - 获取单个课程详情 (用于编辑页) */
export const getMyCourseDetail = async (courseId: string): Promise<Course> => {
  const response = await apiClient.get<Course>(`/creator/courses/${courseId}/`);
  return response.data;
};

/** PUT /creator/courses/{pk}/ - 更新课程 */
export const updateMyCourse = async (courseId: string, courseData: FormData): Promise<OperationResponse> => {
  const response = await apiClient.put(`/creator/courses/${courseId}/`, courseData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

/** POST /creator/courses/{pk}/submit/ - 提交课程审核 (关键状态流) */
export const submitMyCourseForReview = async (courseId: string): Promise<{ status: string; message: string }> => {
  const response = await apiClient.post(`/creator/courses/${courseId}/submit/`);
  return response.data;
};

// -----------------------------------------------------------------
// 章节 (Chapter)
// -----------------------------------------------------------------

/** POST /creator/courses/{course_pk}/chapters/ - 为课程创建新章节 */
export const createMyChapter = async (courseId: string, data: { title: string; videoUrl?: string }): Promise<Chapter> => {
  const response = await apiClient.post<Chapter>(`/creator/courses/${courseId}/chapters/`, data);
  return response.data;
};

/** PUT /creator/chapters/{pk}/ - 更新章节 */
export const updateMyChapter = async (chapterId: string, data: { title: string; videoUrl?: string }): Promise<Chapter> => {
  const response = await apiClient.put<Chapter>(`/creator/chapters/${chapterId}/`, data);
  return response.data;
};

/** DELETE /creator/chapters/{pk}/ - 删除章节 */
export const deleteMyChapter = async (chapterId: string): Promise<void> => {
  await apiClient.delete(`/creator/chapters/${chapterId}/`);
};

/** PUT /creator/courses/{course_pk}/chapters/order/ - 批量更新章节排序 */
export const updateMyChapterOrder = async (courseId: string, chapterIds: string[]): Promise<{ status: string }> => {
  const response = await apiClient.put(`/creator/courses/${courseId}/chapters/order/`, { chapter_ids: chapterIds });
  return response.data;
};

// -----------------------------------------------------------------
// 练习题 (Exercise)
// -----------------------------------------------------------------

/** POST /creator/chapters/{chapter_pk}/exercises/ - 为章节创建新练习 */
export const createMyExercise = async (chapterId: string, exerciseData: FormData): Promise<Exercise> => {
  const response = await apiClient.post<Exercise>(`/creator/chapters/${chapterId}/exercises/`, exerciseData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

/** GET /creator/exercises/{pk}/ - 获取练习详情 (用于编辑) */
export const getMyExerciseDetail = async (exerciseId: string): Promise<Exercise> => {
  const response = await apiClient.get<Exercise>(`/creator/exercises/${exerciseId}/`);
  return response.data;
};

/** PUT /creator/exercises/{pk}/ - 更新练习 */
export const updateMyExercise = async (exerciseId: string, exerciseData: FormData): Promise<Exercise> => {
  const response = await apiClient.put<Exercise>(`/creator/exercises/${exerciseId}/`, exerciseData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

/** DELETE /creator/exercises/{pk}/ - 删除练习 */
export const deleteMyExercise = async (exerciseId: string): Promise<void> => {
  await apiClient.delete(`/creator/exercises/${exerciseId}/`);
};

// -----------------------------------------------------------------
// 画廊作品 (Gallery Item) - 仅对创作者可见
// -----------------------------------------------------------------

/** GET /creator/gallery/ - 获取创作者的所有作品 (作品列表) */
export const getMyGalleryItems = async (): Promise<GalleryItem[]> => {
  const response = await apiClient.get<GalleryItem[]>('/creator/gallery/');
  return response.data;
};

/** POST /creator/gallery/ - 创建新作品 */
export const createMyGalleryItem = async (itemData: FormData): Promise<OperationResponse> => {
  const response = await apiClient.post('/creator/gallery/', itemData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

/** GET /creator/gallery/{pk}/ - 获取单个作品详情 (用于编辑页) */
export const getMyGalleryItemDetail = async (itemId: string): Promise<GalleryItem> => {
  const response = await apiClient.get<GalleryItem>(`/creator/gallery/${itemId}/`);
  return response.data;
};

/** PUT /creator/gallery/{pk}/ - 更新作品 (保存为草稿) */
export const updateMyGalleryItem = async (itemId: string, itemData: FormData): Promise<OperationResponse> => {
  const response = await apiClient.put(`/creator/gallery/${itemId}/`, itemData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

/** POST /creator/gallery/{pk}/submit/ - 提交作品审核 */
export const submitMyGalleryItemForReview = async (itemId: string): Promise<{ status: string; message: string }> => {
  // 假设后端的 URL 与 Course 提交一致
  const response = await apiClient.post(`/creator/gallery/${itemId}/submit/`);
  return response.data;
};

// -----------------------------------------------------------------
// 社群 (Community) - 仅对创作者可见
// -----------------------------------------------------------------

/** GET /creator/communities/ - 获取创作者的所有社群 (社群列表) */
export const getMyCommunities = async (): Promise<Community[]> => {
  const response = await apiClient.get<Community[]>('/creator/communities/');
  return response.data;
};

/** POST /creator/communities/ - 创建新社群 */
export const createMyCommunity = async (communityData: FormData): Promise<OperationResponse> => {
  const response = await apiClient.post('/creator/communities/', communityData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

/** GET /creator/communities/{pk}/ - 获取单个社群详情 (用于编辑页) */
export const getMyCommunityDetail = async (communityId: string): Promise<Community> => {
  const response = await apiClient.get<Community>(`/creator/communities/${communityId}/`);
  return response.data;
};

/** PUT /creator/communities/{pk}/ - 更新社群 */
export const updateMyCommunity = async (communityId: string, communityData: FormData): Promise<OperationResponse> => {
  const response = await apiClient.put(`/creator/communities/${communityId}/`, communityData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};