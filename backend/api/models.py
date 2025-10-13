from django.contrib.auth.models import AbstractUser
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils import timezone
from django.conf import settings
from django_bleach.models import BleachField

class User(AbstractUser):
    # 用户角色
    ROLE_CHOICES = [
        ('Student', 'Student'),
        ('Student-Artist', 'Student-Artist'),
        ('Admin', 'Admin'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='Student')

    # 账户状态
    ACCOUNT_STATUS_CHOICES = [
        ('active', 'active'),
        ('suspended', 'suspended'),
        ('frozen', 'frozen')
    ]
    accountStatus = models.CharField(max_length=20, choices=ACCOUNT_STATUS_CHOICES, default='active')

    # 积分状态
    POINTS_STATUS_CHOICES = [
        ('active', 'active'),
        ('frozen', 'frozen'),
    ]
    pointsStatus = models.CharField(max_length=20, choices=POINTS_STATUS_CHOICES, default='active')

    # 额外信息
    nickname = models.CharField(max_length=100, blank=True, null=True)
    avatarUrl = models.ImageField(upload_to='avatars/', blank=True, null=True,verbose_name="头像")
    currentPoints = models.IntegerField(default=0)
    
    # 注册时填写的分类信息
    ageGroup = models.CharField(max_length=20, blank=True, null=True)
    gender = models.CharField(max_length=20, blank=True, null=True)
    interests = models.JSONField(default=list, blank=True, null=True)
    
    # 移除 AbstractUser 中我们不直接使用的字段
    first_name = None
    last_name = None
    
    # 使用 email和phone 作为登录的主要凭证
    email = models.EmailField(unique=True,verbose_name="邮箱")
    phone = models.CharField(max_length=15, unique=True, verbose_name="手机号")
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username','phone'] # username 仍然需要，但 email 是登录凭证
    

    #课程进度字段
    completed_chapters = models.ManyToManyField(
        'Chapter', through='UserChapterCompletion',
        related_name='completed_by_users',
        blank=True
    )
    vip_expiration_date = models.DateTimeField(null=True, blank=True, verbose_name="VIP到期时间")
    @property
    def is_vip(self):
        """动态判断用户是否处于VIP状态"""
        if self.vip_expiration_date:
            return timezone.now() < self.vip_expiration_date
        return False
    def __str__(self):
        return self.email
    
class CertificationRequest(models.Model):
    """创作者资质认证申请模型"""
    class StatusChoices(models.TextChoices):
        PENDING = 'pending', '待审核'
        APPROVED = 'approved', '已批准'
        REJECTED = 'rejected', '已拒绝'

    # 申请人
    applicant = models.OneToOneField(User, on_delete=models.CASCADE, related_name='certification_request', verbose_name="申请人")
    
    # 申请状态
    status = models.CharField(max_length=20, choices=StatusChoices.choices, default=StatusChoices.PENDING, verbose_name="审核状态")
    
    # 上传的认证文件 
    certificationFile = models.FileField(upload_to='certifications/', verbose_name="认证文件")
    
    # 用户的备注信息
    notes = models.TextField(blank=True, null=True, verbose_name="备注")

    # 提交与处理时间
    submissionDate = models.DateTimeField(auto_now_add=True, verbose_name="提交日期")
    processedDate = models.DateTimeField(blank=True, null=True, verbose_name="处理日期")

    class Meta:
        verbose_name = "认证审批"
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"认证申请 - {self.applicant.username} ({self.get_status_display()})"
    

class Tag(models.Model):
    """标签模型"""
    class TagScope(models.TextChoices):
        COURSE = 'course', '课程'
        GALLERY = 'gallery', '画廊'
        COMMUNITY = 'community', '社群'
        CERTIFICATION = 'certification', '认证'
        PERSONALCENTER = 'personalcenter', '个人中心'

    name = models.CharField(max_length=100, verbose_name="标签")
    scope = models.CharField(max_length=20, choices=TagScope.choices, default=TagScope.COURSE, verbose_name="标签范围")
    creator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_tags', verbose_name="创建人")
    created_at = models.DateTimeField(auto_now_add=True, null=True, verbose_name="创建时间")

    def __str__(self):
        return f"{self.name} ({self.get_scope_display()})"
    class Meta:
        verbose_name = "标签"
        verbose_name_plural = verbose_name
        constraints = [
            models.UniqueConstraint(fields=['name', 'scope'], name='unique_name_scope_combination')
        ]
        ordering = ['scope', 'name'] 

# ===============================================
# =======         课程模块模型         =======
# ===============================================


class Course(models.Model):
    """课程模型"""
    class StatusChoices(models.TextChoices):
        DRAFT = 'draft', '草稿'
        PENDING_REVIEW = 'pending_review', '待审核'
        PUBLISHED = 'published', '已发布'
        REJECTED = 'rejected', '已驳回'

    title = models.CharField(max_length=200, verbose_name="课程标题")
    #description = models.TextField(verbose_name="课程描述")
    description = BleachField(verbose_name="课程描述") 
    coverImage = models.ImageField(upload_to='gallery_covers/', blank=True, null=True, verbose_name="封面图片")
    pricePoints = models.PositiveIntegerField(default=0, verbose_name="所需积分")
    is_vip_free = models.BooleanField(default=False, verbose_name="VIP免费")
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='courses_authored', verbose_name="作者")
    tags = models.ManyToManyField(
        Tag, 
        limit_choices_to={'scope': Tag.TagScope.COURSE}, # 关键点在这里！
        related_name='courses', 
        blank=True, 
        verbose_name="课程标签"
    )
    status = models.CharField(max_length=20, choices=StatusChoices.choices, default=StatusChoices.DRAFT, verbose_name="课程状态")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    subscribers = models.ManyToManyField(User, related_name='subscribed_courses', blank=True, through='Subscription')
    collectors = models.ManyToManyField(User, related_name='collected_courses', blank=True, through='Collection')
   
    def __str__(self):
        return self.title
    class Meta:
        verbose_name = "课程"
        verbose_name_plural = verbose_name

class Chapter(models.Model):
    """章节模型"""
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='chapters', verbose_name="所属课程")
    title = models.CharField(max_length=200, verbose_name="章节标题")
    order = models.PositiveIntegerField(default=0, verbose_name="章节顺序")
    videoUrl = models.URLField(max_length=500, blank=True, null=True, verbose_name="视频链接")
   
    class Meta:
        verbose_name = "章节"
        verbose_name_plural = verbose_name
        ordering = ['order']

    def __str__(self):
        return f"{self.course.title} - Ch.{self.order} {self.title}"

class Option(models.Model):
    """选择题选项模型"""
    exercise = models.ForeignKey('Exercise', on_delete=models.CASCADE, related_name='options')
    text = models.CharField(max_length=500, verbose_name="选项内容")
    is_correct = models.BooleanField(default=False, verbose_name="是否为正确答案") # 新增字段

    def __str__(self):
        return self.text
    class Meta:
        verbose_name = "选项"
        verbose_name_plural = verbose_name


class Exercise(models.Model):
    """练习题模型"""
    class ExerciseTypeChoices(models.TextChoices):
        MULTIPLE_CHOICE = 'multiple-choice', '多选题'
        FILL_IN_THE_BLANK = 'fill-in-the-blank', '填空题'

    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name='exercises', verbose_name="所属章节")
    type = models.CharField(max_length=20, choices=ExerciseTypeChoices.choices, verbose_name="题目类型")
    #prompt = models.TextField(verbose_name="题干")
    prompt = BleachField(verbose_name="题干")
    #explanation = models.TextField(blank=True, null=True, verbose_name="答案解析")
    explanation = BleachField(blank=True, null=True, verbose_name="答案解析")
    image_upload = models.ImageField(upload_to='exercises/', blank=True, null=True, verbose_name="上传图片")
    image_url = models.URLField(blank=True, null=True, verbose_name="图片链接")
    
    # 恢复 answer 字段，专门给填空题使用
    answer = models.JSONField(
        blank=True, 
        null=True, 
        verbose_name="填空题答案",
        help_text="【仅供填空题使用】请在此处输入答案数组, 例如: [\"答案A\", \"答案B\"]"
    )
    class Meta:
        verbose_name = "练习"
        verbose_name_plural = verbose_name
    
    def __str__(self):
        return f"{self.get_type_display()} for {self.chapter.title}: {self.prompt[:30]}..."

class Subscription(models.Model):
    """课程订阅关系模型"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)


    subscribed_at = models.DateTimeField(auto_now_add=True)
    last_updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(blank=True, null=True) 

    class Meta:
        verbose_name = "订阅"
        verbose_name_plural = verbose_name
        unique_together = ('user', 'course')

class Collection(models.Model):
    """课程收藏关系模型"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    collected_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "收藏"
        verbose_name_plural = verbose_name
        unique_together = ('user', 'course')


class UserChapterCompletion(models.Model):
    """记录用户完成章节的中间表"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    chapter = models.ForeignKey('Chapter', on_delete=models.CASCADE)
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "完成章节"
        verbose_name_plural = verbose_name
        unique_together = ('user', 'chapter')


# ===============================================
# =======         画廊模块模型         =======
# ===============================================
class GalleryItem(models.Model):
    """画廊作品模型"""
    class StatusChoices(models.TextChoices):
        DRAFT = 'draft', '草稿'
        PENDING_REVIEW = 'pending_review', '待审核'
        PUBLISHED = 'published', '已发布'
        REJECTED = 'rejected', '已驳回'
        ARCHIVED = 'archived', '已归档'

    title = models.CharField(max_length=200, verbose_name="作品标题")
    #description = models.TextField(verbose_name="作品描述")
    description = BleachField(verbose_name="作品描述") 
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='gallery_items_authored', verbose_name="作者")
    
    coverImage = models.ImageField(upload_to='gallery_covers/', blank=True, null=True, verbose_name="封面图片")
    workFile = models.FileField(upload_to='gallery_files/', verbose_name="作品文件(压缩包等)") # 用于存储实际的作品文件
    is_vip_free = models.BooleanField(default=False, verbose_name="VIP免费")
    tags = models.ManyToManyField(
        Tag, 
        limit_choices_to={'scope': Tag.TagScope.GALLERY}, # 关键点在这里！
        related_name='gallery_items', 
        blank=True, 
        verbose_name="画廊标签"
    )
    status = models.CharField(max_length=20, choices=StatusChoices.choices, default=StatusChoices.DRAFT, verbose_name="作品状态")
    
    requiredPoints = models.PositiveIntegerField(default=0, verbose_name="所需积分")
    
    # 前置作品，指向自身，形成依赖关系
    prerequisiteWork = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="往期版本")

    # 用于展示的只读字段
    version = models.CharField(max_length=20, blank=True, null=True, verbose_name="版本号")
    rating = models.FloatField(default=0.0, verbose_name="平均评分")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    collectors = models.ManyToManyField(User, related_name='collected_gallery_items', blank=True, through='GalleryCollection')
    class Meta:
        verbose_name = "画廊作品"
        verbose_name_plural = verbose_name
    
    def __str__(self):
        return self.title

class GalleryCollection(models.Model):
    """画廊作品收藏关系模型"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    gallery_item = models.ForeignKey(GalleryItem, on_delete=models.CASCADE)
    collected_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "收藏画廊作品"
        verbose_name_plural = verbose_name
        unique_together = ('user', 'gallery_item')

class GalleryDownloadRecord(models.Model):
    """画廊作品下载记录模型"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    gallery_item = models.ForeignKey(GalleryItem, on_delete=models.CASCADE)
    downloaded_at = models.DateTimeField(auto_now_add=True)
    points_spent = models.PositiveIntegerField()
    class Meta:
        verbose_name = "画廊作品下载记录"
        verbose_name_plural = verbose_name
    
    def __str__(self):
        return f"{self.user.username} downloaded {self.gallery_item.title}"

class GalleryItemRating(models.Model):
    """画廊作品评分记录模型"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    gallery_item = models.ForeignKey(GalleryItem, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField() # 1-5
    rated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "画廊作品评分记录"
        verbose_name_plural = verbose_name
        unique_together = ('user', 'gallery_item')


# ===============================================
# =======         社群模块模型         =======
# ===============================================

class Community(models.Model):
    """社群（板块）模型"""
    name = models.CharField(max_length=100, unique=True, verbose_name="社群名称")
    description = BleachField(blank=True, null=True, verbose_name="社群描述")
    founder = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='founded_communities', verbose_name="创始人")
    assistants = models.ManyToManyField(User, related_name='assisted_communities', blank=True, verbose_name="创始人助手")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    members = models.ManyToManyField(User, related_name='joined_communities', blank=True, verbose_name="社群成员")
    coverImage = models.ImageField(upload_to='community_covers/', blank=True, null=True, verbose_name="封面图片")
    related_course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True, related_name='community_access', verbose_name="关联课程")
    related_gallery_item = models.ForeignKey(GalleryItem, on_delete=models.SET_NULL, null=True, blank=True, related_name='community_access', verbose_name="关联画廊作品")
    tags = models.ManyToManyField(
        Tag, 
        limit_choices_to={'scope': Tag.TagScope.COMMUNITY}, 
        related_name='communities', 
        blank=True, 
        verbose_name="社群标签"
    )
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "社群板块"
        verbose_name_plural = verbose_name

class CommunityPost(models.Model):
    """社群帖子模型"""
    class StatusChoices(models.TextChoices):
        PENDING_REVIEW = 'pending_review', '待审核'
        PUBLISHED = 'published', '已发布'
        CLOSED = 'closed', '已关闭'
        REJECTED = 'rejected', '已驳回'

    community = models.ForeignKey(Community, on_delete=models.CASCADE, related_name='posts', verbose_name="所属社群")
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='community_posts', verbose_name="发帖人")
    likes = models.ManyToManyField(User, related_name='liked_posts', blank=True, verbose_name="点赞用户")
    title = models.CharField(max_length=200, verbose_name="帖子标题")
    #content = models.TextField(verbose_name="帖子内容")
    content = BleachField(verbose_name="帖子内容")
    status = models.CharField(max_length=20, choices=StatusChoices.choices, default=StatusChoices.PUBLISHED, verbose_name="帖子状态")
    rewardPoints = models.PositiveIntegerField(default=0, verbose_name="悬赏积分")
    
    # 关联到被采纳的最佳答案
    best_answer = models.OneToOneField('CommunityReply', on_delete=models.SET_NULL, null=True, blank=True, related_name='best_for_post', verbose_name="最佳答案")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="发布时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "社群帖子"
        verbose_name_plural = verbose_name

class CommunityReply(models.Model):
    """社群回帖模型"""
    post = models.ForeignKey(CommunityPost, on_delete=models.CASCADE, related_name='replies', verbose_name="所属帖子")
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='community_replies', verbose_name="回帖人")
    #content = models.TextField(verbose_name="回复内容")
    content = BleachField(verbose_name="回复内容")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="回复时间")
    likes = models.ManyToManyField(User, related_name='liked_replies', blank=True, verbose_name="点赞用户")
    def __str__(self):
        return f"Reply by {self.author.username} on {self.post.title}"

    class Meta:
        verbose_name = "社群回帖"
        verbose_name_plural = verbose_name

# ===============================================
# =======         积分流水模型         =======
# ===============================================
class PointsTransaction(models.Model):
    """积分流水记录模型"""
    class TransactionType(models.TextChoices):
        COMMUNITY_REWARD = 'community_reward', '悬赏帖子'
        PURCHASE = 'purchase', '课程订阅'
        DOWNLOAD = 'download', '作品下载'
        ACTIVITY_REWARD = 'activity_reward', '活动积分'
        ADMIN_ADJUST = 'admin_adjust', '管理员调整'
        INITIAL = 'initial', '初始积分'
        REFUND = 'refund', '积分退回'
        

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='points_transactions', verbose_name="用户")
    amount = models.IntegerField(verbose_name="变动数额") # 正数表示增加，负数表示扣除
    description = models.CharField(max_length=255, verbose_name="变动原因")
    transaction_type = models.CharField(max_length=20, choices=TransactionType.choices, verbose_name="交易类型")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="发生时间")
    
    content_type = models.ForeignKey(
        ContentType, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        verbose_name="关联内容类型"
    )
    object_id = models.PositiveIntegerField(
        null=True, 
        blank=True, 
        verbose_name="关联内容ID"
    )
    content_object = GenericForeignKey('content_type', 'object_id')
    
    operator = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='operated_points_transactions', 
        verbose_name="操作者"
    )

    def __str__(self):
        sign = '+' if self.amount > 0 else ''
        return f"{self.user.username}: {sign}{self.amount} points for {self.get_transaction_type_display()}"

    class Meta:
        verbose_name = "积分流水"
        verbose_name_plural = verbose_name
        ordering = ['-created_at']


# ===============================================
# =======         VIP状态模型         =======
# ===============================================

class VipPlan(models.Model):
    """VIP 购买套餐模型"""
    name = models.CharField(max_length=100, verbose_name="套餐名称") # 例如 "月度会员"
    duration_days = models.PositiveIntegerField(verbose_name="有效天数") # 例如 30
    price_points = models.PositiveIntegerField(verbose_name="所需积分")

    def __str__(self):
        return f"{self.name} ({self.duration_days}天)"
    
    class Meta:
        verbose_name = "VIP套餐"
        verbose_name_plural = verbose_name

# ===============================================
# =======        审核中心 代理模型        =======
# ===============================================

# --- 创建一个自定义管理器，用于筛选待审核内容 ---
class PendingReviewManager(models.Manager):
    def get_queryset(self):
        # 根据模型的不同，使用不同的状态字段进行筛选
        if self.model.__name__ == 'PendingCertificationRequest':
            return super().get_queryset().filter(status='pending')
        else:
            return super().get_queryset().filter(status='pending_review')

# --- 为每种需要审核的内容创建代理模型 ---

class PendingCourse(Course):
    objects = PendingReviewManager()
    class Meta:
        proxy = True
        verbose_name = '待审核课程'
        verbose_name_plural = '待审核课程'

class PendingGalleryItem(GalleryItem):
    objects = PendingReviewManager()
    class Meta:
        proxy = True
        verbose_name = '待审核作品'
        verbose_name_plural = '待审核作品'

class PendingCommunityPost(CommunityPost):
    objects = PendingReviewManager()
    class Meta:
        proxy = True
        verbose_name = '待审核帖子'
        verbose_name_plural = '待审核帖子'

class PendingCertificationRequest(CertificationRequest):
    objects = PendingReviewManager()
    class Meta:
        proxy = True
        verbose_name = '待处理认证'
        verbose_name_plural = '待处理认证'
# ===============================================
# =======         站内信模型           =======
# ===============================================

class MessageThread(models.Model):
    """
    站内信会话主题模型。
    它像一个“文件夹”，聚合了所有相关的消息。
    """
    class ThreadType(models.TextChoices):
        NOTIFICATION = 'notification', '系统通知'
        CONVERSATION = 'conversation', '用户会话'

    subject = models.CharField(max_length=255, verbose_name="主题")
    thread_type = models.CharField(
        max_length=20, 
        choices=ThreadType.choices, 
        default=ThreadType.CONVERSATION, 
        verbose_name="会话类型"
    )
    participants = models.ManyToManyField(User, related_name='message_threads', verbose_name="所有参与者")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

 
    content_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    def __str__(self):
        return self.subject

    class Meta:
        verbose_name = "站内信会话"
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

class Message(models.Model):
    """
    单条站内信模型。
    它像文件夹里的一封“信件”。
    """
    thread = models.ForeignKey(MessageThread, on_delete=models.CASCADE, related_name='messages', verbose_name="所属会话")
    sender = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='sent_messages', verbose_name="发信人")
    recipient = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='received_direct_messages', verbose_name="收件人")
    content = BleachField(verbose_name="内容")
    cc_recipient = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='cc_messages', 
        verbose_name="抄送人"
    )
    sent_at = models.DateTimeField(auto_now_add=True, verbose_name="发送时间")

    def __str__(self):
        return f"Reply from {self.sender} to {self.recipient} in thread '{self.thread.subject}'"

    class Meta:
        verbose_name = "单条消息"
        verbose_name_plural = verbose_name
        ordering = ['sent_at']