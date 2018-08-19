from celery import Celery
from . import config
import os

# 设置Django的配置
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "meiduo.settings")

# 创建对象
app = Celery('meiduo')
# 加载配置
app.config_from_object(config)

# 初始化任务
# 在指定的包中找tasks.py文件，在这个文件中找@app.task函数
app.autodiscover_tasks([
    'celery_tasks.sms',

])