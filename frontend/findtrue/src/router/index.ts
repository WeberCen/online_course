// frontend/findtrue/src/router/index.js

import { createRouter, createWebHistory } from 'vue-router'
import CoursesView from '../views/CoursesView.vue' 
import CourseDetailView from '../views/CoursesDetailView.vue' 
import GalleryView from '../views/GalleryView.vue'
import GalleryDetailView from '../views/GalleryDetailView.vue'  
import CommunitiesView from '../views/CommunitiesView.vue'
import CommunityDetailView from '@/views/CommunityDetailView.vue'
import CommunityPostsView from '@/views/CommunityPostsView.vue'
import CreatePostView from '../views/CreatePostView.vue' 

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      redirect: '/courses' // 将根路径重定向到课程列表页
    },
    {
      path: '/courses',
      name: 'courses-list',
      component: CoursesView
    },
    {
      path: '/courses/:id', 
      name: 'course-detail',
      component: CourseDetailView
    },
    {
      path: '/gallery',
      name: 'gallery-list',
      component: GalleryView
    },
    {
      path: '/gallery/:id', 
      name: 'gallery-detail',
      component: GalleryDetailView
    },
    {
      path: '/communities', // 社群板块列表
      name: 'communities-list',
      component: CommunitiesView
    },
    {
      path: '/communities/:communityId/posts', // 特定社群下的帖子列表
      name: 'community-posts-list',
      component: CommunityPostsView 
    },
    { 
      path: '/communities/:communityId/posts/new', 
      name: 'create-post', 
      component: CreatePostView 
    }, 
    {
      path: '/communities/:communityId/posts/:postId',
      name: 'community-post-detail',
      component: CommunityDetailView
    }

  ]
})

export default router
