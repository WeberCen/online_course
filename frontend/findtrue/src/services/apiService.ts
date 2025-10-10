// frontend/findtrue/src/services/apiService.ts

import axios from 'axios';
import type { Course, CourseDetail, ExerciseAnswer, Progress, SubmissionResult,
 GalleryItem, GalleryItemDetail, CommunityPost,CommunityReply,CommunityPostListItem, Community} from '../types'; 

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
      }
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// --- API 函数 ---

export const getCourses = () => {
  // 我们可以告诉 axios 期望返回的数据类型
  return apiClient.get<Course[]>('/courses/');
};

export const getCourseDetail = (id: string) => {
  return apiClient.get<CourseDetail>(`/courses/${id}/`);
};

export const subscribeCourse = (courseId: string) => {
  return apiClient.post(`/courses/${courseId}/subscribe/`);
};

export const unsubscribeCourse = (courseId: string) => {
  return apiClient.delete(`/courses/${courseId}/subscribe/`);
};

export const collectCourse = (courseId: string) => {
  return apiClient.post(`/courses/${courseId}/collect/`);
};

export const uncollectCourse = (courseId: string) => {
  return apiClient.delete(`/courses/${courseId}/collect/`);
};

export const getCourseProgress = (courseId: string) => {
  return apiClient.get<Progress>(`/courses/${courseId}/progress/`);
};

export const submitChapterExercises = (courseId: string, chapterId: string, answers: ExerciseAnswer[]) => {
  return apiClient.post<SubmissionResult>(`/courses/${courseId}/chapters/${chapterId}/submit/`, { answers });
};


export const getGalleryWorks = () => {
  return apiClient.get<GalleryItem[]>('/gallery/works/');
};

export const getGalleryWorkDetail = (id: string) => {
  return apiClient.get<GalleryItemDetail>(`/gallery/works/${id}/`);
};

export const collectGalleryWork = (workId: string) => {
  return apiClient.post(`/gallery/works/${workId}/collect/`);
};

export const uncollectGalleryWork = (workId: string) => {
  return apiClient.delete(`/gallery/works/${workId}/collect/`);
};

export const downloadGalleryWork = (workId: string, confirmDeduction: boolean = false) => {
  return apiClient.post(`/gallery/works/${workId}/`, { confirmDeduction });
};

export const getCommunities = () => {
  return apiClient.get<Community[]>('/communities/');
};

export const getPostsForCommunity = (communityId: string) => {
  return apiClient.get<CommunityPostListItem[]>(`/communities/${communityId}/posts/`);
};

export const getCommunityPostDetail = (communityId: string, postId: string) => {
  return apiClient.get<CommunityPost>(`/communities/${communityId}/posts/${postId}/`);
};

export const createCommunityPost = (communityId: string, postData: { title: string; content: string; rewardPoints?: number }) => {
  return apiClient.post<CommunityPost>(`/communities/${communityId}/posts/`, postData);
};

export const createCommunityReply = (postId: string, replyData: { content: string }) => {
  return apiClient.post<CommunityReply>(`/posts/${postId}/replies/`, replyData);
};

export const likeCommunityPost = (postId: string) => {
  return apiClient.post(`/posts/${postId}/like/`);
};

export const uploadEditorImage = (file: File) => {
  const formData = new FormData();
  formData.append('image', file);
  
  return apiClient.post<{ imageUrl: string }>('/uploads/editor-image/', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
};
