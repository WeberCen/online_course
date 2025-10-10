# backend/api/serializers.py

from rest_framework import serializers
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User,CertificationRequest,Course,Chapter,Exercise
from .models import (Subscription, Collection, 
                     GalleryItem, GalleryCollection, GalleryDownloadRecord, 
                     GalleryItemRating,Community,CommunityPost,CommunityReply,
                     Message,MessageThread)
 
class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    password2 = serializers.CharField(write_only=True, required=True, label="Confirm password", style={'input_type': 'password'})

    class Meta:
        model = User
        fields = ['username', 'email', 'phone', 'password', 'password2', 'nickname', 'ageGroup', 'gender', 'interests']
        extra_kwargs = {
            'email': {'required': True},
            'phone': {'required': True}
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
        # 创建用户实例，注意要对密码进行哈希加密
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            phone=validated_data['phone'],
            nickname=validated_data.get('nickname', ''),
            ageGroup=validated_data.get('ageGroup'),
            gender=validated_data.get('gender'),
            interests=validated_data.get('interests', [])
        )
        user.set_password(validated_data['password'])
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
            'id', 'username', 'email', 'phone', 'nickname', 'avatarUrl',
            'currentPoints', 'role', 'ageGroup', 'gender', 'interests',
            'accountStatus', 'pointsStatus'
        ]
        # 设置某些字段为只读，防止用户通过此接口修改它们
        read_only_fields = [
            'id', 'username', 'email', 'phone', 'currentPoints', 'role',
            'accountStatus', 'pointsStatus'
        ]
class AvatarUpdateSerializer(serializers.ModelSerializer):
    """
    专门用于头像更新的序列化器
    """
    class Meta:
        model = User
        fields = ['avatarUrl']

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
        fields = ['id', 'username', 'nickname', 'avatarUrl']

# ===============================================
# =======         课程模块 Serializers     =======
# ===============================================

class ExerciseSerializer(serializers.ModelSerializer):
    options = serializers.StringRelatedField(many=True, read_only=True)
    class Meta:
        model = Exercise
        fields = ['id', 'prompt', 'type', 'options'] 

class ChapterSerializer(serializers.ModelSerializer):
    """章节信息的序列化器（包含练习题）"""
    exercises = ExerciseSerializer(many=True, read_only=True)

    class Meta:
        model = Chapter
        fields = ['id', 'title', 'order', 'videoUrl', 'exercises']

class CourseListSerializer(serializers.ModelSerializer):
    """用于课程列表的序列化器"""
    author = UserSummarySerializer(read_only=True)
    chapterCount = serializers.SerializerMethodField()
    tags = serializers.StringRelatedField(many=True, read_only=True) # 将标签显示为名称

    class Meta:
        model = Course
        fields = ['id', 'title', 'description', 'coverImage', 'pricePoints', 'author', 'tags', 'chapterCount', 'status']

    def get_chapterCount(self, obj):
        # 计算该课程下的章节总数
        return obj.chapters.count()

class CourseDetailSerializer(CourseListSerializer):
    """
    用于课程详情的序列化器，继承自列表序列化器
    并额外包含完整的章节列表
    """
    chapters = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()
    is_collected = serializers.SerializerMethodField()

    class Meta(CourseListSerializer.Meta):
        fields = CourseListSerializer.Meta.fields + ['chapters', 'is_subscribed', 'is_collected']
    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        if user and user.is_authenticated:
            return Subscription.objects.filter(user=user, course=obj).exists()
        return False

    def get_is_collected(self, obj):
        user = self.context['request'].user
        if user and user.is_authenticated:
            return Collection.objects.filter(user=user, course=obj).exists()
        return False
        
    def get_chapters(self, obj):
        is_subscribed = self.get_is_subscribed(obj)
        user = self.context['request'].user

        # 游客、未订阅用户，只看前三章
        if not is_subscribed and (not hasattr(user, 'is_staff') or not user.is_staff):
            chapters_queryset = obj.chapters.all()[:3]
        else: # 已订阅用户或管理员，看全部
            chapters_queryset = obj.chapters.all()
        
        return ChapterSerializer(chapters_queryset, many=True, context=self.context).data
    
    
class SimpleCourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ['id', 'title', 'coverImage']

class SimpleChapterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chapter
        fields = ['id', 'title', 'order']

class CourseProgressSerializer(serializers.Serializer):
    """课程进度序列化器"""   
    # 关联对象信息
    course = SimpleCourseSerializer(read_only=True)
    
    # 核心进度量化
    completedChapters = serializers.IntegerField()
    totalChapters = serializers.IntegerField()
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
        completed = obj.get('completedChapters', 0)
        total = obj.get('totalChapters', 0)
        
        if total > 0:
            return round((completed / total) * 100)
        return 0


class AnswerSerializer(serializers.Serializer):
    """单个答案的序列化器"""
    exerciseId = serializers.IntegerField()
    userAnswer = serializers.JSONField()
     
class ExerciseSubmissionSerializer(serializers.Serializer):
    """整个章节练习提交的序列化器"""
    answers = AnswerSerializer(many=True)



# ===============================================
# =======         画廊模块 Serializers     =======
# ===============================================

class GalleryListSerializer(serializers.ModelSerializer):
    """用于画廊作品列表的序列化器"""
    author = UserSummarySerializer(read_only=True)
    tags = serializers.StringRelatedField(many=True, read_only=True)
    
    class Meta:
        model = GalleryItem
        fields = [
            'id', 'title', 'description', 'coverImage', 'author', 
            'tags', 'requiredPoints', 'rating', 'version'
        ]

class GalleryDetailSerializer(GalleryListSerializer):
    """
    用于画廊作品详情的序列化器，并包含当前用户的下载，收藏状态
    """
    is_collected = serializers.SerializerMethodField()
    is_downloaded = serializers.SerializerMethodField() 

    class Meta(GalleryListSerializer.Meta):
        fields = GalleryListSerializer.Meta.fields + ['is_collected', 'is_downloaded', 'workFile']

    def get_is_collected(self, obj):
        user = self.context.get('request').user
        if user and user.is_authenticated:
            return GalleryCollection.objects.filter(user=user, gallery_item=obj).exists()
        return False

    # 新增的方法，用于计算 is_downloaded 的值
    def get_is_downloaded(self, obj):
        user = self.context.get('request').user
        if user and user.is_authenticated:
            return GalleryDownloadRecord.objects.filter(user=user, gallery_item=obj).exists()
        return False
    
# ===============================================
# =======         社群模块 Serializers     =======
# ===============================================
class CommunityListSerializer(serializers.ModelSerializer):
    """【第一级页面使用】：用于“社群板块列表”"""
    founder = UserSummarySerializer(read_only=True)
    post_count = serializers.SerializerMethodField()
    tags = serializers.StringRelatedField(many=True, read_only=True) # <-- 修正 1: tags

    class Meta:
        model = Community
        fields = ['id', 'name', 'description', 'founder', 'coverImage', 'tags', 'post_count'] # <-- 修正 2: tags, 不重复

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
        fields = ['id', 'title', 'author', 'rewardPoints', 'created_at', 'reply_count']

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