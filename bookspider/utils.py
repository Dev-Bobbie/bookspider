import asyncio
from functools import wraps

import requests
from motor.motor_asyncio import AsyncIOMotorClient
import os
try:
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

except ImportError:
    pass


MONGODB = dict(
    MONGO_HOST=os.getenv('MONGO_HOST', "mongo"),
    MONGO_PORT=os.getenv('MONGO_PORT', 27017),
    MONGO_USERNAME=os.getenv('MONGO_USERNAME', ""),
    MONGO_PASSWORD=os.getenv('MONGO_PASSWORD', ""),
    DATABASE='test_mongodb',
)


def singleton(cls):
    """
    :param cls: cls
    :return: instance
    """
    _instances = {}

    @wraps(cls)
    def instance(*args, **kw):
        if cls not in _instances:
            _instances[cls] = cls(*args, **kw)
        return _instances[cls]

    return instance


@singleton
class MotorBase:
    """
    更改mongodb连接方式 单例模式下支持多库操作
    About motor's doc: https://github.com/mongodb/motor
    """
    _db = {}
    _collection = {}
    MONGODB = MONGODB

    def __init__(self):
        self.motor_uri = ''

    def client(self, db):
        # motor
        self.motor_uri = 'mongodb://{account}{host}:{port}/{database}'.format(
            account='{username}:{password}@'.format(
                username=self.MONGODB['MONGO_USERNAME'],
                password=self.MONGODB['MONGO_PASSWORD']) if self.MONGODB['MONGO_USERNAME'] else '',
            host=self.MONGODB['MONGO_HOST'] if self.MONGODB['MONGO_HOST'] else 'localhost',
            port=self.MONGODB['MONGO_PORT'] if self.MONGODB['MONGO_PORT'] else 27017,
            database=db)
        return AsyncIOMotorClient(self.motor_uri)

    def get_db(self, db=MONGODB['DATABASE']):
        """
        获取一个db实例
        :param db: database name
        :return: the motor db instance
        """
        if db not in self._db:
            self._db[db] = self.client(db)[db]

        return self._db[db]

    def get_collection(self, db_name, collection):
        """
        获取一个集合实例
        :param db_name: database name
        :param collection: collection name
        :return: the motor collection instance
        """
        collection_key = db_name + collection
        if collection_key not in self._collection:
            self._collection[collection_key] = self.get_db(db_name)[collection]

        return self._collection[collection_key]




import aiohttp

from talospider.utils import get_random_user_agent
REQUEST_TIMEOUT = 0
REQUEST_DELAY = 0
HEADERS = {"User-Agent":get_random_user_agent()}

async def _get_page(url, sleep, headers):
    """
    获取并返回网页内容
    """
    async with aiohttp.ClientSession() as session:
        try:
            await asyncio.sleep(sleep)
            async with session.get(
                    url, headers=headers, timeout=REQUEST_TIMEOUT
            ) as resp:
                return await resp.text()
        except:
            return ""


def fetch(url, sleep=REQUEST_DELAY, headers=HEADERS):
    """
    请求方法，用于获取网页内容

    :param url: 请求链接
    :param sleep: 延迟时间（秒）
    """
    loop = asyncio.get_event_loop()
    html = loop.run_until_complete(_get_page(url, sleep, headers=headers))
    if html:
        return html

