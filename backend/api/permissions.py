# backend/api/permissions.py

from rest_framework.permissions import BasePermission,SAFE_METHODS
from .models import Community, Subscription, GalleryDownloadRecord

# ===============================================
# =======    角色权限 (Role Permissions)     =======
# ===============================================

class IsStudent(BasePermission):
    """允许学生或更高等级的角色访问"""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ['student', 'artist', 'admin']

class IsArtist(BasePermission):
    """只允许创作者或更高等级的角色访问"""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ['artist', 'admin']

class IsAdmin(BasePermission):
    """只允许管理员访问"""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'admin'
    
# ===============================================
# =======    对象权限 (Object Permissions)   =======
# ===============================================

class IsOwner(BasePermission):
    """只允许对象的所有者 (author/founder) 进行写入操作"""
    def has_object_permission(self, request, view, obj):
        # 读取权限对所有人开放
        if request.method in SAFE_METHODS:
            return True
        
        # 检查对象是否有 'author' 或 'founder' 字段
        if hasattr(obj, 'author'):
            return obj.author == request.user
        if hasattr(obj, 'founder'):
            return obj.founder == request.user
        
        return False

class IsPaidUsers(BasePermission):
    """
    自訂權限：檢查用戶是否有權限在「門禁社群」中發言。
    """
    message = "您需要先訂閱關聯課程或下載關聯作品才能在此社群發言。"

    def has_permission(self, request, view):
        # 從 URL 中獲取正在操作的社群 ID
        community_pk = view.kwargs.get('community_pk')
        try:
            community = Community.objects.get(pk=community_pk)
        except Community.DoesNotExist:
            return False
        
        if community.related_course is None and community.related_gallery_item is None:
            return True
         
        user = request.user
        if community.related_course:
            if Subscription.objects.filter(user=user, course=community.related_course).exists():
                return True  
        if community.related_gallery_item:
            if GalleryDownloadRecord.objects.filter(user=user, gallery_item=community.related_gallery_item).exists():
                return True  

        return False 