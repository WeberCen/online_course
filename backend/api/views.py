# backend/api/views.py
import random
import json
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import generics, status,mixins,serializers
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from django.db.models import Count, Q
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404,render
from django.utils import timezone
from datetime import timedelta
from rest_framework.decorators import action
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db.models import Prefetch, OuterRef, Subquery, Max
from .permissions import CanPostOrReplyInCommunity, IsCreator
from .tasks import send_verification_code_email
from .serializers import (
    UserRegisterSerializer, UserProfileSerializer, UserSummarySerializer,UserLoginSerializer,
    ChangePhoneInitiateSerializer, ChangePhoneVerifyNewSerializer, ChangePhoneCommitSerializer,
    ChangeEmailInitiateSerializer, ChangeEmailVerifyNewSerializer, ChangeEmailCommitSerializer,
    CertificationRequestSerializer, EditorImageSerializer,CourseListSerializer, CourseDetailSerializer,
    PasswordResetRequestSerializer, PasswordResetConfirmSerializer,
    CourseProgressSerializer, ExerciseSubmissionSerializer,
    GalleryListSerializer, GalleryDetailSerializer, CourseCreateSerializer,GalleryItemCreateSerializer,CommunityCreateSerializer,
    CommunityListSerializer, CommunityPostListSerializer, CommunityPostDetailSerializer,
    CommunityPostCreateSerializer,CommunityReplyCreateSerializer,
    MessageCreateSerializer,MessageThreadListSerializer,MessageThreadDetailSerializer,
    MyCollectionsSerializer,MySupportedSerializer,MyCreationsSerializer,MyParticipationsSerializer)
from .models import (CertificationRequest,Course,Chapter,
                     Subscription,Collection,Exercise,UserChapterCompletion,
                     GalleryItem,GalleryCollection,GalleryDownloadRecord,
                     Community,CommunityPost,CommunityReply,
                     User,Tag,Message,MessageThread)


User = get_user_model() # 获取当前项目使用的 User 模型

class UserRegisterView(generics.CreateAPIView):
    """
    用户注册视图
    """
    serializer_class = UserRegisterSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        
        # 注册成功后，返回一个简单的成功消息
        return Response(
            {"message": "User registered successfully."},
            status=status.HTTP_201_CREATED,
            headers=headers
        )

class UserLoginView(generics.GenericAPIView):
    serializer_class = UserLoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        tokens = serializer.get_tokens_for_user(user)
        
        # 可以在这里返回更多用户信息
        user_data = UserProfileSerializer(user).data
        
        return Response({
            'user': user_data,
            'tokens': tokens
        }, status=status.HTTP_200_OK)
    
class AvatarUpdateView(generics.UpdateAPIView):
    """
    处理用户头像上传
    """
    # 这个视图只用于返回更新后的用户信息，核心逻辑在 update 方法中
    serializer_class = UserProfileSerializer 
    permission_classes = [IsAuthenticated]
    # 指定解析器，以支持 multipart/form-data 格式的请求
    parser_classes = [MultiPartParser, FormParser]

    def get_object(self):
        return self.request.user

    def put(self, request, *args, **kwargs):
        user = self.get_object()
        # 'avatarFile' 必须与前端/Postman 发送请求时使用的字段名一致
        avatar_file = request.data.get('avatarFile') 

        if not avatar_file:
            return Response({"error": "No avatar file provided."}, status=status.HTTP_400_BAD_REQUEST)

        # 直接更新用户的 avatarUrl 字段
        user.avatarUrl = avatar_file
        user.save()

        # 使用 UserProfileSerializer 序列化并返回更新后的用户数据
        serializer = self.get_serializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # 我们只允许 PUT 或 POST (在此视图中视为更新)，不允许 PATCH
    def patch(self, request, *args, **kwargs):
        return self.put(request, *args, **kwargs)
    
class PasswordResetRequestView(generics.GenericAPIView):
    """
    处理发送密码重置验证码的请求
    """
    serializer_class = PasswordResetRequestSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']

        # 1. 生成一个6位数的随机验证码
        code = str(random.randint(100000, 999999))

        # 2. 将验证码存入 Redis 缓存，有效期10分钟
        #    我们使用一个带前缀的 key 来避免冲突
        cache.set(f'password_reset_{email}', code, timeout=600)

        # 3. 调用 Celery 异步任务发送邮件
        send_verification_code_email.delay(email, code)

        return Response(
            {"message": "If an account with this email exists, a password reset code has been sent."},
            status=status.HTTP_200_OK
        )
class PasswordResetConfirmView(generics.GenericAPIView):
    """
    处理使用验证码重置密码的请求
    """
    serializer_class = PasswordResetConfirmSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        code = serializer.validated_data['code']
        new_password = serializer.validated_data['newPassword']

        # 1. 从 Redis 缓存中获取正确的验证码
        cached_code = cache.get(f'password_reset_{email}')

        # 2. 验证验证码
        if cached_code is None:
            return Response({"error": "Verification code has expired or is invalid."}, status=status.HTTP_400_BAD_REQUEST)
        
        if cached_code != code:
            return Response({"error": "Invalid verification code."}, status=status.HTTP_400_BAD_REQUEST)

        # 3. 验证通过，获取用户并设置新密码
        try:
            user = User.objects.get(email=email)
            user.set_password(new_password)
            user.save()
            
            # 4. 密码重置成功后，删除缓存中的验证码，防止重复使用
            cache.delete(f'password_reset_{email}')

            return Response({"message": "Password has been reset successfully."}, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            # 理论上 serializer 已经检查过用户存在，但这里做一个双重保障
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        

class ChangePhoneInitiateView(generics.GenericAPIView):
    """更换手机号 - 步骤1：向已绑定的邮箱发送验证码以验证身份"""
    serializer_class = ChangePhoneInitiateSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        if not user.email:
            return Response({"error": "No email address is associated with this account for verification."}, status=status.HTTP_400_BAD_REQUEST)
        
        code = str(random.randint(100000, 999999))
        cache.set(f'change_phone_identity_{user.id}', code, timeout=600)
        
        # 新逻辑：将身份验证码发送到用户的邮箱
        send_verification_code_email.delay(user.email, code)

        return Response({"message": "Verification code sent to your registered email address."}, status=status.HTTP_200_OK)

class ChangePhoneVerifyNewView(generics.GenericAPIView):
    """更换手机号 - 步骤2：向新手机发送验证码"""
    serializer_class = ChangePhoneVerifyNewSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_phone = serializer.validated_data['newPhone']
        
        code = str(random.randint(100000, 999999))
        cache.set(f'change_phone_new_{request.user.id}', code, timeout=600)
        
        print(f"--- SIMULATING SMS --- To new phone: {new_phone}, Code: {code} ---")
        
        return Response({"message": "Verification code sent to the new phone number."}, status=status.HTTP_200_OK)

class ChangePhoneCommitView(generics.GenericAPIView):
    """更换手机号 - 步骤3：提交所有信息完成更换"""
    serializer_class = ChangePhoneCommitSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        user = request.user
        identity_code_cached = cache.get(f'change_phone_identity_{user.id}')
        new_code_cached = cache.get(f'change_phone_new_{user.id}')

        if not identity_code_cached or identity_code_cached != data['identityCode']:
            return Response({"error": "Invalid identity verification code from email."}, status=status.HTTP_400_BAD_REQUEST)
        
        if not new_code_cached or new_code_cached != data['newCode']:
            return Response({"error": "Invalid new phone verification code."}, status=status.HTTP_400_BAD_REQUEST)
        
        # 检查新手机是否已被占用
        if User.objects.filter(phone=data['newPhone']).exclude(pk=user.pk).exists():
            return Response({"error": "This phone number is already in use."}, status=status.HTTP_409_CONFLICT)
        
        # 正式更新用户手机号
        user.phone = data['newPhone'] 
        user.save()
        
        cache.delete(f'change_phone_identity_{user.id}')
        cache.delete(f'change_phone_new_{user.id}')
        
        return Response({"message": "Phone number has been changed successfully."}, status=status.HTTP_200_OK)

class ChangeEmailInitiateView(generics.GenericAPIView):
    """更换邮箱 - 步骤1：向已绑定的手机发送验证码以验证身份"""
    serializer_class = ChangeEmailInitiateSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        if not user.phone:
            return Response({"error": "No phone number is associated with this account for verification."}, status=status.HTTP_400_BAD_REQUEST)
        
        code = str(random.randint(100000, 999999))
        cache.set(f'change_email_identity_{user.id}', code, timeout=600)
        
        # 新逻辑：将身份验证码发送到用户的手机（模拟）
        print(f"--- SIMULATING SMS --- To old phone: {user.phone}, Code: {code} ---")
        
        return Response({"message": "Verification code sent to your registered phone number."}, status=status.HTTP_200_OK)

class ChangeEmailVerifyNewView(generics.GenericAPIView):
    """更换邮箱 - 步骤2：向新邮箱发送验证码"""
    serializer_class = ChangeEmailVerifyNewSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_email = serializer.validated_data['newMail']
        
        code = str(random.randint(100000, 999999))
        cache.set(f'change_email_new_{request.user.id}', code, timeout=600)
        
        send_verification_code_email.delay(new_email, code)
        
        return Response({"message": "Verification code sent to the new email address."}, status=status.HTTP_200_OK)

class ChangeEmailCommitView(generics.GenericAPIView):
    """更换邮箱 - 步骤3：提交所有信息完成更换"""
    serializer_class = ChangeEmailCommitSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        user = request.user
        identity_code_cached = cache.get(f'change_email_identity_{user.id}')
        new_code_cached = cache.get(f'change_email_new_{user.id}')

        if not identity_code_cached or identity_code_cached != data['identityCode']:
            return Response({"error": "Invalid identity verification code from phone."}, status=status.HTTP_400_BAD_REQUEST)
        
        if not new_code_cached or new_code_cached != data['newCode']:
            return Response({"error": "Invalid new email verification code."}, status=status.HTTP_400_BAD_REQUEST)
        
        if User.objects.filter(email=data['newMail']).exclude(pk=user.pk).exists():
            return Response({"error": "This email address is already in use."}, status=status.HTTP_409_CONFLICT)
        
        user.email = data['newMail']
        user.save()
        
        cache.delete(f'change_email_identity_{user.id}')
        cache.delete(f'change_email_new_{user.id}')
        
        return Response({"message": "Email address has been changed successfully."}, status=status.HTTP_200_OK)

class CertificationSubmitView(generics.CreateAPIView):
    """
    处理创作者资质认证申请的提交
    """
    queryset = CertificationRequest.objects.all()
    serializer_class = CertificationRequestSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser] # 支持文件上传

    def perform_create(self, serializer):
        # 在创建对象时，自动将申请人设置为当前登录的用户
        serializer.save(applicant=self.request.user)

class EditorImageView(generics.CreateAPIView):
    """
    为富文本编辑器提供图片上传功能
    """
    serializer_class = EditorImageSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        image = serializer.validated_data['image']
        
        # 在这里，我们可以将图片保存到任何地方，比如模型字段或直接保存
        # 为了简单，我们直接返回图片的访问 URL
        image_url = request.build_absolute_uri(image.url)

        return Response({'imageUrl': image_url}, status=status.HTTP_201_CREATED)


# ===============================================
# =======          课程模块视图          =======
# ===============================================


class CourseListView(generics.ListAPIView):
    """
    获取所有已发布的课程列表
    """
    queryset = Course.objects.filter(status='published').order_by('-created_at')
    serializer_class = CourseListSerializer
    authentication_classes = [JWTAuthentication] 
    permission_classes = [AllowAny] 

class CourseDetailView(generics.RetrieveAPIView):
    """
    获取单个已发布课程的详情
    """
    queryset = Course.objects.filter(status='published')
    serializer_class = CourseDetailSerializer
    authentication_classes = [JWTAuthentication] 
    permission_classes = [AllowAny] 

class CourseSubscriptionView(generics.GenericAPIView):
    """
    处理课程的订阅与取消订阅
    """
    permission_classes = [IsAuthenticated]
    queryset = Course.objects.filter(status='published')

    def post(self, request, *args, **kwargs):
        """订阅课程"""
        course = self.get_object()
        user = request.user

        # 检查是否已订阅
        if Subscription.objects.filter(user=user, course=course).exists():
            return Response({"message": "You have already subscribed to this course."}, status=status.HTTP_409_CONFLICT)
            
        # 简单模拟积分扣除
        # if user.currentPoints < course.pricePoints:
        #     return Response({"error": "Insufficient points."}, status=status.HTTP_402_PAYMENT_REQUIRED)
        # user.currentPoints -= course.pricePoints
        # user.save()

        Subscription.objects.create(user=user, course=course)
        return Response({"message": "Successfully subscribed to the course."}, status=status.HTTP_201_CREATED)

    def delete(self, request, *args, **kwargs):
        """取消订阅课程"""
        course = self.get_object()
        user = request.user

        try:
            subscription = Subscription.objects.get(user=user, course=course)
            subscription.delete()
            # 注意：通常取消订阅不退还积分
            return Response({"message": "Successfully unsubscribed from the course."}, status=status.HTTP_204_NO_CONTENT)
        except Subscription.DoesNotExist:
            return Response({"message": "You are not subscribed to this course."}, status=status.HTTP_404_NOT_FOUND)


class CourseCollectionView(generics.GenericAPIView):
    """
    处理课程的收藏与取消收藏
    """
    permission_classes = [IsAuthenticated]
    queryset = Course.objects.all() # 收藏可以针对任何状态的课程

    def post(self, request, *args, **kwargs):
        """收藏课程"""
        course = self.get_object()
        user = request.user

        if Collection.objects.filter(user=user, course=course).exists():
            return Response({"message": "You have already collected this course."}, status=status.HTTP_409_CONFLICT)
            
        Collection.objects.create(user=user, course=course)
        return Response({"message": "Course collected successfully."}, status=status.HTTP_201_CREATED)

    def delete(self, request, *args, **kwargs):
        """取消收藏课程"""
        course = self.get_object()
        user = request.user

        try:
            collection = Collection.objects.get(user=user, course=course)
            collection.delete()
            return Response({"message": "Course uncollected successfully."}, status=status.HTTP_204_NO_CONTENT)
        except Collection.DoesNotExist:
            return Response({"message": "You have not collected this course."}, status=status.HTTP_404_NOT_FOUND)

class CourseProgressView(generics.RetrieveAPIView):
    """
    获取用户在特定课程中的学习进度
    """
    permission_classes = [IsAuthenticated]
    queryset = Course.objects.all()
    serializer_class = CourseProgressSerializer

    def get(self, request, *args, **kwargs):
        course = self.get_object()
        user = request.user
        
        # 检查用户是否已订阅该课程
        if not Subscription.objects.filter(user=user, course=course).exists():
            return Response({"error": "You must subscribe to this course to view progress."}, status=status.HTTP_403_FORBIDDEN)

        try:
            subscription = Subscription.objects.get(user=user, course=course)
        except Subscription.DoesNotExist:
            return Response(
                {"error": "You must subscribe to this course to view progress."}, 
                status=status.HTTP_403_FORBIDDEN
            )
           
        total_chapters = course.chapters.count()
        completed_chapter_ids = user.completed_chapters.filter(course=course).values_list('id', flat=True)
        completed_chapters_count = UserChapterCompletion.objects.filter(
            user=user, chapter__course=course
        ).count()
        is_completed = total_chapters > 0 and completed_chapters_count == total_chapters
        next_chapter_id = None
        if not is_completed:
            next_chapter = course.chapters.exclude(id__in=completed_chapter_ids).order_by('order').first()
            if next_chapter:
                next_chapter_id = next_chapter.id
        data = {
            'completedChapters': completed_chapters_count,
            'totalChapters': total_chapters,
            'isCompleted': is_completed,
            'subscribed_at': subscription.subscribed_at, 
            'last_updated_at': subscription.last_updated_at,
            'completed_at': subscription.completed_at,
            'nextChapterId': next_chapter_id, 
            'nextChapterToComplete': None
        }
        serializer = self.get_serializer(data)
        return Response(serializer.data)

class ExerciseSubmissionView(generics.GenericAPIView):
    """
    处理用户提交的章节练习答案
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ExerciseSubmissionSerializer

    def post(self, request, *args, **kwargs):
        # 从 URL 中获取 course_pk 和 chapter_pk
        course_pk = self.kwargs.get('course_pk')
        chapter_pk = self.kwargs.get('chapter_pk')

        try:
            chapter = Chapter.objects.get(pk=chapter_pk, course_id=course_pk)
            course = chapter.course
        except Chapter.DoesNotExist:
            return Response({"error": "Chapter or Course not found."}, status=status.HTTP_404_NOT_FOUND)

        user = request.user
        # 检查用户是否已订阅
        if not Subscription.objects.filter(user=user, course=course).exists():
            return Response({"error": "You must be subscribed to this course to submit answers."}, status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        submitted_answers = serializer.validated_data['answers']
        
        answers_map = {answer['exerciseId']: answer['userAnswer'] for answer in submitted_answers}
        total_exercises = chapter.exercises.count()
        correct_answers_count = 0

        for exercise in chapter.exercises.all():
            user_answer = answers_map.get(exercise.id)
            if user_answer is None:
                continue

            # 根据题目类型进行不同方式的批改
            if exercise.type == 'multiple-choice':
                correct_options_texts = set(exercise.options.filter(is_correct=True).values_list('text', flat=True))
                user_answers_set = set(user_answer) if isinstance(user_answer, list) else set()
                if correct_options_texts == user_answers_set:
                    correct_answers_count += 1         
            elif exercise.type == 'fill-in-the-blank':
                correct_answers_list = [str(ans).strip() for ans in exercise.answer]
                user_answer_str = str(user_answer).strip()
                if user_answer_str in correct_answers_list:
                    correct_answers_count += 1

        score = (correct_answers_count / total_exercises * 100) if total_exercises > 0 else 0
        is_passed = score >= 80

        if is_passed:
            UserChapterCompletion.objects.get_or_create(user=user, chapter=chapter)

        # --- 计算并返回最新进度 ---
        total_chapters = course.chapters.count()
        completed_chapters_count = user.completed_chapters.filter(course=course).count()
        is_completed = total_chapters > 0 and completed_chapters_count == total_chapters

        new_progress_data = {
            'completedChapters': completed_chapters_count,
            'totalChapters': total_chapters,
            'isCompleted': is_completed,
        }

        # 构造最终返回的数据
        response_data = {
            'score': round(score),
            'isPassed': is_passed,
            'newProgress': new_progress_data
        }

        return Response(response_data, status=status.HTTP_200_OK)
    
# ===============================================
# =======          画廊模块视图          =======
# ===============================================

class GalleryListView(generics.ListAPIView):
    """
    获取所有已发布的画廊作品列表
    """
    queryset = GalleryItem.objects.filter(status='published').order_by('-created_at')
    serializer_class = GalleryListSerializer
    permission_classes = [AllowAny] # 公开接口，允许任何人访问

class GalleryDetailView(mixins.RetrieveModelMixin, generics.GenericAPIView):
    """
    获取单个作品详情 (GET) 或处理下载请求 (POST)
    """
    queryset = GalleryItem.objects.filter(status='published')
    serializer_class = GalleryDetailSerializer
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        """处理 GET 请求，返回作品详情"""
        return self.retrieve(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """处理 POST 请求，用于下载 (最终健壮版)"""
        if not request.user.is_authenticated:
            return Response({"error": "Please log in to download."}, status=status.HTTP_401_UNAUTHORIZED)
        
        work = self.get_object()
        user = request.user
        confirm_deduction = request.data.get('confirmDeduction', False)

        if not work.workFile:
            return Response({"error": "Work file is not available for this item."}, status=status.HTTP_404_NOT_FOUND)

        # 检查前置条件，并返回带标题的错误
        if work.prerequisiteWork and not GalleryDownloadRecord.objects.filter(user=user, gallery_item=work.prerequisiteWork).exists():
            return Response({
                "prerequisiteNotMet": True,
                "requiredWork": {
                    "id": work.prerequisiteWork.id,
                    "title": work.prerequisiteWork.title
                }
            }, status=status.HTTP_409_CONFLICT)
        
        is_redownload = GalleryDownloadRecord.objects.filter(user=user, gallery_item=work).exists()
        
        if is_redownload or work.requiredPoints == 0:
            return Response({"downloadUrl": request.build_absolute_uri(work.workFile.url)})
        
        if user.currentPoints < work.requiredPoints:
            return Response({"error": "Insufficient points."}, status=status.HTTP_402_PAYMENT_REQUIRED)

        if not confirm_deduction:
            return Response({
                "confirmationRequired": True,
                "pointsToDeduct": work.requiredPoints
            }, status=status.HTTP_409_CONFLICT)
        
        user.currentPoints -= work.requiredPoints
        user.save()
        GalleryDownloadRecord.objects.create(user=user, gallery_item=work, points_spent=work.requiredPoints)
        
        return Response({"downloadUrl": request.build_absolute_uri(work.workFile.url)})

class GalleryCollectionView(generics.GenericAPIView):
    """
    处理画廊作品的收藏与取消收藏
    """
    permission_classes = [IsAuthenticated]
    queryset = GalleryItem.objects.all()

    def post(self, request, *args, **kwargs):
        """收藏作品"""
        work = self.get_object()
        user = request.user
        _, created = GalleryCollection.objects.get_or_create(user=user, gallery_item=work)
        if not created:
            return Response({"message": "You have already collected this work."}, status=status.HTTP_409_CONFLICT)
        return Response({"message": "Work collected successfully."}, status=status.HTTP_201_CREATED)

    def delete(self, request, *args, **kwargs):
        """取消收藏作品"""
        work = self.get_object()
        user = request.user
        deleted_count, _ = GalleryCollection.objects.filter(user=user, gallery_item=work).delete()
        if deleted_count == 0:
            return Response({"message": "You have not collected this work."}, status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)
    
# ===============================================
# =======          社群模块视图          =======
# ===============================================


class CommunityListView(generics.ListAPIView):
    """
    【第一级】获取所有社群板块的列表
    """
    queryset = Community.objects.all().order_by('-created_at')
    serializer_class = CommunityListSerializer
    permission_classes = [AllowAny] # 公开接口

class CommunityPostListCreateView(generics.ListCreateAPIView):
    """
    【第二级】获取帖子列表 (GET) 或创建新帖子 (POST)
    """
    #permission_classes = [AllowAny] # GET 请求允许任何人
    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated(), CanPostOrReplyInCommunity()]
        return [AllowAny()]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CommunityPostCreateSerializer
        return CommunityPostListSerializer

    def get_queryset(self):
        if self.request.method == 'GET':
            community_pk = self.kwargs.get('community_pk')
            return CommunityPost.objects.filter(community_id=community_pk, status='published').order_by('-created_at')
        return super().get_queryset()
    
    def perform_create(self, serializer):
        user = self.request.user
        if user.accountStatus == 'suspended':
            raise serializers.ValidationError({"error": "您的账户已被禁言，无法发布帖子。"})
        community = get_object_or_404(Community, pk=self.kwargs.get('community_pk'))
        reward_points = serializer.validated_data.get('rewardPoints', 0)
        if reward_points > 0:
            if user.currentPoints < reward_points:
                raise serializers.ValidationError({"error": "您的积分不足以支付悬赏。"})
            user.currentPoints -= reward_points
            user.save(update_fields=['currentPoints'])
        serializer.save(author=user, community=community)

class CommunityPostDetailView(generics.RetrieveAPIView):
    """
    【第三级】获取单个帖子的详情（包含所有回复）
    """
    serializer_class = CommunityPostDetailSerializer
    permission_classes = [AllowAny]
    lookup_url_kwarg = 'post_pk' 

    def get_queryset(self):
        # 根据 URL 动态筛选，确保帖子属于该社群
        community_pk = self.kwargs.get('community_pk')
        return CommunityPost.objects.filter(
            community_id=community_pk, 
            status='published'
        )

class CommunityPostDestroyView(generics.DestroyAPIView):
    """删除当前用户自己的帖子"""
    queryset = CommunityPost.objects.all()
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return super().get_queryset().filter(author=self.request.user)

class CommunityPostLikeView(generics.GenericAPIView):
    """点赞/取消点赞一个帖子"""
    queryset = CommunityPost.objects.all()
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        post = self.get_object()
        user = request.user
        if user in post.likes.all():
            post.likes.remove(user)
            return Response({"status": "unliked", "likes_count": post.likes.count()})
        else:
            post.likes.add(user)
            return Response({"status": "liked", "likes_count": post.likes.count()})

class CommunityReplyCreateView(generics.CreateAPIView):
    """为指定帖子创建新回复"""
    queryset = CommunityReply.objects.all()
    serializer_class = CommunityReplyCreateSerializer
    permission_classes = [IsAuthenticated,CanPostOrReplyInCommunity]

    def perform_create(self, serializer):
        user = self.request.user
        if user.accountStatus == 'suspended':
            raise serializers.ValidationError({"error": "您的账户已被禁言，无法发布回复。"})
        post = get_object_or_404(CommunityPost, pk=self.kwargs.get('post_pk'))
        serializer.save(author=self.request.user, post=post)

class CommunityCreateView(generics.CreateAPIView):
    """
    POST /creator/communities/
    允许创作者创建新的社群板块
    """
    queryset = Community.objects.all()
    serializer_class = CommunityCreateSerializer
    permission_classes = [IsAuthenticated, IsCreator] # <-- 应用创作者权限

    def perform_create(self, serializer):
        # 自动将创始人设置为当前用户
        serializer.save(founder=self.request.user)

# ===============================================
# =======          管理员模块视图          =======
# ===============================================

@staff_member_required
def dashboard_view(request):
    """
    后台仪表盘的视图函数 (可视化数据版)
    """
    # --- 1. 核心 KPI ---
    thirty_days_ago = timezone.now() - timedelta(days=30)
    kpi_data = {
        'totalUsers': User.objects.count(),
        'newUsersLast30Days': User.objects.filter(date_joined__gte=thirty_days_ago).count(),
        'totalCourses': Course.objects.filter(status='published').count(),
        'totalGalleryWorks': GalleryItem.objects.filter(status='published').count(),
        'totalCommunities': Community.objects.count(),
    }

    # --- 2. 用户画像 (平台全局) ---
    # 按年龄段
    age_data = User.objects.values('ageGroup').annotate(count=Count('id')).order_by('-count')
    # 按性别
    gender_data = User.objects.values('gender').annotate(count=Count('id')).order_by('-count')
    user_demographics_data = {
        'byAge': json.dumps({item['ageGroup'] or '未知': item['count'] for item in age_data}),
        'byGender': json.dumps({item['gender'] or '未知': item['count'] for item in gender_data}),
    }

    # --- 3. 内容与审核指标 ---
    review_metrics_data = {
        'pendingCourses': Course.objects.filter(status='pending_review').count(),
        'pendingWorks': GalleryItem.objects.filter(status='pending_review').count(),
        'pendingCertifications': CertificationRequest.objects.filter(status='pending').count(),
        'pendingCommunityPosts': CommunityPost.objects.filter(status='pending_review').count(),
    }

    # --- 4. 平台参与度指标 ---
    top_5_tags = list(Tag.objects.annotate(
        usage_count=Count('courses') + Count('gallery_items') + Count('communities')
    ).order_by('-usage_count').values('name', 'usage_count')[:5])

    top_5_courses = list(Course.objects.annotate(
        num_subs=Count('subscribers')
    ).order_by('-num_subs').values('title', 'num_subs')[:5])

    top_5_works = list(GalleryItem.objects.annotate(
        num_downs=Count('gallerydownloadrecord')
    ).order_by('-num_downs').values('title', 'num_downs')[:5])

    top_5_communities = list(Community.objects.annotate(
        num_members=Count('members')
    ).order_by('-num_members').values('name', 'num_members')[:5])
    
    top_5_posts = list(CommunityPost.objects.annotate(
        num_replies=Count('replies')
    ).order_by('-num_replies').values('title', 'num_replies')[:5])

    engagement_metrics_data = {
        'top5UsedTags': json.dumps({item['name']: item['usage_count'] for item in top_5_tags}),
        'top5SubscribedCourses': json.dumps({item['title']: item['num_subs'] for item in top_5_courses}),
        'top5DownloadedWorks': json.dumps({item['title']: item['num_downs'] for item in top_5_works}),
        'top5CommunitiesByMembers': json.dumps({item['name']: item['num_members'] for item in top_5_communities}),
        'top5PostsByReplies': json.dumps({item['title']: item['num_replies'] for item in top_5_posts}),
    }
    
    context = {
        'title': '平台仪表盘',
        'kpi_data': kpi_data,
        'user_demographics_data': user_demographics_data,
        'review_metrics_data': review_metrics_data,
        'engagement_metrics_data': engagement_metrics_data,
        'age_chart_labels': json.dumps([item['ageGroup'] or '未知' for item in age_data]),
        'age_chart_data': json.dumps([item['count'] for item in age_data]),
        
        'gender_chart_labels': json.dumps([item['gender'] or '未知' for item in gender_data]),
        'gender_chart_data': json.dumps([item['count'] for item in gender_data]),
        
        'tags_chart_labels': json.dumps([item['name'] for item in top_5_tags]),
        'tags_chart_data': json.dumps([item['usage_count'] for item in top_5_tags]),
        
        'courses_chart_labels': json.dumps([item['title'] for item in top_5_courses]),
        'courses_chart_data': json.dumps([item['num_subs'] for item in top_5_courses]),
        
        'works_chart_labels': json.dumps([item['title'] for item in top_5_works]),
        'works_chart_data': json.dumps([item['num_downs'] for item in top_5_works]),
        
        'communities_chart_labels': json.dumps([item['name'] for item in top_5_communities]),
        'communities_chart_data': json.dumps([item['num_members'] for item in top_5_communities]),
        
        'posts_chart_labels': json.dumps([item['title'] for item in top_5_posts]),
        'posts_chart_data': json.dumps([item['num_replies'] for item in top_5_posts]),
    }

    return render(request, 'admin/dashboard.html', context)

# ===============================================
# =======      站内信视图        =======
# ===============================================
class MessageThreadListCreateView(generics.ListCreateAPIView):
    """
    GET: 获取当前用户的所有会话列表
    POST: 用户发送一条新消息（开启一个新会话）
    """
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return MessageCreateSerializer
        return MessageThreadListSerializer

    def get_queryset(self):
        user = self.request.user
        # 1. 找到每个会话的最后一条消息的 ID
        latest_message_subquery = Message.objects.filter(
            thread=OuterRef('pk')
        ).order_by('-sent_at').values('pk')[:1] # 找到每条线程的最新消息ID
        
        # 2. 创建 Prefetch 对象，只预取那些 ID 在子查询结果中的 Message
        prefetch_messages = Prefetch(
            'messages',
            queryset=Message.objects.filter(
                pk__in=Subquery(latest_message_subquery)
            ).select_related('sender') # 优化：同时预加载发信人信息
        )
        queryset = user.message_threads.all().prefetch_related(prefetch_messages).order_by('-created_at')
        
        return queryset

    def perform_create(self, serializer):
        # POST 请求时，执行创建逻辑
        subject = serializer.validated_data['subject']
        content = serializer.validated_data['content']
        recipient = get_object_or_404(User, pk=serializer.validated_data['recipient_id'])
        sender = self.request.user

        thread = MessageThread.objects.create(subject=subject)
        thread.participants.add(sender, recipient)
        
        admin_user = User.objects.filter(is_superuser=True).first()
        Message.objects.create(
            thread=thread,
            sender=sender,
            recipient=recipient,
            content=content,
            cc_recipient=admin_user
        )
        
    def create(self, request, *args, **kwargs):
        # 重写 create 方法以返回自定义消息，而不是序列化器数据
        super().create(request, *args, **kwargs)
        return Response({"message": "消息已成功发送。"}, status=status.HTTP_201_CREATED)

class MessageThreadRetrieveDestroyView(generics.RetrieveDestroyAPIView):
    """
    GET /my/messages/{pk}/: 获取单个会话详情
    DELETE /my/messages/{pk}/: 用户离开会话
    """
    queryset = MessageThread.objects.all()
    serializer_class = MessageThreadDetailSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # 确保用户只能查看/删除自己参与的会话
        return self.request.user.message_threads.all()
    
    def perform_destroy(self, instance):
        instance.participants.remove(self.request.user)

class UserSearchView(generics.ListAPIView):
    """
    根据查询参数 'q' 搜索用户，用于站内信收件人自动补全
    """
    serializer_class = UserSummarySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # 从 URL query a参数中获取搜索关键词
       query = self.request.query_params.get('q', None)
       if query:
        return User.objects.filter(
            Q(username__icontains=query) | 
            Q(nickname__icontains=query)
        ).filter(is_active=True)[:10]
       return User.objects.none() 
# ===============================================
# =======     个人中心 API 视图            =======
# ===============================================

class MyCollectionsView(generics.GenericAPIView):
    """获取当前用户收藏的所有内容"""
    permission_classes = [IsAuthenticated]
    serializer_class = MyCollectionsSerializer

    def get(self, request, *args, **kwargs):
        user = request.user
        collected_courses = Course.objects.filter(collectors=user)
        collected_gallery_items = GalleryItem.objects.filter(collectors=user)
        
        data = {
            'courses': collected_courses,
            'gallery_items': collected_gallery_items
        }
        serializer = self.get_serializer(data)
        return Response(serializer.data)

class MySupportedView(generics.GenericAPIView):
    """获取当前用户已订阅/下载的所有内容"""
    permission_classes = [IsAuthenticated]
    serializer_class = MySupportedSerializer

    def get(self, request, *args, **kwargs):
        user = request.user
        subscribed_courses = Course.objects.filter(subscribers=user)
        downloaded_gallery_items = GalleryItem.objects.filter(gallerydownloadrecord__user=user)
        
        data = {
            'courses': subscribed_courses,
            'gallery_items': downloaded_gallery_items
        }
        serializer = self.get_serializer(data)
        return Response(serializer.data)

class MyCreationsView(generics.GenericAPIView):
    """获取当前用户创建的所有内容"""
    permission_classes = [IsAuthenticated]
    serializer_class = MyCreationsSerializer

    def get(self, request, *args, **kwargs):
        user = request.user
        authored_courses = Course.objects.filter(author=user)
        authored_gallery_items = GalleryItem.objects.filter(author=user)
        founded_communities = Community.objects.filter(founder=user)
        
        data = {
            'courses': authored_courses,
            'gallery_items': authored_gallery_items,
            'founded_communities': founded_communities,
        }
        serializer = self.get_serializer(data)
        return Response(serializer.data)

class MyParticipationsView(generics.GenericAPIView):
    """获取当前用户参与回复过的所有帖子"""
    permission_classes = [IsAuthenticated]
    serializer_class = MyParticipationsSerializer

    def get(self, request, *args, **kwargs):
        user = request.user
        # 查找所有该用户回复过的帖子的ID，并去重
        participated_post_ids = CommunityReply.objects.filter(author=user).values_list('post_id', flat=True).distinct()
        participated_posts = CommunityPost.objects.filter(pk__in=participated_post_ids)
        
        data = {'posts': participated_posts}
        serializer = self.get_serializer(data)
        return Response(serializer.data)
    
class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    处理获取和更新当前登录用户信息的视图
    GET: 返回当前用户信息
    PUT/PATCH: 更新当前用户信息
    """
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]  

    def get_object(self):
        return self.request.user
    def post(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)
    
class CourseCreateView(generics.CreateAPIView):
    """
    POST /creator/courses/
    允许创作者创建新课程
    """
    queryset = Course.objects.all()
    serializer_class = CourseCreateSerializer 
    permission_classes = [IsAuthenticated, IsCreator]
    parser_classes = [MultiPartParser, FormParser] # 支持封面图上传

    def perform_create(self, serializer):
        # 自动将作者设为当前用户，初始状态设为 draft (草稿)
        serializer.save(author=self.request.user, status='draft')
class GalleryItemCreateView(generics.CreateAPIView):
    queryset = GalleryItem.objects.all()
    serializer_class = GalleryItemCreateSerializer
    permission_classes = [IsAuthenticated, IsCreator] 
    parser_classes = [MultiPartParser, FormParser]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user, status='pending_review')
class CommunityCreateView(generics.CreateAPIView):
    queryset = Community.objects.all()
    serializer_class = CommunityCreateSerializer
    permission_classes = [IsAuthenticated, IsCreator]
    parser_classes = [MultiPartParser, FormParser]

    def perform_create(self, serializer):
        serializer.save(founder=self.request.user)