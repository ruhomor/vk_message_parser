from scrapy import Spider, Request, FormRequest
from vk.items import VkMessage
from urllib.parse import urlencode
import json
from vk import pipelines


class VkSpiderSpider(Spider):
    name = 'vk_spider'
    allowed_domains = ['vk.com']
    start_urls = ['http://vk.com/login']

    def parse(self, response):  # login function
        email = input()
        password = input()
        ip_h = response.xpath('//*[@id="login_form"]/*[@name="ip_h"]/@value').extract_first()
        lg_h = response.xpath('//*[@id="login_form"]/*[@name="lg_h"]/@value').extract_first()
        self.logger.log("got ip_h: {}".format(ip_h))
        self.logger.log("got lg_h: {}".format(ip_h))
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
        if "Error while logging in" in response.body:
            self.logger.error("Login failed!")
        else:
            self.logger.error("Login succeeded!")
            item = VkMessage()
            item["quote"] = response.css(".text").extract()
            item["author"] = response.css(".author").extract()
            return item
