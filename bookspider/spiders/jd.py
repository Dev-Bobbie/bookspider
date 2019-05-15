# -*- coding: utf-8 -*-
import asyncio
from urllib import parse

import scrapy
import json

from bookspider.items import BookItem

from bookspider.settings import DEPLOY_PROJECT
from bookspider.utils import fetch

if DEPLOY_PROJECT:
    from scrapy_redis.spiders import RedisSpider as Spider
else:
    from scrapy import Spider

class JdSpider(Spider):
    name = 'jd'
    allowed_domains = ['jd.com','p.3.cn']
    start_urls = ['https://book.jd.com/booksort.html']

    redis_key = "book:jd:start_url"

    def parse(self, response):

        #  分类提取
        cat_1_titles = response.xpath('//div[@class="mc"]/dl/dt/a/text()').extract()

        dd_list = response.xpath('//div[@class="mc"]/dl/dd')

        for cat_1_title,dd in zip(cat_1_titles,dd_list):
            cat_2_titles = dd.xpath('.//a/text()').extract()
            cat_2_hrefs = dd.xpath('.//a/@href').extract()

            for cat_2_title,cat_2_href in zip(cat_1_titles,cat_2_hrefs):
                print(cat_1_title,"=>",cat_2_title,"=>",cat_2_href)
                yield scrapy.Request(
                    url="https:"+cat_2_href,
                    callback=self.parse_list,
                    meta={
                        "cat_1_title":cat_1_title,
                        "cat_2_title":cat_2_title
                    }
                )

    def parse_list(self,response):
        li_list = response.xpath('//li[@class="gl-item"]')
        items = []
        data_sku_list = []
        venderid_set = set()
        for li in li_list:
            item = {}
            item["name"] = li.xpath('.//div[@class="p-name"]//em/text()').extract_first().strip()
            item["book_image_url"] = parse.urljoin(response.url,li.xpath('.//div[@class="p-img"]/a/img/@src').extract_first())

            data_sku = li.xpath('./div[@class="gl-i-wrap j-sku-item"]/@data-sku').extract_first()
            venderid = li.xpath('./div[@class="gl-i-wrap j-sku-item"]/@venderid').extract_first()
            if data_sku is not None:
                item["data_sku"] = data_sku
                item["venderid"] = venderid
                item["category1"] = response.meta["cat_1_title"]
                item["category2"] = response.meta["cat_2_title"]
                if venderid != "0":
                    venderid_set.add(venderid)

                data_sku_list.append(data_sku)
                items.append(item)

        venderid_list = list(venderid_set)
        step = 10
        cut_vender = [venderid_list[i:i + step] for i in range(0, len(venderid_list), step)]
        vender_map = []
        for cut in cut_vender:

            vender_ids = ",".join(cut)
            venderid_url = 'https://rms.shop.jd.com/json/pop/shopInfo.action?ids='+ vender_ids
            html = json.loads(fetch(venderid_url))
            vender_map.extend(html)


        venders_dict = dict([[vender["venderId"], vender] for vender in vender_map])
        for item in items:
            if item["venderid"] != "0":
                vender_dict = venders_dict[item["venderid"]]
                if vender_dict is not None:
                    item.update({"vender": vender_dict["name"]})
            else:
                item.update({"vender": "京东自营"})

        skuIds = ",".join(data_sku_list)
        comment_url = "https://club.jd.com/comment/productCommentSummaries.action?referenceIds=" + skuIds
        yield scrapy.Request(
            url=comment_url,
            callback=self.parse_comments,
            meta={
                "items": items,
                'skuIds': data_sku_list,
            }
        )

        # 处理下一页
        next_url = response.xpath('//a[@class="pn-next"]/@href').extract_first()
        if next_url is not None:
            next_url = "https://list.jd.com/"+next_url
            yield scrapy.Request(
                url=next_url,
                callback=self.parse_list,
                meta=response.meta
            )

    def parse_comments(self, response):

        '''
        items 数据格式
        [
            {'data_sku': '11757834', 'name': '中国科幻基石丛书：三体（套装1-3册）'},
            {'data_sku': '12090377', 'name': '平凡的世界：全三册'},
            ...
        ]
        '''
        items = response.meta["items"]
        skuIds = ",".join(map(lambda x:"J_"+x,response.meta["skuIds"]))

        '''
       {
        "CommentsCount": [
        {
            "SkuId": 12475106,
            "ProductId": 12475106,
            "ShowCount": 7800,
            "ShowCountStr": "7800+",
            "CommentCountStr": "27万+",
                }
             ]
        }
        '''
        comments = json.loads(response.text)["CommentsCount"]

        comments_dict = dict([[str(comment["SkuId"]), comment] for comment in comments])

        for item in items:
            comment_dict = comments_dict[item["data_sku"]]
            if comment_dict is not None:
                item.update({"comment":comment_dict["CommentCountStr"]})

        price_url = "https://p.3.cn/prices/mgets?skuIds=" + skuIds
        # 发送一个获取价格的请求，获取价格的列表
        yield scrapy.Request(
            url=price_url,
            callback=self.parse_prices,
            meta={
                "items": items,
            }
        )

    def parse_prices(self,response):

        '''
        items 数据格式
        [
            {'data_sku': '11757834', 'name': '中国科幻基石丛书：三体（套装1-3册）'},
            {'data_sku': '12090377', 'name': '平凡的世界：全三册'},
            ...
        ]
        '''
        items = response.meta["items"]

        '''
        prices 数据格式
        [
            {'id': 'J_11757834', 'm': '93.00', 'op': '55.80', 'p': '55.80'},
            {'id': 'J_12090377', 'm': '108.00', 'op': '81.00', 'p': '81.00', 'tpp': '79.00','up': 'tpp'}
        ]
        转换
        {
            "J_11757834":{'id': 'J_11757834', 'm': '93.00', 'op': '55.80', 'p': '55.80'},
            "J_12090377":{'id': 'J_12090377', 'm': '108.00', 'op': '81.00', 'p': '81.00', 'tpp': '79.00','up': 'tpp'}
        }
        '''
        prices = json.loads(response.text)

        prices_dict = dict([[price_dict["id"],price_dict] for price_dict in prices])

        for item in items:
            price_dict = prices_dict["J_"+ item["data_sku"]]
            if price_dict is not None:
                bookItem = BookItem()
                bookItem["price"] = price_dict["op"]
                bookItem["name"] = item["name"]
                bookItem["comment"] = item["comment"]
                bookItem["vender"] = item["vender"]
                bookItem["book_image_url"] = item["book_image_url"]
                bookItem["category1"] = item["category1"]
                bookItem["category2"] = item["category2"]
                bookItem["category3"] = "暂无"

                yield bookItem

