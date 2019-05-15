#!/usr/bin/python3
# -*- coding: utf-8 -*-
from urllib import parse

import scrapy

import re
import json
import jsonpath
from bookspider.items import BookItem

from bookspider.settings import DEPLOY_PROJECT

if DEPLOY_PROJECT:
    from scrapy_redis.spiders import RedisSpider as Spider
else:
    from scrapy.spiders import Spider


class SuningSpider(Spider):
    # 指定名称
    name = "suning"

    allowed_domains = ['suning.com']

    start_urls = ['https://ipservice.suning.com/ipQuery.do']

    redis_key = "book:suning:start_url"

    total_page_pattern = re.compile(r'param.pageNumbers = "(.*?)";')
    ci_pattern = re.compile(r'-(.*?)-')

    def parse(self, response):
        ipquery = json.loads(response.body.decode('utf-8'))

        yield scrapy.Request(
            url="https://book.suning.com/",
            callback=self.parse_cate,
            meta={
                "ipquery": ipquery
            }
        )

    def parse_cate(self, response):
        # 一级分类提取
        cat_1_titles = response.xpath('//div[@class="menu-item"]/dl/dt//a/text()').extract()

        # 获取二级菜单的 div块 列表
        menu_sub_divs = response.css('.menu-sub')

        for cat_1_title, menu_sub_div in zip(cat_1_titles, menu_sub_divs):
            # 二级分类的标题
            cat_2_titles = menu_sub_div.xpath('./div[@class="submenu-left"]/p//a/text()').extract()

            # 二级分类的ul块
            cat_2_uls = menu_sub_div.xpath('./div[@class="submenu-left"]/ul')

            for index, cat_2_ul in enumerate(cat_2_uls):

                cat_2_title = "暂无"
                if index < len(cat_2_titles):
                    cat_2_title = cat_2_titles[index]

                # 获取三级分类标题
                cat_3_titles = cat_2_ul.xpath('./li/a/text()').extract()

                # 获取三级分类超链接
                cat_3_hrefs = cat_2_ul.xpath('./li/a/@href').extract()

                for cat_3_title, cat_3_href in zip(cat_3_titles, cat_3_hrefs):
                    print(cat_1_title, '=>', cat_2_title, '=>', cat_3_title, "=>", cat_3_href)
                    yield scrapy.Request(
                        url=cat_3_href,
                        callback=self.parse_list,
                        meta={
                            "cat_1": cat_1_title,
                            "cat_2": cat_2_title,
                            "cat_3": cat_3_title,
                            "ipquery": response.meta["ipquery"]
                        }
                    )

    def parse_list(self, response):
        '''
        真正数据请求地址
        https://list.suning.com/emall/showProductList.do?
        ci=262669
        pg=03
        paging=1    paging 0表示上半部分30条，1表示下半部分30
        cp: 0  表示页数,

        计算总数
        可以采取两种方案,第一种提取 分页的总数
        第二种可以直接网页中总页数的变量进行提取
        param.pageNumbers = "67";
        '''
        html = response.body.decode('utf-8')
        total_pages = int(self.total_page_pattern.findall(html)[0])

        base_url = "https://list.suning.com/emall/showProductList.do?ci={}&pg=03&paging={}&cp={}"
        flag = False
        ci = ""
        try:
            ci = self.ci_pattern.findall(response.url)[0]
        except IndexError:
            flag = True

        for cp in range(0, 1, 1):
            # 请求上半部分
            paging = 0
            if flag:
                url = 'https://search.suning.com/emall/searchProductList.do?keyword={}&pg=01&cp={}&paging={}'.format(
                    response.meta['cat_3'],paging,cp)
            url = base_url.format(ci, paging, cp)
            yield scrapy.Request(
                url=url,
                callback=self.parse_list_cotent,
                meta=response.meta
            )

            # 请求下半部分
            paging = 1
            if flag:
                url = 'https://search.suning.com/emall/searchProductList.do?keyword={}&pg=01&cp={}&paging={}'.format(
                    response.meta['cat_3'], paging, cp)
            url = base_url.format(ci, paging, cp)
            yield scrapy.Request(
                url=url,
                callback=self.parse_list_cotent,
                meta=response.meta
            )

    def parse_list_cotent(self, response):
        # 真正解析列表数据
        detail_hrefs = response.xpath('//p[@class="sell-point"]/a[@class="sellPoint"]/@href').extract()
        book_image_urls = response.xpath('//img[@class="search-loading"]/@src2').extract()
        venders = response.xpath('//p[contains(@class,"seller")]/a/text()').extract()


        for detail_href, book_image_url, vender, in zip(detail_hrefs, book_image_urls, venders):
            yield scrapy.Request(
            url="https:" + detail_href,
            callback=self.parse_detail,
            meta={"book_image_url": parse.urljoin(response.url, book_image_url),
            "vender": vender,
            "data":response.meta}
            )

    def parse_detail(self, response):
        comment_dict = "".join(map(lambda x: x.replace("'", ""), response.xpath('//div[contains(@class,"favorite")]/a/@sa-data').extract_first()))
        name = response.xpath('//h1[@id="itemDisplayName"]/text()').extract_first()
        if name is not None:
            name = name.strip()

        ipquery = response.meta["data"]["ipquery"]
        html = response.body.decode('utf-8')

        luaUrl = "https:" + re.findall(r'"luaUrl":"(.*?)"', html)[0]
        passPartNumber = re.findall(r'"passPartNumber":"(.*?)",', html)[0]
        partNumber = re.findall(r'"partNumber":"(.*?)",', html)[0]
        vendorCode = re.findall(r'"vendorCode":"(.*?)",', html)[0]
        provinceCode = ipquery["provinceCommerceId"]
        lesCityId = ipquery["cityLESId"]
        a = lesCityId + ipquery["districtLESId"] + "01";
        category1 = re.findall(r'"category1":"(.*?)",', html)[0]
        mdmCityId = ipquery["cityMDMId"]
        cityId = ipquery["cityCommerceId"]
        districtId = ipquery["districtCommerceId"]
        cmmdtyType = re.findall(r'"cmmdtyType":"(.*?)",', html)[0]
        custLevel = ""

        mountType = re.findall(r'"mountType":"(.*?)",', html)[0]

        if mountType != '03':
            b = ""
        else:
            b = mountType

        catenIds = re.findall(r'"catenIds":"(.*?)",', html)[0]
        weight = re.findall(r'"weight":"(.*?)",', html)[0]
        e = ""

        price_url = luaUrl + "/nspcsale_0_" + passPartNumber + "_" + partNumber + "_" + vendorCode + "_" + provinceCode + "_" + lesCityId + "_" + a + "_" + category1 + "_" + mdmCityId + "_" + cityId + "_" + districtId + "_" + cmmdtyType + "_" + custLevel + "_" + b + "_" + catenIds + "_" + weight + "___" + e + ".html";

        yield scrapy.Request(
            url=price_url,
            callback=self.parse_price,
            meta={
                "name": name,
                "cat_1": response.meta["data"]["cat_1"],
                "cat_2": response.meta["data"]["cat_2"],
                "cat_3": response.meta["data"]["cat_3"],
                "ipquery": ipquery,
                "comment_dict": comment_dict,
                "book_image_url":response.meta["book_image_url"],
                "vender":response.meta["vender"]
            }
        )

    def parse_price(self, response):
        item = BookItem()
        item["name"] = response.meta["name"]

        # 解析价格
        string = response.body.decode('utf-8')

        string = re.findall(r'pcData\((.*)\)', string, re.DOTALL)[0]

        result = json.loads(string)

        price = jsonpath.jsonpath(result, '$..netPrice')
        if price is not None and len(price) > 0:
            item["price"] = price[0]
            prdid = re.findall("prdid:(\d+)",response.meta['comment_dict'])[0]
            shopid = re.findall("shopid:(\d+)",response.meta['comment_dict'])[0]

            comment_count_url = f"https://review.suning.com/ajax/review_satisfy/general-{prdid}-{shopid}-----noGoodsSatisfy.htm"
            response.meta.update({"item": item})

            yield scrapy.Request(comment_count_url,
                                 callback=self.parse_comment,
                                 meta=response.meta)

    def parse_comment(self, response):
        comment_info_dict = eval(response.text.replace("noGoodsSatisfy(",'').replace(")",""))
        comment = comment_info_dict["reviewCounts"][0]["totalCount"]
        item = response.meta["item"]
        item["comment"] = comment
        item['category1'] = response.meta['cat_1']
        item['category2'] = response.meta['cat_2']
        item['category3'] = response.meta['cat_3']
        item['book_image_url'] = response.meta['book_image_url']
        item['vender'] = response.meta['vender']

        yield item
