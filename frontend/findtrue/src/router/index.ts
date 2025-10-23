// frontend/findtrue/src/router/index.js

import { createRouter, createWebHistory } from 'vue-router'
import CoursesView from '../views/CoursesView.vue'; 
import CourseDetailView from '../views/CoursesDetailView.vue'; 
import GalleryView from '../views/GalleryView.vue';
import GalleryDetailView from '../views/GalleryDetailView.vue';
import CommunitiesView from '../views/CommunitiesView.vue';
import CommunityDetailView from '@/views/CommunityDetailView.vue';
import CommunityPostsView from '@/views/CommunityPostsView.vue';
import CreatePostView from '../views/CreatePostView.vue'; 
import MessageInboxView from '../views/MessageInboxView.vue';
import MessageThreadDetailView from '../views/MessageThreadDetailView.vue';
import CreateMessageThreadView from '../views/CreateMessageThreadView.vue';
import PersonalCenterLayout from '../views/PersonalCenterLayout.vue';
import MyCollectionsView from '../views/MyCollectionsView.vue';
import MySupportedView from '../views/MySupportedView.vue';
import MyCreationsView from '../views/MyCreationsView.vue';
import MyParticipationsView from '../views/MyParticipationsView.vue'; 
import MyProfileView from '../views/MyProfileView.vue';
import MyPointsView from '../views/MyPointsView.vue';
import CreateCourseView from '../views/CreateCourseView.vue';
import CreateGalleryItemView from '../views/CreateGalleryItemView.vue';
import CreateCommunityView from '../views/CreateCommunityView.vue';
import LoginView from '@/views/LoginView.vue';
import RegisterView from '@/views/RegisterView.vue';
import ForgotPasswordView from '@/views/ForgotPasswordView.vue';
import { useUserStore } from '../stores/userStore';


const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/courses' },
    // 认证相关路由
    { path: '/login', name: 'Login', component: LoginView, meta: { requiresAuth: false } },
    { path: '/register', name: 'Register', component: RegisterView, meta: { requiresAuth: false } },
    { path: '/forgot-password', name: 'ForgotPassword', component: ForgotPasswordView, meta: { requiresAuth: false } },
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

      // --- 修复 1：保护所有“个人中心”子路由 ---
      meta: { requiresAuth: true }, 

      children: [
        { path: '', redirect: { name: 'my-collections' } }, 
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
          component: MyCreationsView,
          meta: { requiresArtist: true } 
        },
        { 
          path: 'creations/new-course', 
          name: 'create-course', 
          component: CreateCourseView, 
          meta: { requiresArtist: true } 
        },
        { 
          path: 'creations/new-gallery-item', 
          name: 'create-gallery-item', 
          component: CreateGalleryItemView, 
          meta: { requiresArtist: true } 
        },
        { 
          path: 'creations/new-community', 
          name: 'create-community', 
          component: CreateCommunityView, 
          meta: { requiresArtist: true } 
        },
        { 
          path: 'creations/courses/:id/edit', 
          name: 'edit-course', 
          component: CreateCourseView, 
          meta: { requiresArtist: true } 
        },
        { 
          path: 'creations/gallery/:id/edit', 
          name: 'edit-gallery-item', 
          component: CreateGalleryItemView, 
          meta: { requiresArtist: true } 
        },
        { 
          path: 'creations/communities/:id/edit', 
          name: 'edit-community', 
          component: CreateCommunityView, 
          meta: { requiresArtist: true } 
        },
        {
          path: 'participations',
          name: 'my-participations',
          component: MyParticipationsView
        },
        {
          path: 'points',
          name: 'my-points',
          component: MyPointsView
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

router.beforeEach((to, from, next) => {
  const userStore = useUserStore();
  
  const requiresAuth = to.matched.some(record => record.meta.requiresAuth);
  const requiresArtist = to.matched.some(record => record.meta.requiresArtist);

  if ((requiresAuth || requiresArtist) && !userStore.isLoggedIn) {
    // 1. 目的地需要登录，但未登录 -> 去登录
    next({ name: 'Login', query: { redirect: to.fullPath } });
  } else if (requiresArtist && !['artist', 'admin'].includes(userStore.userInfo?.role as string)) { 

    alert("您需要创作者或管理员权限才能访问此页面。");
    next({ name: 'my-profile' }); // 重定向到个人资料页

  } else {
    next(); 
  }
});

export default router;