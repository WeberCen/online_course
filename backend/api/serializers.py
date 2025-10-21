# backend/api/serializers.py
import random
from rest_framework import serializers
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User,CertificationRequest,Course,Chapter,Exercise
from .models import (Subscription, Collection, Option, fill_in_blank,Tag,
                     GalleryItem, GalleryCollection, GalleryDownloadRecord, 
                     GalleryItemRating,Community,CommunityPost,CommunityReply,
                     Message,MessageThread,UserExerciseSubmission)

class TagsField(serializers.Field):
    """
    自定义字段，用于处理标签的“查找或创建”。
    接受一个字符串列表，返回一个 Tag 实例列表。
    """
    def __init__(self, *args, **kwargs):
        # 从 Serializer context 中获取 'scope'
        self.scope = kwargs.pop('scope', None)
        if not self.scope:
            raise ValueError("TagsField 必须提供 'scope' 参数。")
        super().__init__(*args, **kwargs)

    def to_representation(self, value):
        """Model -> JSON (返回标签名称列表)"""
        return [tag.name for tag in value.all()]

    def to_internal_value(self, data):
        """JSON -> Model (核心逻辑)"""
        if not isinstance(data, list):
            raise serializers.ValidationError("需要一个标签名称列表。")
        
        request = self.context.get('request')
        if not request or not hasattr(request, 'user'):
            raise serializers.ValidationError("Serializer 需要 request context。")
        
        tags_list = []
        for tag_name in data:
            tag_name = str(tag_name).strip()
            if not tag_name:
                continue
            
            # 查找或创建
            tag, created = Tag.objects.get_or_create(
                name=tag_name, 
                scope=self.scope,
                defaults={'creator': request.user} # 如果新建，则设置 creator
            )
            tags_list.append(tag)
        
        return tags_list


# ===============================================
# =======       基础配置  Serializers     =======
# ===============================================


class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    password2 = serializers.CharField(write_only=True, required=True, label="Confirm password", style={'input_type': 'password'})
    
    class Meta:
        model = User
        fields = ['username','nickname','avatarUrl','bio','email','phone','password','password2','ageGroup','gender','interests']
        extra_kwargs = {
            'username': {'required': True},
            'email': {'required': True},
            'phone': {'required': True},     
        }

    def validate(self, attrs):
        # 校验两次输入的密码是否一致
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        
        # 检查用户名、邮箱、手机是否已被注册
        if User.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError({"email": "Email already exists."})
        
        if User.objects.filter(username=attrs['username']).exists():
            raise serializers.ValidationError({"username": "Username already exists."})
            
        if User.objects.filter(phone=attrs['phone']).exists():
            raise serializers.ValidationError({"phone": "Phone number already exists."})    
        
        return attrs

    def create(self, validated_data):
        password = validated_data.pop('password')
        validated_data.pop('password2')
        # 创建用户实例，注意要对密码进行哈希加密
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user

class UserLoginSerializer(serializers.Serializer):
    identifier = serializers.CharField(label="Username, Email, or Phone")
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})

    def validate(self, data):
        identifier = data.get('identifier')
        password = data.get('password')

        if identifier and password:
            # 调用 Django 的 authenticate 方法，它会自动使用我们自定义的 MultiFieldAuthBackend
            user = authenticate(request=self.context.get('request'), username=identifier, password=password)

            if not user:
                raise serializers.ValidationError('Unable to log in with provided credentials.', code='authorization')
        else:
            raise serializers.ValidationError('Must include "identifier" and "password".', code='authorization')

        data['user'] = user
        return data

    def get_tokens_for_user(self, user):
        refresh = RefreshToken.for_user(user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }

class UserProfileSerializer(serializers.ModelSerializer):
    """
    用于用户资料展示和更新的序列化器
    """
    class Meta:
        model = User
        # 定义需要展示或可以更新的字段
        fields = [
            'id', 'username', 'avatarUrl','email', 'phone', 'nickname', 
            'currentPoints', 'role', 'ageGroup', 'gender', 'interests',
            'accountStatus', 'pointsStatus', 'bio',
            'vip_expiration_date','is_staff','is_beta_tester','unread_message_count',
            'posts_authored_count','items_authored_count','course_authored_count',
            'completed_chapters'
        ]
        # 设置某些字段为只读，防止用户通过此接口修改它们
        read_only_fields = [
            'id', 'username', 'avatarUrl','email', 'phone', 'currentPoints', 'role',
            'accountStatus', 'pointsStatus',
            'vip_expiration_date','is_staff','is_beta_tester','unread_message_count',
            'posts_authored_count','items_authored_count','course_authored_count',
            'completed_chapters'
        ]

class PasswordResetRequestSerializer(serializers.Serializer):
    """
    密码重置请求的序列化器，只用于验证邮箱
    """
    email = serializers.EmailField()

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("User with this email does not exist.")
        return value
    
class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    密码重置确认的序列化器
    """
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6, min_length=6)
    newPassword = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'}, label="New Password")
    confirmPassword = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'}, label="Confirm New Password")

    def validate(self, attrs):
        if attrs['newPassword'] != attrs['confirmPassword']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

class EditorImageSerializer(serializers.Serializer):
    """用于处理编辑器上传图片的序列化器"""
    image = serializers.ImageField(required=True)

#手机号更换
class ChangePhoneInitiateSerializer(serializers.Serializer):
    # 在API文档中，这一步需要用户选择验证方式，我们简化为默认发送到已绑定的邮箱
    pass 

class ChangePhoneVerifyNewSerializer(serializers.Serializer):
    newPhone = serializers.CharField(max_length=20)

class ChangePhoneCommitSerializer(serializers.Serializer):
    newPhone = serializers.CharField(max_length=20)
    identityCode = serializers.CharField(max_length=6, min_length=6, label="旧手机验证码")
    newCode = serializers.CharField(max_length=6, min_length=6, label="新手机验证码")



# 更换邮箱 

class ChangeEmailInitiateSerializer(serializers.Serializer):
    pass # 同样，直接从 request.user 获取旧手机

class ChangeEmailVerifyNewSerializer(serializers.Serializer):
    newMail = serializers.EmailField()

class ChangeEmailCommitSerializer(serializers.Serializer):
    newMail = serializers.EmailField()
    identityCode = serializers.CharField(max_length=6, min_length=6, label="旧邮箱验证码")
    newCode = serializers.CharField(max_length=6, min_length=6, label="新邮箱验证码")

#身份认证
class CertificationRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = CertificationRequest
        fields = ['id', 'applicant', 'status', 'certificationFile', 'notes', 'submissionDate']
        read_only_fields = ['id', 'applicant', 'status', 'submissionDate']

    def validate(self, attrs):
        # 检查用户是否已有待处理的申请
        user = self.context['request'].user
        if CertificationRequest.objects.filter(applicant=user, status='pending').exists():
            raise serializers.ValidationError("You already have a pending certification request.")
        return attrs
    
class UserSummarySerializer(serializers.ModelSerializer):
    """用于嵌套在其他模型中的简化版用户信息"""
    class Meta:
        model = User
        fields = ['id', 'nickname', 'avatarUrl']

# ===============================================
# =======         课程模块 Serializers     =======
# ===============================================

# ==============================================================================
# A. 輔助與基礎序列化器
# ==============================================================================

class SimpleCourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ['id', 'title']

class SimpleChapterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chapter
        fields = ['id', 'title', 'order']

# --- 選項序列化器 (分角色) ---

class OptionStudentSerializer(serializers.ModelSerializer):
    """【學生版】選項序列化器 (安全，不含答案)"""
    class Meta:
        model = Option
        fields = ['id', 'text']

class OptionAdminSerializer(serializers.ModelSerializer):
    """【後台版】選項序列化器 (完整，包含答案)"""
    class Meta:
        model = Option
        fields = ['id', 'text', 'is_correct']

# ==============================================================================
# B. 學生視圖核心序列化器 (前端 API 主要使用)
# ==============================================================================

class UserSubmissionDetailSerializer(serializers.ModelSerializer):
    """【輔助】用於展示用戶作答詳情的序列化器"""
    correct_answer = serializers.SerializerMethodField()
    analysis = serializers.CharField(source='exercise.explanation', read_only=True)
    user_answer = serializers.JSONField(source='submitted_answer', read_only=True)

    class Meta:
        model = UserExerciseSubmission
        fields = ['user_answer', 'is_correct', 'correct_answer', 'analysis']
    def get_correct_answer(self, obj):
        """動態獲取關聯練習題的正確答案"""
        exercise = obj.exercise
        if exercise.type == 'multiple-choice':
            return list(exercise.options.filter(is_correct=True).values_list('text', flat=True))
        elif exercise.type == 'fill-in-the-blank':
            blank = exercise.fill_in_blanks.first()
            return blank.correct_answer if blank else None
        return None

class ExerciseStudentSerializer(serializers.ModelSerializer):
    """【學生版】練習題序列化器 (安全，且包含用戶提交記錄)"""
    options = OptionStudentSerializer(many=True, read_only=True)
    user_submission = serializers.SerializerMethodField()

    class Meta:
        model = Exercise
        fields = [
            'id', 'type', 'prompt', 'image_upload', 
            'image_url', 'options', 'user_submission'
        ]

    def get_user_submission(self, obj):
        request = self.context.get('request', None)
        if not request or not request.user.is_authenticated:
            return None

        submission = UserExerciseSubmission.objects.filter(
            user=request.user, 
            exercise=obj
        ).order_by('-submitted_at').first()

        if submission:
            # 調用輔助序列化器來格式化數據
            return UserSubmissionDetailSerializer(submission).data
        return None

class ChapterSerializer(serializers.ModelSerializer):
    """【學生版】章節序列化器"""
    # 這裡會自動使用上面已增強的 ExerciseStudentSerializer
    exercises = ExerciseStudentSerializer(many=True, read_only=True)

    class Meta:
        model = Chapter
        fields = ['id', 'title', 'order', 'videoUrl', 'exercises']

class CourseListSerializer(serializers.ModelSerializer):
    """課程列表序列化器"""
    author = UserSummarySerializer(read_only=True)
    chapterCount = serializers.IntegerField(source='chapters.count', read_only=True)
    followers_count = serializers.SerializerMethodField()
    display_tags = serializers.StringRelatedField(many=True, source='tags', read_only=True) 

    class Meta:
        model = Course
        fields = ['id', 'title', 'description', 'coverImage', 
                  'author', 'display_tags', 'chapterCount', 
                  'created_at', 'status', 'followers_count']
    
    def get_followers_count(self, obj):
        return obj.collectors.count() + obj.subscribers.count()

class CourseDetailSerializer(CourseListSerializer):
    """課程詳情序列化器"""
    chapters = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()
    is_collected = serializers.SerializerMethodField()

    class Meta(CourseListSerializer.Meta):
        fields = CourseListSerializer.Meta.fields + [
            'pricePoints', 'is_vip_free', 'chapters', 
            'is_subscribed', 'is_collected'
        ]
        
    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Subscription.objects.filter(user=request.user, course=obj).exists()
        return False

    def get_is_collected(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Collection.objects.filter(user=request.user, course=obj).exists()
        return False
        
    def get_chapters(self, obj):
        is_subscribed = self.get_is_subscribed(obj)
        chapters_queryset = obj.chapters.all()

        # 僅對非訂閱用戶限制章節數量
        if not is_subscribed:
            chapters_queryset = chapters_queryset[:3]
        
        # 關鍵：將 context 傳遞下去，以便 ExerciseStudentSerializer 能獲取 request
        return ChapterSerializer(chapters_queryset, many=True, context=self.context).data

# ==============================================================================
# C. 練習提交相關序列化器 (用於接收前端數據)
# ==============================================================================

class AnswerSerializer(serializers.Serializer):
    """單個答案的序列化器"""
    exerciseId = serializers.IntegerField()
    userAnswer = serializers.JSONField()
      
class ExerciseSubmissionSerializer(serializers.Serializer):
    """整個章節練習提交的序列化器"""
    answers = AnswerSerializer(many=True)

class UserExerciseSubmissionCreateSerializer(serializers.ModelSerializer):
    """【輔助】用於在視圖中創建/更新資料庫記錄"""
    class Meta:
        model = UserExerciseSubmission
        fields = ['user', 'exercise', 'submitted_answer', 'is_correct']
# ==============================================================================
# D. 其他特定用途序列化器
# ==============================================================================
class CourseProgressSerializer(serializers.Serializer):
    """课程进度序列化器"""   
    # 关联对象信息
    course = SimpleCourseSerializer(read_only=True)
    # 核心进度量化
    completedExercises = serializers.IntegerField() 
    totalExercises = serializers.IntegerField()     
    progressPercentage = serializers.SerializerMethodField()
    isCompleted = serializers.BooleanField()
    
    # 学习状态与导航
    nextChapterId = serializers.IntegerField(allow_null=True, required=False)
    nextChapterToComplete = SimpleChapterSerializer(read_only=True, allow_null=True)
    
    # 时间戳
    startedAt = serializers.DateTimeField(source='subscribed_at')
    lastUpdatedAt = serializers.DateTimeField(source='last_updated_at')
    completedAt = serializers.DateTimeField(source='completed_at', allow_null=True)
    
    def get_progressPercentage(self, obj):
        """动态计算进度百分比"""
        # obj 是传入的数据对象或字典
        completed = obj.get('completedExercises', 0)
        total = obj.get('totalExercises', 0)
        
        if total > 0:
            return round((completed / total) * 100,2)
        return 0
    
# ==============================================================================
# E. 後台管理/作者序列化器 (Admin-Only)
# ==============================================================================

class FillInBlankAnswerAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = fill_in_blank
        fields = ['id', 'index_number', 'correct_answer', 'case_sensitive']

class ExerciseAdminSerializer(serializers.ModelSerializer):
    """【後台版】練習題完整序列化器"""
    answer_details = serializers.SerializerMethodField()
    class Meta:
        model = Exercise
        fields = ['id', 'chapter', 'type', 'prompt', 
                  'explanation', 'image_upload', 
                  'image_url', 'answer_details']
    
    def get_answer_details(self, obj):
        if obj.type == 'multiple-choice':
            return OptionAdminSerializer(obj.options.all(), many=True).data
        elif obj.type == 'fill-in-the-blank':
            return FillInBlankAnswerAdminSerializer(obj.fill_in_blanks.all(), many=True).data
        return None

# ===============================================
# =======         画廊模块 Serializers     =======
# ===============================================

class GalleryListSerializer(serializers.ModelSerializer):
    """用于画廊作品列表的序列化器"""
    author = UserSummarySerializer(read_only=True)
    display_tags = serializers.StringRelatedField(many=True, read_only=True)
    followers_count = serializers.SerializerMethodField()
    is_collected = serializers.SerializerMethodField()
    is_downloaded = serializers.SerializerMethodField()
    
    class Meta:
        model = GalleryItem
        fields = [
            'id', 'title', 'description', 'coverImage', 'author', 'created_at',
            'display_tags', 'requiredPoints', 'rating', 'version', 'followers_count',
            'is_collected','is_downloaded'
        ]

    def get_followers_count(self, obj):
        return obj.annotated_collectors_count + obj.annotated_downloaders_count
    def get_is_collected(self, obj):
        return getattr(obj, 'annotated_is_collected', False)
    def get_is_downloaded(self, obj):
        return getattr(obj, 'annotated_is_downloaded', False)
    def get_display_tags(self, obj):
        all_tags = obj.tags.all()
        if all_tags.count() <= 3:
             return [tag.name for tag in all_tags] 
        else:
             sampled_tags = random.sample(list(all_tags), 3)
        return [tag.name for tag in sampled_tags]


class GalleryDetailSerializer(GalleryListSerializer):
    """
    用于画廊作品详情的序列化器，并包含当前用户的下载，收藏状态
    """
    class Meta(GalleryListSerializer.Meta):
        fields = GalleryListSerializer.Meta.fields + ['workFile']

# ===============================================
# =======         社群模块 Serializers     =======
# ===============================================
class CommunityListSerializer(serializers.ModelSerializer):
    """【第一级页面使用】：用于“社群板块列表”"""
    founder = UserSummarySerializer(read_only=True)
    post_count = serializers.SerializerMethodField()
    tags = serializers.StringRelatedField(many=True, read_only=True)
    

    class Meta:
        model = Community
        fields = ['id', 'name', 'description', 'founder', 'coverImage', 'tags', 'post_count'] 

    def get_post_count(self, obj):
        return obj.posts.filter(status='published').count()


class CommunityPostListSerializer(serializers.ModelSerializer):
    """
    【第二级页面使用】：用于展示“特定社群下的帖子列表” (/communities/<id>/posts/)
    """
    author = UserSummarySerializer(read_only=True)
    reply_count = serializers.SerializerMethodField()

    class Meta:
        model = CommunityPost
        fields = ['id', 'title', 'author', 'rewardPoints', 'created_at', 'reply_count','community']

    def get_reply_count(self, obj):
        # 计算该帖子下的回复总数
        return obj.replies.count()


class CommunityReplySerializer(serializers.ModelSerializer):
    """
    【第三级页面使用】：用于嵌套在帖子详情中，展示单个回帖
    """
    author = UserSummarySerializer(read_only=True)

    class Meta:
        model = CommunityReply
        fields = ['id', 'author', 'content', 'created_at']


class CommunityPostDetailSerializer(serializers.ModelSerializer):
    """
    【第三级页面使用】：用于“帖子详情页” (/communities/posts/<id>/)
    """
    author = UserSummarySerializer(read_only=True)
    # 嵌套导入该帖子下的所有回帖
    replies = CommunityReplySerializer(many=True, read_only=True)
    
    class Meta:
        model = CommunityPost
        # 返回帖子的所有详细信息
        fields = [
            'id', 'title', 'content', 'author', 'status', 
            'rewardPoints', 'created_at', 'updated_at', 
            'best_answer', # 最佳答案的 ID
            'replies'      # 嵌套的回复列表
        ]

class CommunityPostCreateSerializer(serializers.ModelSerializer):
    """【发帖用】用于创作者提交新帖子的序列化器"""
    class Meta:
        model = CommunityPost
        fields = ['title', 'content', 'rewardPoints']


class CommunityReplyCreateSerializer(serializers.ModelSerializer):
    """【回帖用】用于用户提交新回复的序列化器"""
    class Meta:
        model = CommunityReply
        fields = ['content']

class CommunityCreateSerializer(serializers.ModelSerializer):
    """【创建社群用】的序列化器"""
    class Meta:
        model = Community
        fields = ['name', 'description', 'tags', 'coverImage', 'related_course', 'related_gallery_item','assistants']
class CommunityDetailSerializer(serializers.ModelSerializer):
    """【编辑/详情页使用】用于获取单个社群的完整可编辑详情"""
    founder = UserSummarySerializer(read_only=True)
    class Meta:
        model = Community
        # 包含所有创作者可编辑的字段
        fields = [
            'id', 'name', 'description', 'founder', 'coverImage', 
            'tags', 'related_course', 'related_gallery_item'
        ]

# ===============================================
# =======    站内信 API Serializers  =======
# ===============================================

class MessageSerializer(serializers.ModelSerializer):
    """用于嵌套在会话中，显示单条消息"""
    sender = UserSummarySerializer(read_only=True)
    
    class Meta:
        model = Message
        fields = ['id', 'sender', 'content', 'sent_at']

class MessageThreadListSerializer(serializers.ModelSerializer):
    """ 用于会话列表的序列化器"""
    last_message = serializers.SerializerMethodField()
    
    class Meta:
        model = MessageThread
        fields = ['id', 'subject', 'thread_type', 'last_message', 'created_at']

    def get_last_message(self, obj):
        # 获取该会话的最后一条消息用于预览
        if hasattr(obj, 'messages') and obj.messages.all():
            # 这里的 .all() 不会触发新查询，因为它正在访问 Prefetch 缓存
            last_msg = obj.messages.all()[0]
            return MessageSerializer(last_msg).data
        return None

class MessageCreateSerializer(serializers.Serializer):
    """用于用户发送新消息的序列化器"""
    subject = serializers.CharField(max_length=255)
    content = serializers.CharField()
    recipient_id = serializers.IntegerField()

    def validate_recipient_id(self, value):
        if not User.objects.filter(pk=value).exists():
            raise serializers.ValidationError("指定的收件人不存在。")
        return value
    
class MessageThreadDetailSerializer(serializers.ModelSerializer):
    """
    【GET /my/messages/{id}】: 用于单个会话详情页的序列化器
    """
    # 嵌套 MessageSerializer，并指明这是一个包含多条消息的列表
    messages = MessageSerializer(many=True, read_only=True)
    participants = UserSummarySerializer(many=True, read_only=True)

    class Meta:
        model = MessageThread
        fields = ['id', 'subject', 'thread_type', 'participants', 'created_at', 'messages']

# ===============================================
# =======    个人中心 API Serializers     =======
# ===============================================

class MyCollectionsSerializer(serializers.Serializer):
    """【/my/collections】 我的收藏"""
    courses = CourseListSerializer(many=True, read_only=True)
    gallery_items = GalleryListSerializer(many=True, read_only=True)

class MySupportedSerializer(serializers.Serializer):
    """【/my/supported】 我的已购"""
    courses = CourseListSerializer(many=True, read_only=True)
    gallery_items = GalleryListSerializer(many=True, read_only=True)

class MyCreationsSerializer(serializers.Serializer):
    """【/my/creations】 我的创作"""
    courses = CourseListSerializer(many=True, read_only=True)
    gallery_items = GalleryListSerializer(many=True, read_only=True)
    founded_communities = CommunityListSerializer(many=True, read_only=True)

class MyParticipationsSerializer(serializers.Serializer):
    """【/my/participations】 我的参与"""
    # 直接返回帖子列表
    posts = CommunityPostListSerializer(many=True, read_only=True)
class CourseCreateSerializer(serializers.ModelSerializer):
    """【创建课程用】的序列化器"""
    tags = TagsField(scope=Tag.TagScope.COURSE, required=False)
    class Meta:
        model = Course
        fields = ['id', 'title', 'description', 'coverImage', 'tags', 'pricePoints', 'is_vip_free','status']
        read_only_fields = ['id','status']

class GalleryItemCreateSerializer(serializers.ModelSerializer):
    """【创建作品用】的序列化器"""
    tags = TagsField(scope=Tag.TagScope.GALLERY, required=False)
    class Meta:
        model = GalleryItem
        fields = ['id','title', 'description', 'coverImage', 'workFile', 'tags', 'requiredPoints', 'prerequisiteWork', 'version', 'is_vip_free','status']
        read_only_fields = ['id','status']

class CommunityCreateSerializer(serializers.ModelSerializer):
    """【创建社群用】的序列化器 """
    tags = TagsField(scope=Tag.TagScope.COMMUNITY, required=False)  
    class Meta:
        model = Community
        fields = ['id','name', 'description', 'tags', 'coverImage', 'related_course', 'related_gallery_item','status']
        read_only_fields = ['id','status']

class ChapterSerializer(serializers.ModelSerializer):
    """
    用于创作者创建和编辑章节
    """
    class Meta:
        model = Chapter
        fields = ['id', 'title', 'videoUrl', 'order']
        read_only_fields = ['id', 'order']

class OptionSerializer(serializers.ModelSerializer):
    """用于 Exercise 的 'options' 字段的嵌套序列化器"""
    id = serializers.IntegerField(required=False) # 允许更新时传入ID
    class Meta:
        model = Option
        fields = ['id', 'text', 'is_correct']

class FillInBlankSerializer(serializers.ModelSerializer):
    """用于 Exercise 的 'fill_in_blanks' 字段的嵌套序列化器"""
    id = serializers.IntegerField(required=False) # 允许更新时传入ID
    class Meta:
        model = fill_in_blank
        fields = ['id', 'index_number', 'correct_answer', 'case_sensitive']

class ExerciseSerializer(serializers.ModelSerializer):
    """
    练习题的核心序列化器 (支持嵌套创建和更新)
    """
    options = OptionSerializer(many=True, required=False)
    fill_in_blanks = FillInBlankSerializer(many=True, required=False)

    class Meta:
        model = Exercise
        fields = [
            'id', 'chapter', 'type', 'prompt', 'explanation', 
            'image_upload', 'image_url', 
            'options', 'fill_in_blanks'
        ]
        # chapter 字段将由 View 在 perform_create 中自动设置
        read_only_fields = ['id', 'chapter']
        extra_kwargs = {
            'image_upload': {'required': False, 'allow_null': True},
            'image_url': {'required': False, 'allow_null': True},
            'explanation': {'required': False, 'allow_null': True},
        }

    def validate(self, data):
        """动态验证：确保题目类型和选项匹配"""
        q_type = data.get('type')
        options = data.get('options')
        blanks = data.get('fill_in_blanks')

        if q_type == Exercise.ExerciseTypeChoices.MULTIPLE_CHOICE:
            if not options:
                raise serializers.ValidationError("多选题必须至少有一个选项。")
            if blanks:
                raise serializers.ValidationError("多选题不应包含填空题答案。")
        
        elif q_type == Exercise.ExerciseTypeChoices.FILL_IN_THE_BLANK:
            if not blanks:
                raise serializers.ValidationError("填空题必须至少有一个答案。")
            if options:
                raise serializers.ValidationError("填空题不应包含多选题选项。")
        
        return data

    def _create_nested(self, exercise, options_data, blanks_data):
        """内部方法：创建嵌套的选项/填空"""
        if exercise.type == Exercise.ExerciseTypeChoices.MULTIPLE_CHOICE:
            for option_data in options_data:
                Option.objects.create(exercise=exercise, **option_data)
        elif exercise.type == Exercise.ExerciseTypeChoices.FILL_IN_THE_BLANK:
            for blank_data in blanks_data:
                fill_in_blank.objects.create(exercise=exercise, **blank_data)

    def create(self, validated_data):
        """处理嵌套创建"""
        options_data = validated_data.pop('options', [])
        blanks_data = validated_data.pop('fill_in_blanks', [])
        
        exercise = Exercise.objects.create(**validated_data)
        self._create_nested(exercise, options_data, blanks_data)
        return exercise

    def update(self, instance, validated_data):
        """处理嵌套更新 (先删后增，简化逻辑)"""
        options_data = validated_data.pop('options', [])
        blanks_data = validated_data.pop('fill_in_blanks', [])
        
        # 更新 Exercise 实例
        instance = super().update(instance, validated_data)

        if instance.type == Exercise.ExerciseTypeChoices.MULTIPLE_CHOICE:
            instance.options.all().delete()
            self._create_nested(instance, options_data, [])
        elif instance.type == Exercise.ExerciseTypeChoices.FILL_IN_THE_BLANK:
            instance.fill_in_blanks.all().delete()
            self._create_nested(instance, [], blanks_data)
            
        instance.save()
        return instance      
    
class ExerciseNestedSerializer(serializers.ModelSerializer):
    """(只读) 嵌套在章节中，用于列表显示的轻量级练习序列化器"""
    class Meta:
        model = Exercise
        fields = ['id', 'type', 'prompt']

class ChapterNestedSerializer(serializers.ModelSerializer):
    """(只读) 嵌套在课程中，包含练习列表的章节序列化器"""
    exercises = ExerciseNestedSerializer(many=True, read_only=True)
    
    class Meta:
        model = Chapter
        fields = ['id', 'title', 'videoUrl', 'order', 'exercises']
class CourseDetailSerializer(serializers.ModelSerializer):
    """
    (只读) 创作者获取课程详情 (GET) 时的序列化器
    """
    # 修复 Tags: 返回字段 "tags": ["标签名1", "标签名2"]
    tags = serializers.SlugRelatedField(
        many=True, 
        read_only=True, 
        slug_field='name'
    )

    chapters = ChapterNestedSerializer(many=True, read_only=True)
    author = UserSummarySerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Course
        fields = [
            'id', 'title', 'description', 'coverImage', 'pricePoints', 
            'is_vip_free', 'author', 'tags', 'status', 'status_display', 
            'chapters'
        ]