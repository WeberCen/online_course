"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path,include
from django.conf import settings
from django.conf.urls.static import static
from django.apps import apps
from api.views import dashboard_view


# ---------------------------------------------------
# --- 1. 建我们自定义的后台站点 ---
# ---------------------------------------------------
class MyAdminSite(admin.AdminSite):
    site_header = '本末实验室运营管理后台'
    site_title = '本末实验室'
    
    def get_app_list(self, request, app_label=None):
        """
        重组后台首页的模块。
        """
        app_dict = self._build_app_dict(request)
        review_center_app = {"name": "审核中心", "app_label": "review_center", "models": []}
        
        api_app = app_dict.get('api')
        if api_app:
            remaining_models = []
            for model in api_app['models']:
                if model['object_name'].startswith('Pending'):
                    review_center_app['models'].append(model)
                else:
                    remaining_models.append(model)
            api_app['models'] = remaining_models
        
        app_list = sorted(list(app_dict.values()), key=lambda x: x['name'].lower())
        
        # 只有在审核中心有内容时才显示
        if review_center_app['models']:
            app_list.insert(0, review_center_app)
        
        return app_list
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('dashboard/', self.admin_view(dashboard_view), name='dashboard'),
        ]
        return custom_urls + urls

# ---------------------------------------------------
# --- 2. 实例化并注册 ---
# ---------------------------------------------------
site = MyAdminSite(name='admin')


for model, model_admin in admin.site._registry.items():
    try:
        site.register(model, model_admin.__class__)
    except admin.sites.AlreadyRegistered:
        pass

# ---------------------------------------------------
# --- 3. 自动发现并注册所有模型到我们的新站点 ---
# ---------------------------------------------------
from api.admin import *
from api.models import *

for name, var in locals().copy().items():
    if isinstance(var, type) and issubclass(var, admin.ModelAdmin) and var is not admin.ModelAdmin:
        model_name = name.replace("Admin", "")
        model = locals().get(model_name)
        if model and not site.is_registered(model):
            site.register(model, var)
# ---------------------------------------------------
# --- 4. 最终的 URL Patterns ---
# ---------------------------------------------------
urlpatterns = [
    path('admin/', site.urls),
    path('v1/', include('api.urls')),
    path('tinymce/', include('tinymce.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)