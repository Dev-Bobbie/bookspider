from scrapy.commands.crawl import Command
from scrapy.exceptions import UsageError
from logging import getLogger

logger = getLogger(__name__)

class CustomCrawlCommand(Command):
    def run(self, args, opts):

        spider_settings = self.settings.getdict('SPIDER_SETTINGS', {})
        self.settings.update(spider_settings, priority='cmdline')
        spider_loader = self.crawler_process.spider_loader
        for spidername in args or spider_loader.list():
            logger.info(f">>>>>>>>>>>>>>>>>crawlspider [{spidername}]>>>>>>>>>>>>>>>>>")
            self.crawler_process.crawl(spidername, **opts.spargs)
        self.crawler_process.start()

