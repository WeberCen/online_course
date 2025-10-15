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
import MessageInboxView from '../views/MessageInboxView.vue';
import MessageThreadDetailView from '../views/MessageThreadDetailView.vue'
import CreateMessageThreadView from '../views/CreateMessageThreadView.vue'
import PersonalCenterLayout from '../views/PersonalCenterLayout.vue';
import MyCollectionsView from '../views/MyCollectionsView.vue';
import MySupportedView from '../views/MySupportedView.vue';
import MyCreationsView from '../views/MyCreationsView.vue';
import MyParticipationsView from '../views/MyParticipationsView.vue'; 
import MyProfileView from '../views/MyProfileView.vue';
import CreateCourseView from '../views/CreateCourseView.vue'
import CreateGalleryItemView from '../views/CreateGalleryItemView.vue'
import CreateCommunityView from '../views/CreateCommunityView.vue'

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
    },
    
    {
      path: '/my',
      component: PersonalCenterLayout,
      children: [
        { path: '', redirect: { name: 'my-collections' } }, // 默认显示我的收藏
        {
          path: 'collections',
          name: 'my-collections',
          component: MyCollectionsView
        },
        {
          path: 'supported',
          name: 'my-supported',
          component: MySupportedView
        },
        {
          path: 'creations',
          name: 'my-creations',
          component: MyCreationsView
        },
        { path: 'creations/new-course', name: 'create-course', component: CreateCourseView },
        { path: 'creations/new-gallery-item', name: 'create-gallery-item', component: CreateGalleryItemView },
        { path: 'creations/new-community', name: 'create-community', component: CreateCommunityView },
        { path: 'creations/courses/:id/edit', name: 'edit-course', component: CreateCourseView },
        { path: 'creations/gallery/:id/edit', name: 'edit-gallery-item', component: CreateGalleryItemView },
        { path: 'creations/communities/:id/edit', name: 'edit-community', component: CreateCommunityView },
        {
          path: 'participations',
          name: 'my-participations',
          component: MyParticipationsView
        },
        {
          path: 'profile',
          name: 'my-profile',
          component: MyProfileView
        },
        {
          path: 'message',
          name: 'message-inbox',
          component: MessageInboxView
        },
        {
          path: '/messages/:threadId',
          name: 'message-thread-detail',
          component: MessageThreadDetailView
        },
        {
          path: '/messages/new',
          name: 'create-message-thread',
          component: CreateMessageThreadView
        },
      ]
    }
  ]
})

export default router
