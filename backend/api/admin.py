# backend/api/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin 
from tinymce.widgets import TinyMCE
from django_bleach.models import BleachField
from django.db.models import Count
from django import forms
from django.urls import reverse
from django.utils.html import format_html
from reversion.admin import VersionAdmin 
from .models import (User, Tag, Course, Chapter, Exercise,
                      CertificationRequest, Subscription, 
                      Collection,UserChapterCompletion,Option,
                      GalleryItem, GalleryCollection, 
                      GalleryDownloadRecord, GalleryItemRating,
                      Community,CommunityPost,CommunityReply,PointsTransaction,
                      VipPlan,
                      PendingCertificationRequest,PendingCommunityPost,
                      PendingCourse,PendingGalleryItem,
                      Message,MessageThread)

# --- 自定义表单 ---
class CommunityAdminForm(forms.ModelForm):
    class Meta:
        model = Community
        fields = '__all__'
    def clean_assistants(self):
        assistants = self.cleaned_data.get('assistants')
        if assistants and assistants.count() > 3:
            raise forms.ValidationError("最多只能设置3个助手。")
        return assistants

# --- 可复用的 Mixin ---
class RichTextAdminMixin:
    formfield_overrides = {
        BleachField: {'widget': TinyMCE(attrs={'cols': 80, 'rows': 30})},
    }
#内联编辑部分
class OptionInline(admin.TabularInline):
    """选项的内联编辑器"""
    model = Option
    # 显示 text 和 is_correct 字段
    fields = ('text', 'is_correct')
    extra = 4  # 默认提供4个空的选项输入框
    max_num = 8 # 最多只能添加4个选项

class ChapterInline(admin.TabularInline):
    model = Chapter
    extra = 1
    fields = ('title', 'order','videoUrl')
    ordering = ['order']

class SubscriptionInline(admin.TabularInline):
    model = Subscription
    extra = 0
    verbose_name_plural = '订阅的课程'
    fields = ('course', 'course_price', 'learning_progress', 'subscribed_at')
    readonly_fields = ('course_price', 'learning_progress', 'subscribed_at')
    autocomplete_fields = ['course']
    def course_price(self, obj):
        return f"{obj.course.pricePoints} 积分"

    def learning_progress(self, obj):
        total_chapters = obj.course.chapters.count()
        if total_chapters == 0: 
            return "0%"
        completed_chapters = UserChapterCompletion.objects.filter(user=obj.user, chapter__course=obj.course).count()
        progress = (completed_chapters / total_chapters) * 100
        return f"{progress:.0f}% ({completed_chapters}/{total_chapters})"

class GalleryDownloadRecordInline(admin.TabularInline):
    model = GalleryDownloadRecord
    extra = 0
    verbose_name_plural = '下载的作品'
    fields = ('gallery_item','item_version','points_spent', 'downloaded_at')
    readonly_fields = ('item_version','downloaded_at',)
    autocomplete_fields = ['gallery_item']
    def item_version(self, obj):
        return obj.gallery_item.version

class AuthoredCoursesInline(admin.TabularInline):
    model = Course
    extra = 0
    verbose_name_plural = '创建的课程'
    fields = ('title', 'status', 'created_at')
    readonly_fields = ('created_at',)

class AuthoredGalleryItemsInline(admin.TabularInline):
    model = GalleryItem
    extra = 0
    verbose_name_plural = '发布的画廊作品'
    fields = ('title', 'status', 'created_at')
    readonly_fields = ('created_at',)

class CertificationRequestInline(admin.TabularInline):
    model = CertificationRequest
    extra = 0
    verbose_name_plural = '提交的认证申请'
    fields = ('status', 'submissionDate', 'certificationFile')
    readonly_fields = ('submissionDate',)

class PointsTransactionInline(admin.TabularInline):
    model = PointsTransaction
    fk_name = 'user'
    extra = 0
    verbose_name_plural = '积分流水'
    

    fields = ('created_at', 'amount', 'description', 'transaction_type', 'linked_object', 'operator')
    readonly_fields = ('created_at', 'amount', 'description', 'transaction_type', 'linked_object', 'operator')
    
    ordering = ('-created_at',)

    def linked_object(self, obj):
        """创建一个可点击的链接，指向关联的具体内容（课程、帖子等）"""
        if obj.content_object:
            url = reverse(
                f'admin:{obj.content_type.app_label}_{obj.content_type.model}_change', 
                args=[obj.object_id]
            )
            return format_html('<a href="{}">{}</a>', url, obj.content_object)
        return "N/A"
    linked_object.short_description = '关联内容' 

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

class CommunityReplyInline(admin.TabularInline):
    model = CommunityReply
    extra = 1
    fields = ('author', 'content', 'created_at')
    readonly_fields = ('created_at',)
    autocomplete_fields = ['author']

class MessageInline(admin.TabularInline):
    model = Message
    extra = 1
    formfield_overrides = {
        BleachField: {'widget': TinyMCE(attrs={'cols': 80, 'rows': 15})},
    }
    fields = ('sender', 'recipient', 'content', 'cc_recipient', 'sent_at')
    readonly_fields = ('sent_at',)
    autocomplete_fields = ['sender', 'recipient', 'cc_recipient']

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    actions = ['suspend_accounts', 'activate_accounts', 'promote_to_artist']
    # 定义在 user 搜索框中可以搜索的字段
    list_display = ('username', 'email', 'nickname', 'role','currentPoints', 'is_staff', 'last_login','date_joined')
    list_filter = ('role','is_staff','accountStatus', 'is_active', 'groups')
    search_fields = ['username', 'email', 'phone', 'nickname']
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('个人信息', {'fields': ('nickname', 'email', 'phone', 'ageGroup', 'gender', 'interests')}),
        ('平台数据', {'fields': ('role', 'vip_expiration_date', 'currentPoints')}),
        ('状态控制', {'fields': ('accountStatus', 'pointsStatus')}),
        ('关联内容', {'fields': ('posts_link',)}),
        ('权限', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups')}),
        ('重要日期', {'fields': ('last_login', 'date_joined')}),
    )
    readonly_fields = ('last_login', 'date_joined','posts_link')

    inlines = [
        PointsTransactionInline,
        SubscriptionInline,
        GalleryDownloadRecordInline,
        AuthoredCoursesInline,
        AuthoredGalleryItemsInline,
        CertificationRequestInline,
    ]
    readonly_fields += ('posts_link',)
    def posts_link(self, obj):
        count = obj.community_posts.count()
        url = reverse('admin:api_communitypost_changelist') + f'?author__id__exact={obj.id}'
        return format_html('<a href="{}" target="_blank">查看并管理该用户的 {} 篇帖子</a>', url, count)
    posts_link.short_description = '发布的帖子'

    def suspend_accounts(self, request, queryset):
        queryset.update(accountStatus='suspended')
    suspend_accounts.short_description = "暂停选中用户的账号"

    def activate_accounts(self, request, queryset):
        queryset.update(accountStatus='active')
    activate_accounts.short_description = "激活选中用户的账号"

    def promote_to_artist(self, request, queryset):
        queryset.update(role='Student-artist')
    promote_to_artist.short_description = "将选中用户提升为创作者"


@admin.register(Course)
class CourseAdmin(RichTextAdminMixin, VersionAdmin):
    list_display = (
        'id', 'title', 'author', 'status', 'chapter_count', 
        'subscription_link', 'collection_link', 'completion_rate'
    )
    list_filter = ('status', 'author', 'tags')
    search_fields = ['title', 'description', 'author__username']
    inlines = [ChapterInline]
    filter_horizontal = ('tags',)
    is_vip_free: bool = False
    readonly_fields = ('created_at', 'updated_at') # 将时间戳设为只读

    def chapter_count(self, obj):
        return obj.chapters.count()
    chapter_count.short_description = '章节数'

    def subscription_link(self, obj):
        count = obj.subscribers.count()
        url = reverse('admin:api_subscription_changelist') + f'?course__id__exact={obj.id}'
        return format_html('<a href="{}">{}</a>', url, count)
    subscription_link.short_description = '订阅人数'

    def collection_link(self, obj):
        count = obj.collectors.count()
        url = reverse('admin:api_collection_changelist') + f'?course__id__exact={obj.id}'
        return format_html('<a href="{}">{}</a>', url, count)
    collection_link.short_description = '收藏人数'

    def completion_rate(self, obj):
        subscriber_count = obj.subscribers.count()
        if subscriber_count == 0:
            return "0.0%"
        
        # 找到所有订阅者
        subscribers = obj.subscribers.all()
        # 统计每个订阅者在该课程下完成的章节数
        completed_counts = UserChapterCompletion.objects.filter(
            user__in=subscribers, chapter__course=obj
        ).values('user').annotate(completed_count=Count('chapter'))

        # 找到完成了所有章节的用户
        total_chapters = obj.chapters.count()
        if total_chapters == 0:
            return "N/A"
            
        completer_count = sum(1 for item in completed_counts if item['completed_count'] == total_chapters)
        
        rate = (completer_count / subscriber_count) * 100
        return f"{rate:.2f}%"
    completion_rate.short_description = '完读率'


@admin.register(Exercise)
class ExerciseAdmin(RichTextAdminMixin, admin.ModelAdmin):
    list_display = ('id', 'prompt', 'chapter', 'type', 'completion_count','display_custom_id')
    list_filter = ('type', 'chapter__course', 'type')
    search_fields = ('prompt', 'explanation','type')
    inlines = [OptionInline]
    autocomplete_fields = ['chapter'] 
    fieldsets = [
        (None, {'fields': ('chapter', 'type', 'prompt')}),
        ('题目配图 (可选)', {'fields': ('image_upload', 'image_url'), 'classes': ('collapse',)}),
        ('答案与解析', {'fields': ('explanation',)}),
        ('填空题专用答案', {'fields': ('answer',), 'classes': ('collapse',)}),
    ]
    inlines = [OptionInline]

    def display_custom_id(self, obj):
        try:
            exercise_order = list(obj.chapter.exercises.all()).index(obj) + 1
            return f"C{obj.chapter.course.id}-CH{obj.chapter.id}-E{exercise_order}"
        except (AttributeError, ValueError):
            return "N/A"
    display_custom_id.short_description = "题目ID"
    def completion_count(self, obj):
        return UserChapterCompletion.objects.filter(chapter=obj.chapter).count()
    completion_count.short_description = '章节完成人数'


@admin.register(Chapter)
class ChapterAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'order', 'completion_count')
    
    def get_model_perms(self, request):
        return {}
    
    list_filter = ('course',)
    search_fields = ('title', 'course__title') 
    
    def completion_count(self, obj):
        return UserChapterCompletion.objects.filter(chapter=obj).count()
    completion_count.short_description = '完成人数'
    

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'subscribed_at')
    autocomplete_fields = ['user', 'course']
    def get_model_perms(self, request):
        # 返回空的权限字典，从而在主页隐藏
        return {}

@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'collected_at')
    autocomplete_fields = ['user', 'course']
    def get_model_perms(self, request):
        return {}

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'scope', 'creator', 'created_at', 'usage_count')
    list_filter = ('scope',)
    search_fields = ('name',)

    def usage_count(self, obj):
        return obj.courses.count() + obj.gallery_items.count() + obj.communities.count()
    usage_count.short_description = '引用次数'

#画廊相关模型
@admin.register(GalleryItem)
class GalleryItemAdmin(RichTextAdminMixin, VersionAdmin): 
    list_display = ('id', 'title', 'author', 'status', 'version', 'requiredPoints', 'rating', 'download_count', 'collection_count')
    list_filter = ('status', 'author', 'tags')
    search_fields = ('title', 'description', 'author__username')
    autocomplete_fields = ['author', 'prerequisiteWork']
    list_editable = ('status', 'version', 'requiredPoints') # 允许在列表页直接编辑版本号
    filter_horizontal = ('tags',) 
    is_vip_free: bool = False

    # 自定义函数，用于计算并链接到下载记录
    def download_count(self, obj):
        count = GalleryDownloadRecord.objects.filter(gallery_item=obj).count()
        url = reverse('admin:api_gallerydownloadrecord_changelist') + f'?gallery_item__id__exact={obj.id}'
        return format_html('<a href="{}">{}</a>', url, count)
    download_count.short_description = '下载次数'

    # 自定义函数，用于计算并链接到收藏记录
    def collection_count(self, obj):
        count = obj.collectors.count()
        url = reverse('admin:api_gallerycollection_changelist') + f'?gallery_item__id__exact={obj.id}'
        return format_html('<a href="{}">{}</a>', url, count)
    collection_count.short_description = '收藏次数'


@admin.register(GalleryCollection)
class GalleryCollectionAdmin(admin.ModelAdmin):
    list_display = ('user', 'gallery_item', 'collected_at')
    autocomplete_fields = ['user', 'gallery_item']
    search_fields = ['user__username', 'gallery_item__title']
    def get_model_perms(self, request): return {}

@admin.register(GalleryDownloadRecord)
class GalleryDownloadRecordAdmin(admin.ModelAdmin):
    list_display = ('user', 'gallery_item', 'downloaded_at', 'points_spent')
    autocomplete_fields = ['user', 'gallery_item']
    search_fields = ['user__username', 'gallery_item__title']
    def get_model_perms(self, request): return {}

@admin.register(GalleryItemRating)
class GalleryItemRatingAdmin(admin.ModelAdmin):
    list_display = ('user', 'gallery_item', 'rating', 'rated_at')
    autocomplete_fields = ['user', 'gallery_item']
    search_fields = ['user__username', 'gallery_item__title']
    def get_model_perms(self, request): return {}

#社群相关模型


@admin.register(Community)
class CommunityAdmin(RichTextAdminMixin, admin.ModelAdmin):
    form = CommunityAdminForm
    list_display = ('name', 'founder', 'created_at','member_count','display_tags')
    search_fields = ('name', 'description', 'founder__username')
    autocomplete_fields = ['founder','related_course','related_gallery_item']
    filter_horizontal = ('tags','assistants','members')
    def member_count(self, obj):
        return obj.members.count()
    member_count.short_description = '成员人数'
    def display_tags(self, obj):
        return ", ".join([tag.name for tag in obj.tags.all()])
    display_tags.short_description = '社群标签'

@admin.register(CommunityPost)
class CommunityPostAdmin(RichTextAdminMixin,admin.ModelAdmin):
    list_display = ('title', 'community', 'author', 'status', 'rewardPoints', 'created_at','participant_count')
    list_filter = ('status', 'community')
    search_fields = ('title', 'content', 'author__username')
    autocomplete_fields = ['community', 'author', 'best_answer']
    inlines = [CommunityReplyInline]
    filter_horizontal = ('likes',)
    def participant_count(self, obj):
        """动态计算并返回参与人数"""
        reply_author_ids = obj.replies.values_list('author_id', flat=True)
        participant_ids = set(reply_author_ids)
        participant_ids.add(obj.author_id)
        return len(participant_ids)
    participant_count.short_description = '参与人数'
    def likes_count(self, obj):
        return obj.likes.count()
    likes_count.short_description = '点赞人数'


@admin.register(CommunityReply)
class CommunityReplyAdmin(RichTextAdminMixin,admin.ModelAdmin):
    list_display = ('content_summary', 'author', 'post', 'created_at')
    search_fields = ('content', 'author__username', 'post__title')
    autocomplete_fields = ['post', 'author']

    def content_summary(self, obj):
        return f"{obj.content[:50]}..."
    content_summary.short_description = '内容摘要'

@admin.register(VipPlan)
class VipPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'duration_days', 'price_points')
    readonly_fields = ('view_vip_courses', 'view_vip_gallery_items')
    fieldsets = (
        (None, {'fields': ('name', 'duration_days', 'price_points')}),
        ('关联内容', {'fields': ('view_vip_courses', 'view_vip_gallery_items')}),
    )

    def view_vip_courses(self, obj):
        url = reverse('admin:api_course_changelist') + '?is_vip_free__exact=1'
        count = Course.objects.filter(is_vip_free=True).count()
        return format_html('<a href="{}" target="_blank">查看全部 {} 门 VIP 免费课程</a>', url, count)
    view_vip_courses.short_description = 'VIP 免费课程'

    def view_vip_gallery_items(self, obj):
        url = reverse('admin:api_galleryitem_changelist') + '?is_vip_free__exact=1'
        count = GalleryItem.objects.filter(is_vip_free=True).count()
        return format_html('<a href="{}" target="_blank">查看全部 {} 件 VIP 免费作品</a>', url, count)
    view_vip_gallery_items.short_description = 'VIP 免费作品'

# ===============================================
# =======       审核中心后台管理         =======
# ===============================================

@admin.register(PendingCourse)
class PendingCourseAdmin(admin.ModelAdmin):
    # 将其归入新的 "review_center" 应用（显示为“审核中心”）
    def get_model_perms(self, request):
        return {
            'view': self.has_view_permission(request),
            'change': self.has_change_permission(request),
        }
    
    list_display = ('title', 'author', 'created_at')
    actions = ['approve_selected', 'reject_selected']

    def approve_selected(self, request, queryset):
        queryset.update(status='published')
    approve_selected.short_description = "批准选中的课程"

    def reject_selected(self, request, queryset):
        queryset.update(status='rejected')
    reject_selected.short_description = "驳回选中的课程"

@admin.register(PendingGalleryItem)
class PendingGalleryItemAdmin(admin.ModelAdmin):
    def get_model_perms(self, request): 
        return {'view': True, 'change': True}
    list_display = ('title', 'author', 'created_at')
    actions = ['approve_selected', 'reject_selected']
    def approve_selected(self, request, queryset): queryset.update(status='published')
    approve_selected.short_description = "批准选中的作品"
    def reject_selected(self, request, queryset): queryset.update(status='rejected')
    reject_selected.short_description = "驳回选中的作品"



@admin.register(PendingCommunityPost)
class PendingCommunityPostAdmin(admin.ModelAdmin):
    def get_model_perms(self, request): # ... (同上)
        return {'view': True, 'change': True}
    list_display = ('title', 'author', 'created_at')
    actions = ['approve_selected', 'reject_selected']
    def approve_selected(self, request, queryset): queryset.update(status='published')
    approve_selected.short_description = "批准选中的帖子"
    def reject_selected(self, request, queryset): queryset.update(status='rejected')
    reject_selected.short_description = "驳回选中的帖子"


@admin.register(PendingCertificationRequest)
class PendingCertificationRequestAdmin(admin.ModelAdmin):
    def get_model_perms(self, request): # ... (同上)
        return {'view': True, 'change': True}
    list_display = ('applicant', 'submissionDate')
    actions = ['approve_selected', 'reject_selected']

    def approve_selected(self, request, queryset):
        for req in queryset:
            req.status = 'approved'
            req.applicant.role = 'Student-Artist' # 批准后，升级用户角色
            req.applicant.save(update_fields=['role'])
            req.save()
    approve_selected.short_description = "批准选中的认证"

    def reject_selected(self, request, queryset):
        queryset.update(status='rejected')
    reject_selected.short_description = "驳回选中的认证"

# --- 隐藏原有的 CertificationRequest 入口 ---
@admin.register(CertificationRequest)
class CertificationRequestAdmin(admin.ModelAdmin):
    list_display = ('applicant', 'status', 'submissionDate')
    def get_model_perms(self, request):
        return {} 
    
# ===============================================
# =======       站内信系统         =======
# ===============================================

@admin.register(MessageThread)
class MessageThreadAdmin(admin.ModelAdmin):
    list_display = ('subject', 'thread_type', 'created_at')
    search_fields = ('subject', 'messages__content', 'participants__username')
    list_filter = ('thread_type',)
    
    autocomplete_fields = ['participants']
    filter_horizontal = ('participants',)
    inlines = [MessageInline]

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        thread = form.instance
        
        participants = set(thread.participants.all())
        
        for instance in instances:
            if not instance.pk and isinstance(instance, Message):
                if not instance.cc_recipient:
                    admin_user = User.objects.filter(is_superuser=True).first()
                    if admin_user:
                        instance.cc_recipient = None
            instance.save()
            
            if instance.sender: participants.add(instance.sender)
            if instance.recipient: participants.add(instance.recipient)
            if instance.cc_recipient: participants.add(instance.cc_recipient)

        formset.save_m2m()
        thread.participants.set(participants)
        super().save_model(request, thread, form, change)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('thread', 'sender', 'recipient', 'sent_at')
    def get_model_perms(self, request):
        return {} 