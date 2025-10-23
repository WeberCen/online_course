from celery import shared_task
from django.apps import apps
import logging
from django_elasticsearch_dsl.registries import registry

logger = logging.getLogger(__name__)

@shared_task(name="search.update_index")
def update_index_task(app_label, model_name, pk):
    """
    异步任务：更新单个对象的 ES 索引
    """
    try:
        model = apps.get_model(app_label, model_name)
        instance = model.objects.get(pk=pk) # 从数据库获取最新的实例
        
        # 遍历所有注册的 Document，找到匹配的
        for doc in registry.get_documents(models=[model]):
            doc().update(instance) # 更新 ES 索引
            
        logger.info(f"Successfully updated index for {model_name} {pk}")
        
    except model.DoesNotExist:
        # 这种情况可能发生在：对象刚创建马上就被删了
        logger.warning(f"{model_name} with pk={pk} not found for update. Skipping.")
    except Exception as e:
        logger.error(f"Error updating index for {model_name} {pk}: {e}")
        # 失败时重试（例如 ES 暂时连接不上）
        raise update_index_task.retry(exc=e, countdown=60)


@shared_task(name="search.delete_index")
def delete_index_task(app_label, model_name, pk):
    """
    异步任务：从 ES 索引中删除单个对象
    """
    try:
        model = apps.get_model(app_label, model_name)
        
        for doc in registry.get_documents(models=[model]):
            # 获取 ES 索引的名称, e.g., 'courses'
            index_name = doc._index._name
            # 获取底层的 es-py 客户端
            es_client = doc._get_connection()
            
            try:
                # 按 ID 从 ES 中删除（ID 默认就是 Django 的 PK）
                es_client.delete(index=index_name, id=pk, ignore=[404]) # ignore[404] 避免"已删除"时报错
                logger.info(f"Successfully deleted index doc {pk} from {index_name}")
            except Exception as e:
                 logger.error(f"Error deleting index doc {pk} from {index_name}: {e}")
                 # 失败时重试
                 raise delete_index_task.retry(exc=e, countdown=60)
                 
    except Exception as e:
        # (例如 apps.get_model 失败)
        logger.error(f"Error in delete_index_task for {app_label}.{model_name} {pk}: {e}")