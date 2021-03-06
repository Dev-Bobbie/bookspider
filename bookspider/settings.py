# -*- coding: utf-8 -*-

# Scrapy settings for bookspider project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://doc.scrapy.org/en/latest/topics/settings.html
#     https://doc.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://doc.scrapy.org/en/latest/topics/spider-middleware.html

BOT_NAME = 'bookspider'

COMMANDS_MODULE = 'bookspider.commands'
SPIDER_MODULES = ['bookspider.spiders']
NEWSPIDER_MODULE = 'bookspider.spiders'


# LOG_LEVEL = "INFO"
# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = 'bookspider (+http://www.yourdomain.com)'

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# Configure maximum concurrent requests performed by Scrapy (default: 16)
#CONCURRENT_REQUESTS = 32

# Configure a delay for requests for the same website (default: 0)
# See https://doc.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
#DOWNLOAD_DELAY = 3
# The download delay setting will honor only one of:
#CONCURRENT_REQUESTS_PER_DOMAIN = 16
#CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
#TELNETCONSOLE_ENABLED = False

# Override the default request headers:
#DEFAULT_REQUEST_HEADERS = {
#   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
#   'Accept-Language': 'en',
#}

# Enable or disable spider middlewares
# See https://doc.scrapy.org/en/latest/topics/spider-middleware.html
#SPIDER_MIDDLEWARES = {
#    'bookspider.middlewares.BookspiderSpiderMiddleware': 543,
#}

# Enable or disable downloader middlewares
# See https://doc.scrapy.org/en/latest/topics/downloader-middleware.html
#DOWNLOADER_MIDDLEWARES = {
#    'bookspider.middlewares.BookspiderDownloaderMiddleware': 543,
#}
DOWNLOADER_MIDDLEWARES = {
    'bookspider.middlewares.RandomUserAgentMiddlware': 543,
    #'bookspider.middlewares.ProxyMiddleware': 544,
    'bookspider.middlewares.DownloadRetryMiddleware': 545,
    'scrapy.downloadermiddlewares.retry.RetryMiddleware': None,
    'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None
}

# Enable or disable extensions
# See https://doc.scrapy.org/en/latest/topics/extensions.html
#EXTENSIONS = {
#    'scrapy.extensions.telnet.TelnetConsole': None,
#}

# Configure item pipelines
# See https://doc.scrapy.org/en/latest/topics/item-pipeline.html
#ITEM_PIPELINES = {
#    'bookspider.pipelines.BookspiderPipeline': 300,
#}

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://doc.scrapy.org/en/latest/topics/autothrottle.html
#AUTOTHROTTLE_ENABLED = True
# The initial download delay
#AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
#AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
#AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
#AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See https://doc.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
#HTTPCACHE_ENABLED = True
#HTTPCACHE_EXPIRATION_SECS = 0
#HTTPCACHE_DIR = 'httpcache'
#HTTPCACHE_IGNORE_HTTP_CODES = []
#HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'

DEPLOY_PROJECT = False

if DEPLOY_PROJECT :
   # scrapy-redis 增量爬虫配置
   # 1. 设置请求调度器采用 scrapy-redis 实现方案
   SCHEDULER = "scrapy_redis.scheduler.Scheduler"
   # 2. 设置过滤类，实现去重功能
   DUPEFILTER_CLASS = "scrapy_redis.dupefilter.RFPDupeFilter"
   # 3. 配置redis
   REDIS_HOST = '10.211.55.4'
   REDIS_PORT = 6379
   # 4. 设置持久化，当程序结束时是否清空 SCHEDULER_PERSIST 默认 False,如果程序结束自动清空
   SCHEDULER_PERSIST = True

   ITEM_PIPELINES = {
      'bookspider.pipelines.BookSourcePipeline':100,
      'scrapy_redis.pipelines.RedisPipeline': 300
   }

else:
   ITEM_PIPELINES = {
      'bookspider.pipelines.BookSourcePipeline': 100,
      'bookspider.pipelines.BookPipeline': 300,
   }
import asyncio
try:
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

except ImportError:
    pass

loop = asyncio.get_event_loop()
