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
CourseUpdateView,GalleryItemUpdateView,CommunityUpdateView)

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
    path('creator/courses/', CourseCreateView.as_view(), name='course-create'),
    path('creator/courses/<int:pk>/', CourseUpdateView.as_view(), name='course-update'),
    path('creator/gallery/', GalleryItemCreateView.as_view(), name='gallery-create'),
    path('creator/gallery/<int:pk>/', GalleryItemUpdateView.as_view(), name='gallery-update'),
    path('creator/communities/<int:pk>/', CommunityUpdateView.as_view(), name='community-update'),
    path('creator/communities/', CommunityCreateView.as_view(), name='community-create'),
    ]
