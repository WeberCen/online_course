export interface Author {
  id: number;
  username: string;
  nickname?: string;
  avatarUrl?: string | null;
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
  coverImage?: string | null;
  author: Author;
  tags: string[];
  chapterCount: number;
  status: string;
  pricePoints: number;
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
}

export interface GalleryItemDetail extends GalleryItem {
  is_collected: boolean;
  is_downloaded: boolean;
  workFile: string;
}



export interface Community {
  id: number;
  name: string;
  description: string;
  founder: Author;
  post_count: number;
  coverImage?: string | null;
  tags: string[];
}

export interface CommunityPostListItem {
  id: number;
  title: string;
  author: Author;
  rewardPoints: number;
  created_at: string;
  reply_count: number;
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
export interface Message {
  id: number;
  sender: Author;
  content: string;
  sent_at: string;
}

// 用于会话列表页的摘要信息
export interface MessageThread {
  id: number;
  subject: string;
  thread_type: string;
  last_message: Message | null;
  created_at: string;
}

// 用于会话详情页的完整信息
export interface MessageThreadDetail {
  id: number;
  subject: string;
  thread_type: string;
  participants: Author[];
  created_at: string;
  messages: Message[];
}