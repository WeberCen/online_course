export interface Author {
  id: number;
  username: string;
  nickname?: string;
  avatarUrl?: string | null;
}
// ===============================================
// =======          课程模块类型          =======
// ===============================================
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
  coverImage?: string | File | null;
  author: Author;
  tags: string[];
  chapterCount: number;
  status: string;
  pricePoints: number;
  is_vip_free: boolean;
}

export interface CourseDetail extends Course {
  chapters: Chapter[];
  is_subscribed: boolean;
  is_collected: boolean;
}

export interface ExerciseAnswer {
   exerciseId:number;
   userAnswer:string | string[];
}

export interface Exercise {
  id: number;
  prompt: string;
  type: 'multiple-choice' | 'fill-in-the-blank'; 
  options?: string[]; 
}

export interface Progress {
  completedChapters: number;
  totalChapters: number;
  isCompleted: boolean;
  nextChapterId: number | null;
}

export interface SubmissionResult {
  score: number;
  isPassed: boolean;
  newProgress: Progress;
}
// ===============================================
// =======          画廊模块类型          =======
// ===============================================
export interface GalleryItem {
  id: number;
  title: string;
  description: string;
  coverImage?: string | File | null;
  author: Author;
  tags: string[];
  requiredPoints: number;
  rating: number;
  version: string;
  is_vip_free: boolean;
}

export interface GalleryItemDetail extends GalleryItem {
  is_collected: boolean;
  is_downloaded: boolean;
  workFile: string;
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
  coverImage?: string | File | null;
  tags: string[];
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
  is_best_answer: boolean;
}

export interface CommunityPost {
  id: number;
  title: string;
  content: string;
  author: Author;
  status: string;
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
  content: string;
  sent_at: string;
}


export interface MessageThread {
  id: number;
  subject: string;
  thread_type: string;
  last_message: Message | null;
  created_at: string;
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
export interface User {
  id: number;
  username: string;
  email: string;
  phone: string;
  nickname: string | null;
  avatarUrl: string | null;
  role: string;
  currentPoints: number;
  ageGroup: string | null;
  gender: string | null;
  interests: string[];
  accountStatus: string;
  pointsStatus: string;
}
export type UserProfileUpdatePayload = Partial<Pick<User, 'nickname' | 'ageGroup' | 'gender' | 'interests'>>;
