# backend/api/permissions.py

# backend/api/permissions.py

from rest_framework.permissions import BasePermission
from .models import Community, Subscription, GalleryDownloadRecord

class CanPostOrReplyInCommunity(BasePermission):
    """
    自定义权限，检查用户是否可以在特定社群中发帖或回帖。(逻辑修复版)
    """
    message = "You do not have permission to post or reply in this community."

    def has_permission(self, request, view):
        # ... (获取 community 的部分保持不变) ...
        community_pk = view.kwargs.get('community_pk')
        post_pk = view.kwargs.get('post_pk')
        community = None
        if community_pk:
            try:
                community = Community.objects.get(pk=community_pk)
            except Community.DoesNotExist:
                self.message = "Community not found."; return False
        elif post_pk:
            try:
                community = Community.objects.get(posts__pk=post_pk)
            except Community.DoesNotExist:
                self.message = "Community for the post not found."; return False
        else:
            return False

        # --- 核心权限检查逻辑 (全新升级) ---
        
        # 1. 检查社群是否为开放社群
        if not community.related_course and not community.related_gallery_item:
            return True # 开放社群，允许

        # 2. 如果是门禁社群，用户必须已登录
        if not request.user.is_authenticated:
            self.message = "You must be logged in to post in this restricted community."
            return False

        user = request.user
        
        # 3. 检查是否满足课程订阅条件 (如果有关联)
        if community.related_course:
            has_course_permission = Subscription.objects.filter(user=user, course=community.related_course).exists()
            if not has_course_permission:
                self.message = f"You must be subscribed to the course '{community.related_course.title}' to post here."
                return False # 不满足课程条件，直接拒绝

        # 4. 检查是否满足作品下载条件 (如果有关联)
        if community.related_gallery_item:
            has_gallery_permission = GalleryDownloadRecord.objects.filter(user=user, gallery_item=community.related_gallery_item).exists()
            if not has_gallery_permission:
                self.message = f"You must own the gallery item '{community.related_gallery_item.title}' to post here."
                return False # 不满足画廊条件，直接拒绝
            
        # 只有通过了所有存在的检查，才能最终被允许
        return True