// frontend/findtrue/src/types.ts


// ===============================================
// =======          核心基础类型          =======
// ===============================================


export interface Author {
  id: number;
  username: string;
  nickname?: string;
  avatarUrl?: string | null;
}
export interface User {
  id: number;
  username: string;
  email: string;
  phone: string;
  nickname: string | null;
  avatarUrl: string | null;
  role: 'student' | 'artist' | 'admin';
  currentPoints: number;
  ageGroup: string | null;
  gender: string | null;
  interests: string[];
  accountStatus: 'active' | 'suspended' | 'frozen';
  pointsStatus: 'active' | 'frozen';
  bio: string | null;
  vip_expiration_date: string | null; 
  last_activity_at: string | null;
  unread_message_count: number;
  is_beta_tester: boolean;
}

export type UserProfileUpdatePayload = Partial<Pick<User, 'nickname' | 'ageGroup' | 'gender' | 'interests' | 'bio'>>;


// ===============================================
// =======          认证模块类型          =======
// ===============================================
export interface AuthTokens {
  access: string;
  refresh: string;
}

export interface LoginResponse {
  tokens: AuthTokens;
  user: User;
} 

export interface RegisterData {
  username: string;
  email: string;
  phone: string;
  password: string;
  password2: string;
  nickname?: string;
  avatarUrl?: string;
  bio?: string;
  gender?: 'male' | 'female' | 'other' | null; 
  ageGroup?: string | null;
  interests?: string[];
}

export interface LoginData {
  identifier: string;
  password: string;
}

export type PasswordResetRequest = 
  | { email: string; phone?: never; } 
  | { email?: never; phone: string; };
interface PasswordResetConfirmBase {
  code: string;
  password: string;
  password2: string;
}
export type PasswordResetConfirm = PasswordResetConfirmBase & (
  | { email: string; phone?: never; }
  | { email?: never; phone: string; }
);

// ===============================================
// =======          课程模块类型          =======
// ===============================================
export interface ExerciseOption {
  id: number;
  text: string;
}

export interface UserSubmission {
  user_answer: string | string[]; // 用戶當時提交的答案
  is_correct: boolean;           // 批改結果：是否正確
  correct_answer: string | string[]; // 官方正確答案
  analysis: string;              // 答案解析
}

export interface Exercise {
  id: number;
  prompt: string;
  type: 'multiple-choice' | 'fill-in-the-blank';
  options: ExerciseOption[];
  explanation: string | null; 
  image_upload: string | null; 
  image_url: string | null; 
  user_submission: UserSubmission | null;
}

export interface SubmissionSummary {
  correct_count: number;
  incorrect_count: number;
  incorrect_exercises: { id: number; prompt: string }[];
}

export interface SubmissionDetail {
  is_correct: boolean;
  correct_answer: string | string[];
  analysis: string;
}

export interface SubmissionReport {
  summary: SubmissionSummary;
  details: Record<string, SubmissionDetail>; 
}


export interface ExerciseAnswer {
  exerciseId: number;
  userAnswer: string | string[];
}

export interface Chapter {
  id: number;
  title: string;
  order: number;
  videoUrl?: string | null;
  exercises?: Exercise[]; 
}

export interface Course {
  id: number;
  title: string;
  description: string;
  coverImage: string | null;
  author: Author;
  tags: string[];
  chapterCount: number;
  status: 'draft' | 'pending_review' | 'published' | 'rejected' | 'archived';
  pricePoints: number;
  is_vip_free: boolean; 
  chapters?: Chapter[];
}

export interface CourseDetail extends Course {
  chapters: Chapter[];
  is_subscribed: boolean;
  is_collected: boolean;
}

export interface Progress {
  completed_exercises: number;
  total_exercises: number;
  progress_percentage: number;
  next_chapter_id: number | null; 
}


// ===============================================
// =======          画廊模块类型          =======
// ===============================================
export interface GalleryItem {
  id: number;
  title: string;
  description: string;
  coverImage: string | null;
  author: Author;
  tags: string[];
  requiredPoints: number;
  rating: number;
  version: string;
  is_vip_free: boolean; 
  estimated_download_time: number; 
  status: 'draft' | 'pending_review' | 'published' | 'rejected' | 'archived';
}

export interface GalleryItemDetail extends GalleryItem {
  is_collected: boolean;
  is_downloaded: boolean;
  workFile: string;
}

export interface DownloadLinkPayload {
  downloadUrl: string;
}


// ===============================================
// =======          社群模块类型          =======
// ===============================================

export interface Community {
  id: number;
  name: string;
  description: string;
  founder: Author;
  post_count: number;
  coverImage?: string | null;
  tags: string[];
  status: 'draft' | 'pending_review' | 'published' | 'rejected' | 'archived'; // 新增
}


export interface CommunityPostListItem {
  id: number;
  title: string;
  author: Author;
  rewardPoints: number;
  created_at: string;
  reply_count: number;
  community: number;
}

export interface CommunityReply {
  id: number;
  author: Author;
  content: string;
  created_at: string;
  likes: number[]; 
}

export interface CommunityPost {
  id: number;
  title: string;
  content: string;
  author: Author;
  status: 'pending_review' | 'published' | 'closed' | 'rejected';
  rewardPoints: number;
  created_at: string;
  updated_at: string;
  best_answer: number | null;
  replies: CommunityReply[];
  likes: number[];
}
// ===============================================
// =======         站内信模块类型         =======
// ===============================================
export interface Message {
  id: number;
  sender: Author;
  recipient: Author; // 新增
  content: string;
  sent_at: string;
  is_recipient_read: boolean; // 新增
}


export interface MessageThread {
  id: number;
  subject: string;
  thread_type: 'notification' | 'conversation';
  last_message: Message | null;
  created_at: string;
  last_message_at: string | null; // 新增
}



export interface MessageThreadDetail {
  id: number;
  subject: string;
  thread_type: string;
  participants: Author[];
  created_at: string;
  messages: Message[];
}

// ===============================================
// =======         个人中心模块类型         =======
// ===============================================

export interface MyCollections {
  courses: Course[];
  gallery_items: GalleryItem[];
}

export interface MySupported {
  courses: Course[];
  gallery_items: GalleryItem[]; 
}

export interface MyCreations {
  courses: Course[];
  gallery_items: GalleryItem[];
  founded_communities: Community[]; 
}

export interface MyParticipations {
  posts: CommunityPostListItem[];
}

// ===============================================
// =======         VIP 套餐类型         =======
// ===============================================
export interface VipPlan {
    id: number;
    name: string;
    duration_days: number;
    price_points: number;
}

// ===============================================
// =======          操作响应类型          =======
// ===============================================
export interface OperationResponse {
  success: boolean;
  message?: string;
  [key: string]: boolean | string | number | object | undefined;
}

// 定义Axios错误响应的详细类型
export interface AxiosErrorResponse {
  detail?: string;
  error?: string;
  message?: string;
  [key: string]: boolean | string | number | object | undefined;   
}