from scrapy import Spider, Request, FormRequest
from vk.items import VkMessage
from urllib.parse import urlencode
from urllib.parse import urlparse
from urllib.parse import parse_qs
import json
from vk import pipelines


class VkSpiderSpider(Spider):
    name = 'vk_spider'
    allowed_domains = ['vk.com']
    start_urls = ['http://vk.com/login']

    def parse(self, response):  # login function TODO two-factor bs
        email = input()
        password = input()
        # ip_h = response.xpath('//*[@id="login_form"]/*[@name="ip_h"]/@value').extract_first()
        # lg_h = response.xpath('//*[@id="login_form"]/*[@name="lg_h"]/@value').extract_first()
        action = response.xpath('//*[@id="mcont"]//form/@action').extract_first()
        print("FFFFFFFFFFFFFFFFFFFFFFFFFFF")
        print(action)
        print("FFFFFFFFFFFFFFFFFFFFFFFFFFF")
        parsed_action = urlparse(action)
        action_query = parse_qs(parsed_action.query)
        ip_h = action_query["ip_h"][0]
        lg_h = action_query["lg_h"][0]
        self.logger.info("got ip_h: {}".format(ip_h))
        self.logger.info("got lg_h: {}".format(lg_h))
        yield FormRequest.from_response(response,
                                        formdata={"act": "login",
                                                  "role": "al_frame",
                                                  "expire": "",
                                                  "to": "bG9naW4-",  # bG9naW4-
                                                  "recaptcha": "",
                                                  "captcha_sid": "",
                                                  "captcha_key": "",
                                                  "_origin": "https://vk.com",
                                                  "ip_h": ip_h,
                                                  "lg_h": lg_h,
                                                  "ul": "",
                                                  "email": email,
                                                  "pass": password},
                                        callback=self.after_login)
        pass

    def after_login(self, response):
        yield Request(url="https://vk.com/im", callback=self.parse_im)
        pass

    def parse_im(self, response):
        print("parsing imimim")
        pass