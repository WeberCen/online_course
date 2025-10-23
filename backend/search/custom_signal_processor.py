from django_elasticsearch_dsl.signals import RealTimeSignalProcessor
from .tasks import update_index_task, delete_index_task

class CelerySignalProcessor(RealTimeSignalProcessor):
    """
    自定义信号处理器，将索引更新操作推送到 Celery 队列。
    """

    def handle_save(self, sender, instance, **kwargs):
        """
        处理模型保存信号，异步更新索引。
        """
        # (重写) 不再是实时处理，而是调用 .delay()
        update_index_task.delay(instance._meta.app_label, instance._meta.model_name, instance.pk)

    def handle_delete(self, sender, instance, **kwargs):
        """
        处理模型删除信号，异步删除索引。
        """
        # (重写)
        delete_index_task.delay(instance._meta.app_label, instance._meta.model_name, instance.pk)

    def handle_m2m_changed(self, sender, instance, action, **kwargs):
        """
        处理 ManyToMany 字段变化信号（例如 'tags' 字段增删）
        """
        if action in ('post_add', 'post_remove', 'post_clear'):
            # (重写) 同样是异步更新
            update_index_task.delay(instance._meta.app_label, instance._meta.model_name, instance.pk)