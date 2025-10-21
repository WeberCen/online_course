# backend/api/views.py
import random
import json
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import viewsets,generics,mixins, status,serializers
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Count, Q,Exists,OuterRef,Subquery,Count,Prefetch
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404,render
from django.utils import timezone
from datetime import timedelta
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import transaction
from .permissions import IsStudent,IsArtist,IsAdmin,IsOwner,IsPaidUsers
from .tasks import send_verification_code_email
from .serializers import (
    UserRegisterSerializer, UserProfileSerializer, UserSummarySerializer,UserLoginSerializer,
    ChangePhoneInitiateSerializer, ChangePhoneVerifyNewSerializer, ChangePhoneCommitSerializer,
    ChangeEmailInitiateSerializer, ChangeEmailVerifyNewSerializer, ChangeEmailCommitSerializer,
    CertificationRequestSerializer, EditorImageSerializer,CourseListSerializer, CourseDetailSerializer,
    PasswordResetRequestSerializer, PasswordResetConfirmSerializer,
    CourseProgressSerializer, ExerciseSubmissionSerializer,UserExerciseSubmission,
    GalleryListSerializer, GalleryDetailSerializer, CourseCreateSerializer,GalleryItemCreateSerializer,CommunityCreateSerializer,
    CommunityListSerializer, CommunityPostListSerializer, CommunityPostDetailSerializer,
    CommunityPostCreateSerializer,CommunityReplyCreateSerializer,
    CommunityDetailSerializer,MessageCreateSerializer,MessageThreadListSerializer,MessageThreadDetailSerializer,
    MyCollectionsSerializer,MySupportedSerializer,MyCreationsSerializer,MyParticipationsSerializer,
    ChapterSerializer,ExerciseSerializer)
from .models import (CertificationRequest,Course,Chapter,
                     Subscription,Collection,Exercise,UserChapterCompletion,
                     GalleryItem,GalleryCollection,GalleryDownloadRecord,
                     Community,CommunityPost,CommunityReply,
                     User,Tag,Message,MessageThread,UserExerciseCompletion,)
import logging

logger = logging.getLogger(__name__)

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
    
class UserProfileUpdateView(generics.UpdateAPIView):
    """
    处理用户资料更新上传
    """
    serializer_class = UserProfileSerializer 
    permission_classes = [IsStudent]
    parser_classes = [MultiPartParser, FormParser]

    def get_object(self):
        return self.request.user

    
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
    permission_classes = [IsStudent]
    parser_classes = [MultiPartParser, FormParser] 

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

# ==============================================================================
# 1. 將課程相關視圖整合進 CourseViewSet
# ==============================================================================
class CourseViewSet(viewsets.ReadOnlyModelViewSet):
    """
    用於處理課程列表和詳情的視圖集
    """
    queryset = Course.objects.filter(status='published').select_related('author').prefetch_related('chapters', 'tags', 'collectors', 'subscribers')
    
    def get_serializer_class(self):
        if self.action == 'list':
            return CourseListSerializer
        return CourseDetailSerializer

    def get_serializer_context(self):
        return {'request': self.request}

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def subscribe(self, request, pk=None):
        course = self.get_object()
        user = request.user
        if Subscription.objects.filter(user=user, course=course).exists():
            return Response({"detail": "You have already subscribed to this course."}, status=status.HTTP_409_CONFLICT)
        # ... 您的積分扣除邏輯 ...
        Subscription.objects.create(user=user, course=course)
        return Response({"detail": "Successfully subscribed to the course."}, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['delete'], permission_classes=[IsAuthenticated])
    def unsubscribe(self, request, pk=None):
        course = self.get_object()
        user = request.user
        deleted_count, _ = Subscription.objects.filter(user=user, course=course).delete()
        if deleted_count == 0:
            return Response({"detail": "You are not subscribed to this course."}, status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def collect(self, request, pk=None):
        course = self.get_object()
        user = request.user
        _, created = Collection.objects.get_or_create(user=user, course=course)
        if not created:
            return Response({"detail": "You have already collected this course."}, status=status.HTTP_409_CONFLICT)
        return Response({"detail": "Course collected successfully."}, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['delete'], permission_classes=[IsAuthenticated])
    def uncollect(self, request, pk=None):
        course = self.get_object()
        user = request.user
        deleted_count, _ = Collection.objects.filter(user=user, course=course).delete()
        if deleted_count == 0:
            return Response({"detail": "You have not collected this course."}, status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=True, methods=['get'], permission_classes=[IsStudent])
    def progress(self, request, pk=None):
        """
        獲取用戶對單一課程的學習進度。
        """
        try:
            course = self.get_object()
            user = request.user

            if not Subscription.objects.filter(user=user, course=course).exists():
                return Response({"detail": "用戶未訂閱本課程"}, status=status.HTTP_403_FORBIDDEN)

            total_exercises = Exercise.objects.filter(chapter__course=course).count()

            if total_exercises == 0:
                return Response({
                    "completed_exercises": 0,
                    "total_exercises": 0,
                    "progress_percentage": 100, 
                    "next_chapter_id": None, 
                })
            completed_exercises = UserExerciseSubmission.objects.filter(
                user=user,
                exercise__chapter__course=course,
                is_correct=True
            ).values('exercise').distinct().count()
            progress_percentage = round((completed_exercises / total_exercises) * 100) if total_exercises > 0 else 0
            next_chapter_id = self._get_next_chapter_id(user, course)
            progress_data = {
                "completed_exercises": completed_exercises,
                "total_exercises": total_exercises,
                "progress_percentage": progress_percentage,
                "next_chapter_id": next_chapter_id
            }
            return Response(progress_data, status=status.HTTP_200_OK)

        except Course.DoesNotExist:
            return Response({"detail": "課程未找到"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error getting course progress for user {request.user.id} and course {pk}: {e}")
            return Response({"detail": "獲取課程進度時發生內部伺服器錯誤。"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _get_next_chapter_id(self, user, course):
        """
        【輔助方法】計算並返回用戶在此課程中下一個要學習的章節ID。
        這個方法沒有被 @action 裝飾，所以它不是一個 API 端點。
        """
        completed_chapter_ids = UserChapterCompletion.objects.filter(
            user=user, chapter__course=course
        ).values_list('chapter_id', flat=True)
        next_chapter = Chapter.objects.filter(
            course=course
        ).exclude( 
            id__in=completed_chapter_ids
        ).order_by('order').first()
        return next_chapter.id if next_chapter else None
    
# ==============================================================================
# 2. 新建 ChapterViewSet 並重構練習提交視圖
# ==============================================================================
class ChapterViewSet(viewsets.ReadOnlyModelViewSet):
    """
    用於處理章節相關操作，主要是練習提交
    """
    queryset = Chapter.objects.all()
    # 這裡可以定義一個基礎的 ChapterSerializer
    # serializer_class = BaseChapterSerializer 

    @action(detail=True, methods=['post'], permission_classes=[IsStudent], serializer_class=ExerciseSubmissionSerializer)
    def submit(self, request, pk=None):
        """
        【核心重構】接收章節練習提交，批改並返回詳細報告
        """
        chapter = self.get_object()
        user = request.user
        course = chapter.course

        # 檢查訂閱狀態
        if not Subscription.objects.filter(user=user, course=course).exists():
            return Response({"detail": "You must be subscribed to this course to submit answers."}, status=status.HTTP_403_FORBIDDEN)

        # 1. 使用 ExerciseSubmissionSerializer 驗證輸入數據
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        submitted_answers = serializer.validated_data['answers']
        
        # 2. 初始化報告和輔助數據結構
        summary = {"correct_count": 0, "incorrect_count": 0, "incorrect_exercises": []}
        details = {}
        
        # 為了高效查詢，一次性獲取本章節所有練習題
        exercises = chapter.exercises.prefetch_related('options', 'fill_in_blanks').all()
        exercise_map = {ex.id: ex for ex in exercises}
        
        submissions_to_process = []

        # 3. 循環批改
        for answer_data in submitted_answers:
            exercise_id = answer_data['exerciseId']
            user_answer = answer_data['userAnswer']
            
            exercise = exercise_map.get(exercise_id)
            if not exercise:
                continue # 跳過不屬於本章節的題目

            is_correct = False
            correct_answer = None

            if exercise.type == 'multiple-choice':
                correct_options_qs = exercise.options.filter(is_correct=True)
                correct_answer = list(correct_options_qs.values_list('text', flat=True))
                submitted_options = set(user_answer) if isinstance(user_answer, list) else set()
                is_correct = (set(correct_answer) == submitted_options)
            elif exercise.type == 'fill-in-the-blank':
                blank = exercise.fill_in_blanks.first()
                if blank:
                    correct_answer = blank.correct_answer
                    if blank.case_sensitive:
                        is_correct = (str(user_answer).strip() == correct_answer)
                    else:
                        is_correct = (str(user_answer).strip().lower() == correct_answer.lower())
            
            # 準備數據庫操作
            submissions_to_process.append({
                "user": user,
                "exercise": exercise,
                "submitted_answer": user_answer,
                "is_correct": is_correct
            })

            # --- 構建返回的報告 ---
            if is_correct:
                summary['correct_count'] += 1
            else:
                summary['incorrect_count'] += 1
                summary['incorrect_exercises'].append({"id": exercise.id, "prompt": exercise.prompt})
            
            details[str(exercise_id)] = {
                "is_correct": is_correct,
                "correct_answer": correct_answer,
                "analysis": exercise.explanation
            }
            
        # 4. 高效地將所有提交記錄一次性寫入數據庫
        # 使用 bulk_create 和 bulk_update 可以更高效，這裡用 update_or_create 逐一處理更清晰
        for sub_data in submissions_to_process:
            UserExerciseSubmission.objects.update_or_create(
                user=sub_data['user'],
                exercise=sub_data['exercise'],
                defaults={
                    'submitted_answer': sub_data['submitted_answer'],
                    'is_correct': sub_data['is_correct']
                }
            )

        # 5. 構建最終報告並返回
        final_report = {
            "summary": summary,
            "details": details
        }
        
        return Response(final_report, status=status.HTTP_200_OK)

# ===============================================
# =======          画廊模块视图          =======
# ===============================================

class GalleryItemViewSet(viewsets.ReadOnlyModelViewSet):
    """
    用於處理畫廊作品列表、詳情及相關操作的視圖集
    """
    queryset = GalleryItem.objects.filter(status='published').select_related('author', 'prerequisiteWork').prefetch_related('tags')
    
    def get_serializer_class(self):
        if self.action == 'list':
            return GalleryListSerializer
        return GalleryDetailSerializer

    def get_serializer_context(self):
        return {'request': self.request}
    
    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action not in ['list', 'retrieve']:
            return queryset
        user = self.request.user
        queryset = queryset.annotate(
            annotated_collectors_count=Count('collectors', distinct=True),
            annotated_downloaders_count=Count('downloaders', distinct=True)
        )
        if user and user.is_authenticated:

            collected_subquery = GalleryCollection.objects.filter(
                user=user,
                gallery_item=OuterRef('pk')
            )
            downloaded_subquery = GalleryDownloadRecord.objects.filter(
                user=user,
                gallery_item=OuterRef('pk')
            )

            queryset = queryset.annotate(
                annotated_is_collected=Exists(collected_subquery),
                annotated_is_downloaded=Exists(downloaded_subquery)
            )
        
        return queryset
    


    @action(detail=True, methods=['post'], permission_classes=[IsStudent])
    def collect(self, request, pk=None):
        """收藏作品"""
        work = self.get_object()
        user = request.user
        _, created = GalleryCollection.objects.get_or_create(user=user, gallery_item=work)
        if not created:
            return Response({"detail": "You have already collected this work."}, status=status.HTTP_409_CONFLICT)
        return Response({"detail": "Work collected successfully."}, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['delete'], permission_classes=[IsStudent])
    def uncollect(self, request, pk=None):
        """取消收藏作品"""
        work = self.get_object()
        user = request.user
        deleted_count, _ = GalleryCollection.objects.filter(user=user, gallery_item=work).delete()
        if deleted_count == 0:
            return Response({"detail": "You have not collected this work."}, status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'], permission_classes=[IsStudent])
    def download(self, request, pk=None):
        """
        【核心重構】處理作品的下載請求
        """
        work = self.get_object()
        user = request.user
        # 前端應傳遞 'isConfirmed' 而非 'confirmDeduction' 以保持一致性
        is_confirmed = request.data.get('isConfirmed', False)

        if not work.workFile:
            return Response({"detail": "Work file is not available for this item."}, status=status.HTTP_404_NOT_FOUND)

        if work.prerequisiteWork and not GalleryDownloadRecord.objects.filter(user=user, gallery_item=work.prerequisiteWork).exists():
            return Response({
                "prerequisiteNotMet": True,
                "requiredWork": {"id": work.prerequisiteWork.id, "title": work.prerequisiteWork.title}
            }, status=status.HTTP_409_CONFLICT)
        
        is_redownload = GalleryDownloadRecord.objects.filter(user=user, gallery_item=work).exists()
        
        if is_redownload or work.requiredPoints == 0 or (work.is_vip_free and user.is_vip): # 假設用戶模型有 is_vip 屬性
            return Response({"downloadUrl": request.build_absolute_uri(work.workFile.url)})
        
        if user.currentPoints < work.requiredPoints:
            return Response({"detail": "Insufficient points."}, status=status.HTTP_402_PAYMENT_REQUIRED)

        if not is_confirmed:
            return Response({
                "confirmationRequired": True,
                "pointsToDeduct": work.requiredPoints
            }, status=status.HTTP_409_CONFLICT)
        
        # --- 執行扣分和創建下載記錄 ---
        user.currentPoints -= work.requiredPoints
        user.save()
        
        PointsTransaction.objects.create(
            user=user, 
            amount=-work.requiredPoints,
            description=f"下载作品: {work.title}",
            transaction_type='download', # 假設您有對應的類型
            content_object=work
        )

        # 【關鍵實現】: 在創建下載記錄時，保存當前的版本號
        GalleryDownloadRecord.objects.create(
            user=user, 
            gallery_item=work, 
            points_spent=work.requiredPoints,
            version_at_download=work.version # <-- 將版本號存入資料庫
        )
        
        return Response({"downloadUrl": request.build_absolute_uri(work.workFile.url)})
    
# ===============================================
# =======          社群模块视图          =======
# ===============================================


class CommunityViewSet(viewsets.ModelViewSet):
    """
    【第一级】社群板块
    """
    queryset = Community.objects.all().order_by('-created_at')

    def get_serializer_class(self):
        """根据 action 返回不同的序列化器"""
        if self.action == 'list':
            return CommunityListSerializer
        if self.action == 'create':
            return CommunityCreateSerializer
        if self.action == 'retrieve':
            return CommunityDetailSerializer
        return CommunityListSerializer # 默认

    def get_permissions(self):
        """根据 action 设置不同的权限"""
        if self.action == 'list':
            # 继承自 CommunityListView
            self.permission_classes = [AllowAny]
        elif self.action == 'create':
            # 继承自 CommunityCreateView
            self.permission_classes = [IsAuthenticated, IsArtist]
        elif self.action == 'retrieve':
            # 继承自 CommunityDetailView
            self.permission_classes = [IsAuthenticated, IsArtist]
        # (其他 action 如 update, destroy 可以后续添加)
        return super().get_permissions()

    def perform_create(self, serializer):
        """
        继承自 CommunityCreateView.perform_create
        """
        serializer.save(founder=self.request.user)

class CommunityPostViewSet(viewsets.ModelViewSet):
    """
    【第二级】社群帖子
    """
    queryset = CommunityPost.objects.all().order_by('-created_at')
    
    # URL kwarg (来自 DetailView)
    lookup_url_kwarg = 'post_pk' 

    def get_queryset(self):
        qs = super().get_queryset().filter(
            community_id=self.kwargs.get('community_pk')
        )
        
        # 继承自 CommunityPostListView / DetailView 的逻辑
        if self.action in ['list', 'retrieve']:
             qs = qs.filter(status='published')
        
        # 继承自 CommunityPostDestroyView (虽然 IsOwner 权限会做检查，但双重保险)
        if self.action == 'destroy':
            qs = qs.filter(author=self.request.user)

        return qs

    def get_serializer_class(self):
        """根据 action 返回不同的序列化器"""
        if self.action == 'list':
            return CommunityPostListSerializer
        if self.action == 'create':
            return CommunityPostCreateSerializer
        if self.action == 'retrieve':
            return CommunityPostDetailSerializer
        return CommunityPostListSerializer # 默认

    def get_permissions(self):
        """根据 action 设置不同的权限"""
        if self.action == 'list':
            # 继承自 CommunityPostListView
            self.permission_classes = [AllowAny]
        elif self.action == 'retrieve':
            # 继承自 CommunityPostDetailView
            self.permission_classes = [IsStudent]
        elif self.action == 'create':
            # 继承自 CommunityPostCreateView
            self.permission_classes = [IsStudent, IsPaidUsers]
        elif self.action == 'destroy':
            # 继承自 CommunityPostDestroyView
            self.permission_classes = [IsOwner]
        elif self.action == 'like':
            # 继承自 CommunityPostLikeView
            self.permission_classes = [IsStudent]
        return super().get_permissions()

    def perform_create(self, serializer):
        """
        继承自 CommunityPostCreateView.perform_create
        """
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

    @action(detail=True, methods=['post'])
    def like(self, request, community_pk=None, post_pk=None):
        """
        继承自 CommunityPostLikeView.post
        """
        post = self.get_object() 
        user = request.user
        if user in post.likes.all():
            post.likes.remove(user)
            return Response({"status": "unliked", "likes_count": post.likes.count()})
        else:
            post.likes.add(user)
            return Response({"status": "liked", "likes_count": post.likes.count()})

class CommunityReplyViewSet(mixins.CreateModelMixin, 
                          mixins.ListModelMixin, # (推荐) 添加 List
                          viewsets.GenericViewSet):
    """
    【第三级】帖子回复
    """
    queryset = CommunityReply.objects.all().order_by('-created_at')
    serializer_class = CommunityReplyCreateSerializer
    permission_classes = [IsStudent] 

    def get_queryset(self):
        """根据 URL 中的 post_pk 过滤回复"""
        return super().get_queryset().filter(
            post_id=self.kwargs.get('post_pk')
        )

    def perform_create(self, serializer):
        """
        继承自 CommunityReplyCreateView.perform_create
        """
        user = self.request.user
        if user.accountStatus == 'suspended':
            raise serializers.ValidationError({"error": "您的账户已被禁言，无法发布回复。"})
        
        # 注意: 我们从 URL 中获取 post_pk
        post = get_object_or_404(CommunityPost, pk=self.kwargs.get('post_pk'))
        serializer.save(author=self.request.user, post=post)

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

# ===============================================
# =======    创作者工作台 -    =======
# ===============================================
class CourseCreateView(generics.CreateAPIView):
    """
    POST /creator/courses/
    允许创作者创建新课程
    """
    queryset = Course.objects.all()
    serializer_class = CourseCreateSerializer 
    permission_classes = [IsAuthenticated, IsArtist]
    parser_classes = [MultiPartParser, FormParser] # 支持封面图上传

    def perform_create(self, serializer):
        serializer.save(author=self.request.user, status='draft')
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context
    
class GalleryItemCreateView(generics.CreateAPIView):
    queryset = GalleryItem.objects.all()
    serializer_class = GalleryItemCreateSerializer
    permission_classes = [IsAuthenticated, IsArtist] 
    parser_classes = [MultiPartParser, FormParser]
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context
    def perform_create(self, serializer):
        serializer.save(author=self.request.user, status='pending_review')

class CommunityCreateView(generics.CreateAPIView):
    queryset = Community.objects.all()
    serializer_class = CommunityCreateSerializer
    permission_classes = [IsAuthenticated, IsArtist]
    parser_classes = [MultiPartParser, FormParser]
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context
    def perform_create(self, serializer):
        serializer.save(founder=self.request.user)

class CourseUpdateDetailView(generics.RetrieveUpdateAPIView): 
    """
    GET:    /creator/courses/{pk}/ -> 获取课程详情 (用于填充编辑表单)
    PUT:    /creator/courses/{pk}/ -> 提交整个课程更新
    PATCH:  /creator/courses/{pk}/ -> 提交部分课程更新
    """
    queryset = Course.objects.all()
    #queryset = Course.objects.filter(author=self.request.user)
    serializer_class = CourseCreateSerializer 
    permission_classes = [IsAuthenticated, IsArtist, IsOwner] # IsOwner 即可
    parser_classes = [MultiPartParser, FormParser] 

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return CourseDetailSerializer
        return CourseCreateSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context
    
    def perform_update(self, serializer):
        serializer.save(status=Course.StatusChoices.DRAFT)

class MyCourseListView(generics.ListAPIView):
    """
    GET /creator/courses/
    获取当前登录创作者的所有课程列表 (用于仪表盘)
    """
    serializer_class = CourseListSerializer # 假设这是你已有的列表序列化器
    permission_classes = [IsAuthenticated, IsArtist]

    def get_queryset(self):
        return Course.objects.filter(author=self.request.user).order_by('-updated_at')

class CourseSubmitReviewView(generics.GenericAPIView):
    """
    POST /creator/courses/{pk}/submit/
    将课程状态从 'draft' 或 'rejected' 变为 'pending_review'
    """
    permission_classes = [IsAuthenticated, IsArtist, IsOwner]

    def get_queryset(self):
        # 只允许操作自己处于可提交状态的课程
        return Course.objects.filter(
            author=self.request.user,
            status__in=[Course.StatusChoices.DRAFT, Course.StatusChoices.REJECTED]
        )

    def post(self, request, *args, **kwargs):
        course = self.get_object()
        
        # 最终验证
        if course.chapters.count() == 0:
            return Response(
                {"error": "课程至少需要包含一个章节才能提交审核。"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        # (未来可以增加更多验证，例如：每个章节是否都有视频URL？)

        course.status = Course.StatusChoices.PENDING_REVIEW
        course.save()
        
        # 返回更新后的课程状态
        return Response(
            {"status": course.status, "message": "已提交审核"}, 
            status=status.HTTP_200_OK
        )
    
class ChapterCreateView(generics.CreateAPIView):
    """
    POST /creator/courses/<course_pk>/chapters/
    为指定课程创建新章节
    """
    queryset = Chapter.objects.all()
    serializer_class = ChapterSerializer
    permission_classes = [IsAuthenticated, IsArtist]

    def perform_create(self, serializer):
        course = get_object_or_404(Course, pk=self.kwargs.get('course_pk'))
        
        if course.author != self.request.user:
            raise PermissionDenied("您不是该课程的作者，无法添加章节。")
            
        last_chapter_order = course.chapters.all().order_by('-order').first()
        new_order = last_chapter_order.order + 1 if last_chapter_order else 1
        serializer.save(course=course, order=new_order)

class ChapterDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET, PUT, PATCH, DELETE /creator/chapters/<pk>/
    更新或删除一个特定的章节
    """
    serializer_class = ChapterSerializer
    permission_classes = [IsAuthenticated, IsArtist] # 基础权限

    def get_queryset(self):
        return Chapter.objects.filter(course__author=self.request.user)

class ChapterOrderUpdateView(generics.GenericAPIView):
    """
    PUT /creator/courses/<course_pk>/chapters/order/
    批量更新章节顺序
    """
    permission_classes = [IsAuthenticated, IsArtist]

    def put(self, request, *args, **kwargs):
        course = get_object_or_404(Course, pk=self.kwargs.get('course_pk'))
        if course.author != request.user:
            raise PermissionDenied("您不是该课程的作者，无法排序。")
            
        chapter_ids = request.data.get('chapter_ids') # 期望收到一个 [3, 1, 2] 这样的ID列表
        
        if not isinstance(chapter_ids, list):
            return Response({"error": "无效的数据格式，需要一个 'chapter_ids' 列表。"}, status=status.HTTP_400_BAD_REQUEST)
            
        # 批量更新排序
        with transaction.atomic(): # 确保操作的原子性
            for index, chapter_id in enumerate(chapter_ids):
                Chapter.objects.filter(id=chapter_id, course=course).update(order=index + 1)
                
        return Response({"status": "顺序已更新"}, status=status.HTTP_200_OK)
class ExerciseCreateView(generics.CreateAPIView):
    """
    POST /creator/chapters/<chapter_pk>/exercises/
    为指定章节创建新练习
    """
    queryset = Exercise.objects.all()
    serializer_class = ExerciseSerializer
    permission_classes = [IsAuthenticated, IsArtist]
    parser_classes = [MultiPartParser, FormParser] # 支持图片上传

    def perform_create(self, serializer):
        chapter = get_object_or_404(Chapter, pk=self.kwargs.get('chapter_pk'))
        
        # 权限检查：必须是课程作者
        if chapter.course.author != self.request.user:
            raise PermissionDenied("您不是该课程的作者，无法添加练习。")
            
        serializer.save(chapter=chapter)

class ExerciseDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET, PUT, PATCH, DELETE /creator/exercises/<pk>/
    获取、更新或删除一个特定的练习题
    """
    serializer_class = ExerciseSerializer
    permission_classes = [IsAuthenticated, IsArtist] # 基础权限
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        # 确保用户只能操作自己课程下的练习题
        return Exercise.objects.filter(chapter__course__author=self.request.user)



class GalleryItemUpdateView(generics.RetrieveUpdateAPIView):
    """
    PUT /creator/gallery/{pk}/
    允许创作者编辑自己的画廊作品。
    """
    queryset = GalleryItem.objects.all()
    serializer_class = GalleryItemCreateSerializer
    permission_classes = [IsAuthenticated, IsArtist, IsOwner]
    parser_classes = [MultiPartParser, FormParser]

    def perform_update(self, serializer):
        serializer.save(status='draft')

class CommunityUpdateView(generics.RetrieveUpdateAPIView):
    """
    PUT /creator/communities/{pk}/
    允许创作者编辑自己创建的社群。
    """
    queryset = Community.objects.all()
    serializer_class = CommunityCreateSerializer
    permission_classes = [IsAuthenticated, IsArtist, IsOwner]
    parser_classes = [MultiPartParser, FormParser]
    
    def perform_update(self, serializer):
        serializer.save()