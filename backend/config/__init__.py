from __future__ import absolute_import, unicode_literals

import os

from celery import Celery

# 1. 设置 Django 环境
# 这一步是为了让 Celery 知道去哪里找到 Django 的 settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# 2. 创建 Celery 应用程序实例
# 注意：实例名必须是 'celery'，这样 docker-compose.yml 中的命令才能找到它。
celery = Celery('your_project_name') 

# 3. 从 Django settings 文件中读取配置
# 这里的 'celery' 命名空间意味着所有以 CELERY_ 开头的设置都属于 Celery
celery.config_from_object('django.conf:settings', namespace='CELERY')

# 4. 自动发现 Django 应用中的任务
# 这一行让 Celery 自动在所有的 INSTALLED_APPS 中寻找 tasks.py 文件
celery.autodiscover_tasks()