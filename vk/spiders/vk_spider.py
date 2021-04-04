from scrapy import Spider, Request, FormRequest
from vk.items import VkMessage
from urllib.parse import urlencode
import json
from vk import pipelines


class VkSpiderSpider(scrapy.Spider):
    name = 'vk_spider'
    allowed_domains = ['vk.com']
    start_urls = ['http://vk.com/']

    def parse(self, response):
        pass
