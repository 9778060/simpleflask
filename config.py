"""Config file"""
import datetime as dt
from kombu import Queue, Exchange


class Config(object):
    """Config class"""
    POSTS_PER_PAGE = 5
    RECAPTCHA_PUBLIC_KEY = "..."
    RECAPTCHA_PRIVATE_KEY = "..."
    TWITTER_API_KEY = "XXXX"
    TWITTER_API_SECRET = "XXXX"
    FACEBOOK_CLIENT_ID = "XXX"
    FACEBOOK_CLIENT_SECRET = "XXXX"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = "postgresql+psycopg2://...:...@127.0.0.1:5432/simpleflask"
    JWT_SECRET_KEY = "..."
    JWT_ACCESS_TOKEN_EXPIRES = dt.timedelta(minutes=15)
    CELERY_BROKER_URL = "amqp://...:...@localhost//"
    CELERY_RESULT_BACKEND = "rpc://...:...@localhost//"
    CELERY_IMPORTS = ("webapp.blog.tasks", )
    CELERY_TASK_DEFAULT_QUEUE = 'default'
    CELERY_TASK_DEFAULT_EXCHANGE = 'default'
    CELERY_TASK_DEFAULT_ROUTING_KEY = 'default'
    CELERYBEAT_SCHEDULE = {
        "log-every-30-seconds": {
            "task": "webapp.blog.tasks.log",
            "schedule": dt.timedelta(seconds=30),
            "args": ("Message", )
        },
        'weekly-digest': {
            'task': 'webapp.blog.tasks.digest',
            # 'schedule': crontab(day_of_week=6, hour='10')
            "schedule": dt.timedelta(seconds=30)
        }
    }
    SMTP_SERVER = "localhost"
    SMTP_USER = "..."
    # SMTP_PASSWORD = "..."
    SMTP_FROM = "from@flask.com"
    SERVER_NAME = '127.0.0.1:5000'
    MAIL_SERVER = "localhost"
    MAIL_PORT = 25
    MAIL_USERNAME = "..."
    MAIL_PASSWORD = "..."

class ProductionConfig(Config):
    """ProdConfig class"""
    DEBUG = False
    SECRET_KEY = "..."
    CACHE_TYPE = 'redis'
    CACHE_REDIS_HOST = 'localhost'
    CACHE_REDIS_PORT = '6379'
    CACHE_REDIS_PASSWORD = ''
    CACHE_REDIS_DB = '0'


class DevelopmentConfig(Config):
    """DevConfig class"""
    DEBUG = True
    DEBUG_TB_INTERCEPT_REDIRECTS = False
    SECRET_KEY = "..."
    CACHE_TYPE = 'redis'
    CACHE_REDIS_HOST = 'localhost'
    CACHE_REDIS_PORT = '6379'
    CACHE_REDIS_PASSWORD = ''
    CACHE_REDIS_DB = '0'
