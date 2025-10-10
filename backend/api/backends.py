from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()

class MultiFieldAuthBackend:
    """
    自定义认证后端，支持使用 username, email, 或 phone 登录
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        # 注意：Django 认证框架会将用户输入的主要凭证统一作为 'username' 参数传来
        identifier = username
        try:
            # Q 对象允许我们使用 OR 条件进行查询
            user = User.objects.get(
                Q(username=identifier) | Q(email=identifier) | Q(phone=identifier)
            )
            # 检查密码是否正确
            if user.check_password(password):
                return user
        except User.DoesNotExist:
            # 未找到用户
            return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
