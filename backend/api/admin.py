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
                      Collection,UserChapterCompletion,
                      Option,fill_in_blank,UserExerciseSubmission,
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
    fields = ('text', 'is_correct')
    extra = 4  # 默认提供4个空的选项输入框
    max_num = 8 # 最多只能添加4个选项
    verbose_name = "多选题选项"
    verbose_name_plural = "多选题选项"

class FillInBlankInline(admin.TabularInline):
    """填空题答案的内联编辑器"""
    model = fill_in_blank
    extra = 1
    fields = ('index_number', 'correct_answer', 'case_sensitive')
    verbose_name = "填空题答案"
    verbose_name_plural = "填空题答案"

class UserExerciseSubmissionInline(admin.TabularInline):
    model = UserExerciseSubmission
    extra = 0
    verbose_name_plural = '练习题提交历史'
    fields = ('submitted_at', 'exercise_link', 'submitted_answer', 'is_correct')
    readonly_fields = fields # 设为只读
    ordering = ('-submitted_at',)

    def exercise_link(self, obj):
        url = reverse('admin:api_exercise_change', args=[obj.exercise.id])
        return format_html('<a href="{}">{}</a>', url, obj.exercise)
    exercise_link.short_description = '题目'

    def has_add_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False
    def has_change_permission(self, request, obj=None): return False

    def get_queryset(self, request):
        # 默认只显示最近的 20 条提交记录，避免页面过长
        return super().get_queryset(request).order_by('-submitted_at')[:20]

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
    
class GalleryCollectionInline(admin.TabularInline):
    model = GalleryCollection
    extra = 0
    verbose_name_plural = '收藏记录'
    fields = ('user', 'collected_at')
    readonly_fields = ('collected_at',)
    autocomplete_fields = ['user']
    ordering = ('-collected_at',)

    def has_add_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False
    def has_change_permission(self, request, obj=None): return False

    def get_queryset(self, request):
        # 默认只显示最近的 20 条收藏记录
        return super().get_queryset(request).order_by('-collected_at')

class AuthoredCoursesInline(admin.TabularInline):
    model = Course
    fk_name = 'author'
    extra = 0
    verbose_name_plural = '创建的课程'
    fields = ('title', 'status', 'created_at')
    readonly_fields = ('created_at',)

class AuthoredGalleryItemsInline(admin.TabularInline):
    model = GalleryItem
    fk_name = 'author'
    extra = 0
    verbose_name_plural = '发布的画廊作品'
    fields = ('title', 'status', 'created_at')
    readonly_fields = ('created_at',)

class CertificationRequestInline(admin.TabularInline):
    model = CertificationRequest
    fk_name = 'applicant'
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
    extra = 0
    verbose_name_plural = "消息记录"
    formfield_overrides = {
        BleachField: {'widget': TinyMCE(attrs={'cols': 80, 'rows': 15})},
    }
    fields = ('sender', 'recipient', 'content', 'cc_recipient', 'sent_at', 'is_recipient_read', 'is_cc_read')
    readonly_fields = ('sent_at',)
    autocomplete_fields = ['sender', 'recipient', 'cc_recipient']
    ordering = ('sent_at',)

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    actions = ['suspend_accounts', 'activate_accounts', 'promote_to_artist']
    # 定义在 user 搜索框中可以搜索的字段
    list_display = ('username', 'email', 'nickname', 'role','accountStatus','currentPoints','last_activity_at','date_joined')
    list_filter = ('role','accountStatus','groups')
    boolean_fields = ['is_beta_tester','is_staff']
    search_fields = ['username', 'email', 'phone', 'nickname']
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('核心信息', {'fields': ('nickname', 'email', 'phone')}),
        ('用户画像', {'fields': ('avatarUrl', 'bio','ageGroup', 'gender', 'interests')}),
        ('权限控制', {'fields': ('role', 'vip_expiration_date', 'currentPoints', 'is_staff', 'is_beta_tester','groups')}),
        ('状态控制', {'fields': ('accountStatus', 'pointsStatus')}),
        ('内部标识', {'fields': ('wechat_openid', 'is_deleted', 'deleted_at')}),
        ('关联内容', {'fields': ('posts_link',)}),
        ('重要日期', {'fields': ('last_login', 'date_joined', 'last_activity_at')}),
        ('缓存计数', {'fields': ('unread_message_count', 'posts_authored_count', 'items_authored_count', 'course_authored_count')}),
    )
    readonly_fields = (
        'last_login', 'date_joined', 'last_activity_at', 'posts_link', 
        'unread_message_count', 'posts_authored_count', 'items_authored_count', 
        'course_authored_count', 'deleted_at'
    )
    inlines = [
        PointsTransactionInline,
        SubscriptionInline,
        GalleryDownloadRecordInline,
        AuthoredCoursesInline,
        AuthoredGalleryItemsInline,
        CertificationRequestInline,
    ]
    def avatar_thumbnail(self, obj):
        """
        在后台显示头像的缩略图。
        obj 代表当前的 User 实例。
        """
        if obj.avatarUrl:
            return format_html('<a href="{}"><img src="{}" width="50" height="50" style="object-fit: cover; border-radius: 50%;" /></a>', obj.avatarUrl.url, obj.avatarUrl.url)
        return "无头像"
    
    avatar_thumbnail.short_description = '头像预览'
    def posts_link(self, obj):
        count = obj.community_posts.count()
        url = reverse('admin:api_communitypost_changelist') + f'?author__id__exact={obj.id}'
        return format_html('<a href="{}" target="_blank">查看并管理该用户的 {} 篇帖子</a>', url, count)
    posts_link.short_description = '发布的帖子'

    def suspend_accounts(self, request, queryset):
        queryset.update(accountStatus=User.AccountStatus.SUSPENDED)
    suspend_accounts.short_description = "暂停选中用户的账号"

    def activate_accounts(self, request, queryset):
        queryset.update(accountStatus=User.AccountStatus.ACTIVE)
    activate_accounts.short_description = "激活选中用户的账号"

    def freeze_accounts(self, request, queryset):
        queryset.update(accountStatus=User.AccountStatus.FROZEN)
    freeze_accounts.short_description = "冻结选中用户的账号"

    def promote_to_artist(self, request, queryset):
        queryset.update(role=User.UserRole.ARTIST)
    promote_to_artist.short_description = "将选中用户提升为创作者"

    def set_as_beta_tester(self, request, queryset):
        queryset.update(is_beta_tester=True)
    set_as_beta_tester.short_description = "设为测试用户"


# ===============================================
# =======       课程后台管理         =======
# ===============================================
@admin.register(Course)
class CourseAdmin(RichTextAdminMixin, VersionAdmin):
    list_display = (
        'id', 'title', 'author', 'status', 'chapter_count', 
        'subscription_link', 'collection_link',
        'completion_rate','is_vip_free','display_tags_summary')
    list_filter = ('tags',)
    list_editable = ('status', 'is_vip_free')
    search_fields = ['title', 'description', 'author__username']
    fieldsets = (
        ('核心管理', {'fields': ('status', 'is_vip_free','tags')}),
        ('课程内容 ', {'fields': ('title', 'author', 'description', 'coverImage', 'pricePoints',)}),
        ('时间戳 ', {'fields': ('created_at', 'updated_at')}),
    )
    inlines = [ChapterInline]
    filter_horizontal = ('tags',)
    readonly_fields = ('title', 'description', 'author', 'pricePoints', 'coverImage','created_at', 'updated_at') 
    def has_add_permission(self, request, obj=None):
        return False
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
        subscribers = obj.subscribers.all()
        completed_counts = UserChapterCompletion.objects.filter(
            user__in=subscribers, chapter__course=obj
        ).values('user').annotate(completed_count=Count('chapter'))
        total_chapters = obj.chapters.count()
        if total_chapters == 0:
            return "N/A"
        completer_count = sum(1 for item in completed_counts if item['completed_count'] == total_chapters)
        
        rate = (completer_count / subscriber_count) * 100
        return f"{rate:.2f}%"
    completion_rate.short_description = '完读率'
    def display_tags_summary(self, obj):
        """返回前三个标签的名称，用逗号分隔"""
        tags = obj.tags.all() 
        limit = 3
        tag_list = [tag.name for tag in tags[:limit]]
        if len(tags) > limit:
            tag_summary = ", ".join(tag_list) + "..."
        else:
            tag_summary = ", ".join(tag_list)
            
        # 优化：如果需要链接到标签过滤页面，可以使用 mark_safe
        # return mark_safe(f'<a href="/admin/myapp/tag/?q={tag_list[0]}">{tag_summary}</a>')
        
        return tag_summary
    display_tags_summary.short_description = "标签"

@admin.register(Exercise)
class ExerciseAdmin(RichTextAdminMixin, admin.ModelAdmin):
    list_display = ('id', 'prompt', 'chapter', 'type', 'completion_count','display_custom_id')
    list_filter = ('type', 'chapter__course',)
    search_fields = ('prompt', 'explanation','type')
    inlines = [OptionInline,FillInBlankInline,UserExerciseSubmissionInline]
    autocomplete_fields = ['chapter']
    def get_inlines(self, request, obj=None):
        if obj:
            if obj.type == 'multiple-choice':
                return [OptionInline]
            elif obj.type == 'fill-in-the-blank':
                return [FillInBlankInline]
        return [] 
    fieldsets = [
        (None, {'fields': ('chapter', 'type', 'prompt')}),
        ('题目配图 (可选)', {'fields': ('image_upload', 'image_url'), 'classes': ('collapse',)}),
        ('答案与解析', {'fields': ('explanation',)}),
    ]
    def display_custom_id(self, obj):
        try:
            exercise_order = list(obj.chapter.exercises.all()).index(obj) + 1
            return f"C{obj.chapter.course.id}-CH{obj.chapter.id}-E{exercise_order}"
        except (AttributeError, ValueError):
            return "N/A"
    display_custom_id.short_description = "题目ID"
    def submission_count(self, obj):
        return obj.submissions.count()
    submission_count.short_description = '总提交次数'
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
# ===============================================
# =======       画廊后台管理         =======
# ===============================================
@admin.register(GalleryItem)
class GalleryItemAdmin(RichTextAdminMixin, VersionAdmin): 
    list_display = ('id', 'title', 'author', 'status', 'display_tags_summary','version', 'requiredPoints', 'rating', 'download_count', 'collection_count','is_vip_free')
    list_editable = ('status', 'is_vip_free',) 
    list_filter = ('tags',)
    inlines = [GalleryDownloadRecordInline,GalleryCollectionInline]
    search_fields = ('title', 'description', 'tags')
    autocomplete_fields = ['author', 'prerequisiteWork']
    filter_horizontal = ('tags',)
    fieldsets = (
        ('核心管理', {'fields': ('status', 'is_vip_free','tags')}),
        ('作品内容', {
            'fields': (
                'title', 'author', 'description', 'coverImage', 'workFile',
                'requiredPoints', 'prerequisiteWork', 'version'
            )
        }),
        ('数据统计', {
            'fields': ('rating', 'estimated_download_time_formatted', 'created_at', 'updated_at')
        }),
    ) 

    readonly_fields = (
        'title', 'author', 'description', 'coverImage', 'workFile',
        'requiredPoints', 'prerequisiteWork', 'version', 
        'rating', 'estimated_download_time_formatted', 'created_at', 'updated_at'
    )
    def has_add_permission(self, request, obj=None):
        return False
    # 自定义函数，用于计算并链接到下载记录
    def download_count(self, obj):
        count = obj.downloaders.count()
        url = reverse('admin:api_gallerydownloadrecord_changelist') + f'?gallery_item__id__exact={obj.id}'
        return format_html('<a href="{}">{}</a>', url, count)
    download_count.short_description = '下载次数'

    # 自定义函数，用于计算并链接到收藏记录
    def collection_count(self, obj):
        count = obj.collectors.count()
        url = reverse('admin:api_gallerycollection_changelist') + f'?gallery_item__id__exact={obj.id}'
        return format_html('<a href="{}">{}</a>', url, count)
    collection_count.short_description = '收藏次数'
    def display_tags_summary(self, obj):
        """返回前三个标签的名称，用逗号分隔"""
         # 1. 立即執行查詢並將結果轉換為一個 Python 列表
       #    使用 list() 會立即觸發資料庫查詢
        all_tags = list(obj.tags.all())
       
        limit = 3
       
       # 2. 現在對這個普通的 Python 列表進行切片，這是完全安全的
        tags_to_display = all_tags[:limit]
       
       # 3. 構建顯示的字串
        tag_list = [tag.name for tag in tags_to_display]
       
       # 4. (效率優化) 使用 len() 檢查列表長度，而不是對 QuerySet 使用 .count()
        if len(all_tags) > limit:
            return ", ".join(tag_list) + "..."
        else:
            return ", ".join(tag_list)
           
    display_tags_summary.short_description = "标签"
    def estimated_download_time_formatted(self, obj):
        """将秒转换为更易读的分钟和秒"""
        if obj.estimated_download_time and obj.estimated_download_time > 0:
            total_seconds = int(obj.estimated_download_time)
            minutes = total_seconds // 60
            seconds = total_seconds % 60
            if minutes > 0:
                return f"{minutes} 分 {seconds} 秒"
            return f"{seconds} 秒"
        return "N/A" # 如果没有时间数据，则显示 N/A
    estimated_download_time_formatted.short_description = '预计下载时间'

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

# ===============================================
# =======       社群后台管理         =======
# ===============================================

@admin.register(Community)
class CommunityAdmin(RichTextAdminMixin, admin.ModelAdmin):
    form = CommunityAdminForm
    list_display = ('name', 'founder','status','member_count','post_count','updated_at','display_tags_summary')
    list_editable = ('status',)
    list_filter = ('tags',)
    search_fields = ('name', 'description', 'founder__username')
    autocomplete_fields = ['founder','related_course','related_gallery_item']
    filter_horizontal = ('tags','assistants','members')
    fieldsets = (
        ('核心管理', {'fields': ('status', 'tags')}),
        ('社群内容', {
            'fields': ('name', 'founder', 'description', 
                       'coverImage')
        }),
        ('关联与门禁', {
            'fields': ('related_course', 'related_gallery_item')
        }),
        ('成员管理', {
            'fields': ('assistants', 'members')
        }),
        ('数据统计', {
            'fields': ('post_count', 'created_at', 'updated_at')
        }),
    )
    readonly_fields = (
        'founder', 'description', 'coverImage', 'assistants', 'members',
        'related_course', 'related_gallery_item', 'post_count', 
        'created_at', 'updated_at'
    )
    def has_add_permission(self, request):
        return False
    def member_count(self, obj):
        return obj.members.count()
    member_count.short_description = '成员人数'
    def display_tags_summary(self, obj):
        """返回前三个标签的名称，用逗号分隔"""
        tags = obj.tags.all() 
        limit = 3
        tag_list = [tag.name for tag in tags[:limit]]
        if len(tags) > limit:
            tag_summary = ", ".join(tag_list) + "..."
        else:
            tag_summary = ", ".join(tag_list)
            
        # 优化：如果需要链接到标签过滤页面，可以使用 mark_safe
        # return mark_safe(f'<a href="/admin/myapp/tag/?q={tag_list[0]}">{tag_summary}</a>')
        
        return tag_summary
    display_tags_summary.short_description = "标签"

@admin.register(CommunityPost)
class CommunityPostAdmin(RichTextAdminMixin,admin.ModelAdmin):
    list_display = ('title', 'status','community', 'author', 'rewardPoints', 'created_at','participant_count')
    list_editable =('status',)
    list_filter = ('community',)
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
    readonly_fields = ('created_at','last_message_at')
    autocomplete_fields = ['participants']
    filter_horizontal = ('participants',)
    inlines = [MessageInline]
    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        thread = form.instance
        latest_message_time = thread.last_message_at or thread.created_at        
        for instance in instances:
            if not instance.pk and isinstance(instance, Message):
                if not instance.cc_recipient:
                    admin_user = User.objects.filter(is_superuser=True).first()
                    if admin_user:
                        instance.cc_recipient = admin_user
            instance.save()
            if instance.sent_at > latest_message_time:
                latest_message_time = instance.sent_at
            
            formset.save_m2m()

        participants = set(thread.participants.all())
        for message in thread.messages.all():
            if message.sender: participants.add(message.sender)
            if message.recipient: participants.add(message.recipient)
            if message.cc_recipient: participants.add(message.cc_recipient)
        thread.participants.set(participants)
        thread.last_message_at = latest_message_time
        thread.save()

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('thread', 'sender', 'recipient', 'sent_at')
    def get_model_perms(self, request):
        return {} 