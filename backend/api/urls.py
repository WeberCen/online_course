# backend/api/urls.py
from django.urls import path,include
from rest_framework_nested import routers
from . import views
from rest_framework.routers import DefaultRouter
from .views import CourseViewSet,ChapterViewSet
from .views import (UserRegisterView,UserSearchView,UserLoginView,UserProfileView,
ChangePhoneInitiateView, ChangePhoneVerifyNewView, ChangePhoneCommitView,
ChangeEmailInitiateView, ChangeEmailVerifyNewView, ChangeEmailCommitView,
CertificationSubmitView,EditorImageView,PasswordResetConfirmView,PasswordResetRequestView,
CourseCreateView,
GalleryItemViewSet,
GalleryItemCreateView,
CommunityCreateView,
MessageThreadListCreateView,MessageThreadRetrieveDestroyView,
MyCollectionsView,MySupportedView,MyCreationsView,MyParticipationsView,
CourseUpdateDetailView,GalleryItemUpdateView,CommunityUpdateView,
ChapterOrderUpdateView,ChapterDetailView,ChapterOrderUpdateView)

router = DefaultRouter()
router.register(r'courses', CourseViewSet, basename='course')
router.register(r'chapters', ChapterViewSet, basename='chapter')
router.register(r'gallery/items', GalleryItemViewSet, basename='gallery-item')
router.register(r'communities', views.CommunityViewSet, basename='community')
communities_router = routers.NestedDefaultRouter(router, r'communities', lookup='community')
communities_router.register(r'posts', views.CommunityPostViewSet, basename='community-post')
posts_router = routers.NestedDefaultRouter(communities_router, r'posts', lookup='post')
posts_router.register(r'replies', views.CommunityReplyViewSet, basename='post-reply')


urlpatterns = [
    path('auth/register/', UserRegisterView.as_view(), name='auth_register'),
    path('auth/login/', UserLoginView.as_view(), name='auth_login'),
    path('auth/profile', UserProfileView.as_view(), name='auth_profile_update'),
    path('auth/forgot-password/send-code/', PasswordResetRequestView.as_view(), name='password_reset_request'),
    path('auth/reset-password/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('auth/change-phone/initiate-verification/', ChangePhoneInitiateView.as_view(), name='change_phone_initiate'),
    path('auth/change-phone/verify-new/', ChangePhoneVerifyNewView.as_view(), name='change_phone_verify_new'),
    path('auth/change-phone/commit/', ChangePhoneCommitView.as_view(), name='change_phone_commit'),
    path('auth/change-mail/initiate-verification/', ChangeEmailInitiateView.as_view(), name='change_email_initiate'),
    path('auth/change-mail/verify-new/', ChangeEmailVerifyNewView.as_view(), name='change_email_verify_new'),
    path('auth/change-mail/commit/', ChangeEmailCommitView.as_view(), name='change_email_commit'),
    path('certification/submit/', CertificationSubmitView.as_view(), name='certification_submit'),
    path('uploads/editor-image/', EditorImageView.as_view(), name='editor-image-upload'),
    path('', include(router.urls)),    
    path('', include(communities_router.urls)),
    path('', include(posts_router.urls)),
    path('my/messages/', MessageThreadListCreateView.as_view(), name='my-messages-list-create'),
    path('my/messages/<int:pk>/', MessageThreadRetrieveDestroyView.as_view(), name='my-messages-detail-destroy'),
    path('users/search/', UserSearchView.as_view(), name='user-search'),
    path('my/collections/', MyCollectionsView.as_view(), name='my-collections'),
    path('my/supported/', MySupportedView.as_view(), name='my-supported'),
    path('my/creations/', MyCreationsView.as_view(), name='my-creations'),
    path('my/participations/', MyParticipationsView.as_view(), name='my-participations'),
    path('my/profile/', UserProfileView.as_view(), name='my_profile'),
    path('my/points/', views.PointsHistoryListView.as_view(), name='points-history'),
    
    path('creator/gallery/', GalleryItemCreateView.as_view(), name='gallery-create'),
    path('creator/gallery/<int:pk>/', GalleryItemUpdateView.as_view(), name='gallery-update'),
    path('creator/communities/<int:pk>/', CommunityUpdateView.as_view(), name='community-update'),
    path('creator/communities/', CommunityCreateView.as_view(), name='community-create'),
    # 课程 (Course)
    path('creator/courses/', 
         views.MyCourseListView.as_view(), name='creator-course-list'),
    path('creator/courses/new/', 
         views.CourseCreateView.as_view(), name='creator-course-create'),
    path('creator/courses/<int:pk>/', 
         views.CourseUpdateDetailView.as_view(), name='creator-course-detail-update'),
    path('creator/courses/<int:pk>/submit/', 
         views.CourseSubmitReviewView.as_view(), name='creator-course-submit'),
    
    # 章节 (Chapter) - (你已提供的)
    path('creator/courses/<int:course_pk>/chapters/', 
         views.ChapterCreateView.as_view(), name='creator-chapter-create'),
    path('creator/chapters/<int:pk>/', 
         views.ChapterDetailView.as_view(), name='creator-chapter-detail'),
    path('creator/courses/<int:course_pk>/chapters/order/', 
         views.ChapterOrderUpdateView.as_view(), name='creator-chapter-order'),

    # 练习题 (Exercise) - (新添加的)
    path('creator/chapters/<int:chapter_pk>/exercises/', 
         views.ExerciseCreateView.as_view(), name='creator-exercise-create'),
    path('creator/exercises/<int:pk>/', 
         views.ExerciseDetailView.as_view(), name='creator-exercise-detail'),
    ]
