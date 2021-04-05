from scrapy import Spider, Request, FormRequest
from vk.items import VkMessage, VkDialogue
from urllib.parse import urlencode
from urllib.parse import urlparse
from urllib.parse import parse_qs
import json
from vk import pipelines
from pprint import pprint
from bs4 import BeautifulSoup


class VkSpiderSpider(Spider):
    name = 'vk_spider'
    allowed_domains = ['vk.com']
    start_urls = ['http://vk.com/login']
    offset = 1000

    def parse(self, response):  # login function TODO two-factor bs
        email = input()
        password = input()
        # ip_h = response.xpath('//*[@id="login_form"]/*[@name="ip_h"]/@value').extract_first()
        # lg_h = response.xpath('//*[@id="login_form"]/*[@name="lg_h"]/@value').extract_first()
        action = response.xpath('//*[@id="mcont"]//form/@action').extract_first()
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
        yield Request(url="https://m.vk.com/mail", callback=self.scroll_im)
        pass

    def scroll_im(self, response):
        for currentOffset in range(0, self.offset, 20):
            yield FormRequest.from_response(response,
                                            formdata={"offset": str(currentOffset),
                                                      "_ajax": "1"},
                                            callback=self.parse_im)
        pass

    def parse_im(self, response):
        # chat_links = response.xpath('//*[@class="mailScrap__items mailScrap__items_folder"]//a/@href').extract()
        # chat_links = response.xpath('//*[@id="mcont"]/div/div[1]/div[2]/div/div[4]/div[1]/div/div[1]//div/a/@href').extract()
        # print(chat_links)
        html = response.body_as_unicode()
        soup = BeautifulSoup(html, 'lxml')
        soup = soup.find_all(lambda tag: tag.name == 'a' and
                                         tag.get('class') == ['dialog_item'])
        hrefs = []
        for a in soup:
            link = a.get('href')
            self.logger.info("fetched chat link: {}".format(link))
            hrefs.append(link)
            yield(Request(url="https://m.vk.com" + link, callback=self.parse_dialogue))
        pass

    def parse_dialogue(self, response):
        dialogue = VkDialogue()
        self.logger.info("visited chat: {}".format(response.url))
        parsed_url = urlparse(response.url)
        query = parse_qs(parsed_url.query)
        if 'chat' in query:
            dialogue["dType"] = 'chat'
            dialogue["id"] = query['chat'][0]
        else:
            if int(query["peer"][0]) > 0:
                dialogue["dType"] = 'person'
            else:
                dialogue["dType"] = 'group'
            dialogue["id"] = query['peer'][0]
        dialogue["name"] = response.xpath('//*[@class="mailHat__convoTitle"]/text()').extract_first()
        self.logger.info("dialogue: name: {}, id: {}, type: {}".format(dialogue["name"],
                                                                       dialogue["id"],
                                                                       dialogue["dType"]))
        pass