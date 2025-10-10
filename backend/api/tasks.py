
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings

@shared_task
def send_verification_code_email(email, code):
    """
    发送密码重置验证码邮件的异步任务
    """
    subject = '【本末实验室】密码重置验证码'
    message = f'您好，\n\n您的密码重置验证码是：{code}\n\n该验证码10分钟内有效，请勿泄露给他人。\n\n本末实验室'
    from_email = settings.DEFAULT_FROM_EMAIL or 'noreply@yourproject.com'
    recipient_list = [email]
    
    send_mail(subject, message, from_email, recipient_list)
    
    return f"Verification code email sent to {email}"