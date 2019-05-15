# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html

import asyncio
from bookspider.settings import loop
from bookspider.utils import MotorBase


class BookSourcePipeline(object):
    def process_item(self, item, spider):
        item["source"] = spider.name
        return item


class BookPipeline(object):

    def open_spider(self, spider):
        self.client = MotorBase()
        self.db = self.client.get_db(spider.name)

    async def do_insert(self, db, item):
        asyncio.ensure_future(db.items.update_one(
            {'name': item.get("name"), 'price': item.get("price")},
            {'$set': item},
            upsert=True))
        # asyncio.ensure_future(db.items.insert_one(dict(item)))

    def process_item(self, item, spider):
        loop.run_until_complete(self.do_insert(self.client._db[spider.name], dict(item)))

        return item