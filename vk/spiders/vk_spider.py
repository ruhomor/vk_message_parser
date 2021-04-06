from scrapy import Spider, Request, FormRequest
from vk.items import VkMessage, VkDialogue
from urllib.parse import urlencode
from urllib.parse import urlparse
from urllib.parse import parse_qs
import json
from vk import pipelines
from pprint import pprint
from bs4 import BeautifulSoup
from selenium import webdriver
# from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.support.ui import WebDriverWait
import os.path
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.keys import Keys
from os import path
import shutil
import time
from vk.settings import PROFILESTORAGEPATH, PROFILE
from scrapy_selenium import SeleniumRequest


class VkSpiderSpider(Spider):
    name = 'vk_spider'
    allowed_domains = ['vk.com']
    start_urls = ['https://vk.com/']

    def save_profile(self):
        # driver.execute_script("window.close()")
        # time.sleep(0.5)
        currentProfilePath = self.driver.capabilities[PROFILE]
        if path.exists(PROFILESTORAGEPATH):
            shutil.rmtree(PROFILESTORAGEPATH)
        shutil.copytree(currentProfilePath, PROFILESTORAGEPATH,
                        ignore_dangling_symlinks=True)

    def scroll_down_im(self):
        # Get scroll height
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        # wait till page loads
        el = WebDriverWait(self.driver, timeout=60).until(lambda d: d.find_element_by_id("im_dialogs"))
        el = self.driver.find_element_by_tag_name("body")
        pcounter = 0
        self.update_dialogues()
        while pcounter < self.dialogues_count:
            pcounter = self.dialogues_count
            for i in range(100):
                el.send_keys(Keys.ARROW_DOWN)
                time.sleep(0.1)
            time.sleep(1)
            self.update_dialogues()
        pass

    def after_login(self):
        el = WebDriverWait(self.driver, timeout=60).until(lambda d: d.find_element_by_xpath('//*[@id="l_msg"]/a'))
        time.sleep(5)
        el.click()
        el.click()
        self.scroll_down_im()
        pass

    def sign_in(self):
        self.driver.get("https://www.vk.com/")
        self.driver.find_element_by_id("index_email").send_keys(self.username)
        # find password input field and insert password as well
        self.driver.find_element_by_id("index_pass").send_keys(self.password)
        # click login button
        self.driver.find_element_by_id("index_login_button").click()

        time.sleep(5)
        if self.driver.current_url == "https://vk.com/login?act=authcheck":
            el = WebDriverWait(self.driver, timeout=60).until(lambda d: d.find_element_by_id("authcheck_code"))
            el.send_keys(input())
        # self.driver.find_element_by_id("authcheck_code").send_keys(input())
            self.driver.find_element_by_id("login_authcheck_submit_btn").click()
        self.after_login()
        self.save_profile()  # no need in signing in again
        pass

    def check_login_status(self):
        self.driver.get("https://www.vk.com/feed")
        time.sleep(3)
        if "feed" in self.driver.current_url:
            self.after_login()
        else:
            self.sign_in()


    def __init__(self):
        f = open("email_password.txt", 'r')
        self.username, self.password = f.readline().split()
        self.dialogue_list = []
        self.data_list_ids = []
        self.timeout = 100
        self.dialogues_count = 0
        f.close()
        opts = Options()
        if path.exists(PROFILESTORAGEPATH):  # loads existing profile if it exists
            self.driver = webdriver.Firefox(executable_path=GeckoDriverManager().install(),
                                            firefox_profile=webdriver.FirefoxProfile(PROFILESTORAGEPATH),
                                            options=opts)
            self.check_login_status()
        else:
            self.driver = webdriver.Firefox(executable_path=GeckoDriverManager().install())
            self.sign_in()
        pass

    def parse(self, response):
        response = response.replace(self.driver.page_source)
        for id in self.data_list_ids:
            yield (SeleniumRequest(url="https://vk.com/?sel=" + id,
                                   callback=self.parse_dialogue,
                                   script='window.scrollTo(0, document.body.scrollHeight);'))
        pass

    def update_dialogues(self):
        soup = BeautifulSoup(self.driver.page_source, 'lxml')
        self.dialogues = soup.find('ul', {'id': "im_dialogs"})
        self.dialogue_list = self.dialogues.find_all("li")
        self.dialogues_count = len(self.dialogue_list)
        for i in range(len(self.dialogue_list)):
            if self.dialogue_list[i]["data-list-id"] not in self.data_list_ids:
                self.data_list_ids.append(self.dialogue_list[i]["data-list-id"])
        pass

    def parse_im(self, response):
        html = response.body_as_unicode()
        soup = BeautifulSoup(html, 'lxml')
        soup = soup.find_all(lambda tag: tag.name == 'a' and
                                         tag.get('class') == ['dialog_item'])
        hrefs = []
        for a in soup:
            link = a.get('href')
            self.logger.info("fetched chat link: {}".format(link))
            hrefs.append(link)
            yield Request(url="https://m.vk.com" + link, callback=self.parse_dialogue)
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
        # dialogue["name"] = response.xpath('//*[@class="mailHat__convoTitle"]').extract_first()
        html = response.body_as_unicode()
        soup = BeautifulSoup(html, 'lxml')
        text = soup.find("span", {"class": "sub_header_label"}).text
        dialogue["name"] = text
        self.logger.info("dialogue: name: {}, id: {}, type: {}".format(dialogue["name"],
                                                                       dialogue["id"],
                                                                       dialogue["dType"]))
        f = open("response.body_as_unicode", "w")
        f.write(response.body_as_unicode())
        f.close()
        # msg =
        #while ()
        #    FormRequest.from_response(response,
        #                            formdata={"act": "show",
        #                                      "peer_id": dialogue["id"],
        #                                      "msg": msg,
        #                                      "direction": "before",
        #                                      "_ajax": "1"},
        #                            callback=self.parse_im)
        pass