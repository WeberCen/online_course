from django_elasticsearch_dsl.registries import registry
from django_elasticsearch_dsl import Document, fields
from django.contrib.auth.models import User # 假设 author/founder 指向标准 User
from api.models import Tag, CommunityPost ,Course,GalleryItem

# ==================
# 1. 课程索引
# ==================
@registry.register_document
class CourseDocument(Document):
    doc_type = fields.KeywordField()

    # 关联作者 (外键)
    author = fields.ObjectField(properties={
        'name': fields.TextField(), 
    })

    # 关联标签 (多对多)
    tags = fields.ObjectField(properties={
        'name': fields.TextField(),
    }, multi=True)

    points = fields.IntegerField()

    class Index:
        name = 'courses' # ES 索引的名称

    class Django:
        model = Course # 绑定的 Django 模型
        fields = ['title','is_vip_free','created_at']
        related_models = [User, Tag]

    
    def prepare_doc_type(self, instance):
        return 'course'
    def get_instances_from_related(self, related_instance):
        """当 User 或 Tag 变化时，找到所有关联的课程"""
        if isinstance(related_instance, User):
            # 假设 Course.author 的 related_name 是 'course_set'
            return related_instance.course_set.all() 
        if isinstance(related_instance, Tag):
            # 假设 Course.tags 的 related_name 是 'course_set'
            return related_instance.course_set.all()
    def prepare_points(self, instance):    
        return instance.pricePoints

# ==================
# 2. 画廊索引
# ==================
@registry.register_document
class GalleryItemDocument(Document): 
    doc_type = fields.KeywordField()

    # 关联作者 (外键)
    author = fields.ObjectField(properties={ # <-- 已修正 (从 artist 改为 author)
        'name': fields.TextField(),
    })

    tags = fields.ObjectField(properties={
        'name': fields.TextField(),
    }, multi=True)

    points = fields.IntegerField()

    class Index:
        name = 'gallery'

    class Django:
        model = GalleryItem 
        fields = ['title','is_vip_free','created_at','rating']
        related_models = [User, Tag]
    def prepare_doc_type(self, instance):
        return 'gallery'
    def get_instances_from_related(self, related_instance):
        """当 User 或 Tag 变化时，找到所有关联的画廊作品"""
        if isinstance(related_instance, User):
            # 假设 GalleryItem.author 的 related_name 是 'galleryitem_set'
            return related_instance.galleryitem_set.all() 
        if isinstance(related_instance, Tag):
            # 假设 GalleryItem.tags 的 related_name 是 'galleryitem_set'
            return related_instance.galleryitem_set.all()
    def prepare_points(self, instance):    
        return instance.requiredPoints

# ==================
# 3. 社群帖子索引
# ==================
@registry.register_document
class CommunityPostDocument(Document): # <-- 已修正
    doc_type = fields.KeywordField() 

    # 关联作者 (外键)
    author = fields.ObjectField(properties={
        'name': fields.TextField(),
    })

    tags = fields.ObjectField(properties={
        'name': fields.TextField(),
    }, multi=True)
    
    points = fields.IntegerField()
    likes_count = fields.IntegerField()

    class Index:
        name = 'community_posts' 

    class Django:
        model = CommunityPost 
        fields = [
            'title','created_at'
            # 'content', # 如果你的帖子模型有 content 字段且需要被搜
        ]
        related_models = [User, Tag]
    def prepare_doc_type(self, instance):
        return 'community'
    
    def get_instances_from_related(self, related_instance):
        """当 User 或 Tag 变化时，找到所有关联的帖子"""
        if isinstance(related_instance, User):
            # 假设 CommunityPost.author 的 related_name 是 'communitypost_set'
            return related_instance.communitypost_set.all() 
        if isinstance(related_instance, Tag):
            # 假设 CommunityPost.tags 的 related_name 是 'communitypost_set'
            return related_instance.communitypost_set.all()
    def prepare_points(self, instance):    
        return instance.rewardPoints
    def prepare_likes_count(self, instance):
        return instance.likes.count()