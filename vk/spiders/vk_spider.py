from scrapy import Spider
from bs4 import BeautifulSoup
from selenium import webdriver
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.keys import Keys
from os import path
import shutil
import time
from vk.settings import PROFILESTORAGEPATH, PROFILE

class VkSpiderSpider(Spider):
    name = 'vk_spider'
    allowed_domains = ['vk.com']
    start_urls = ['https://vk.com/']

    def save_profile(self):
        currentProfilePath = self.driver.capabilities[PROFILE]
        if path.exists(PROFILESTORAGEPATH):
            shutil.rmtree(PROFILESTORAGEPATH)
        shutil.copytree(currentProfilePath, PROFILESTORAGEPATH,
                        ignore_dangling_symlinks=True)

    def scroll_down_im(self):
        WebDriverWait(self.driver, timeout=60).until(lambda d: d.find_element_by_id("im_dialogs"))
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
        self.parse_dialogues()
        pass

    def parse_dialogues(self):
        for dialogue in self.data_list_ids:
            self.driver.get("https://www.vk.com/im?sel=" + dialogue)
            self.scroll_up_dialogue()
        pass

    def scroll_up_dialogue(self):
        WebDriverWait(self.driver, timeout=60).until(lambda d: d.find_element_by_id("im_dialogs"))
        pcounter = 0
        self.update_stacks()
        while pcounter < self.stack_count:
            pcounter = self.stack_count
            for i in range(20):
                self.driver.execute_script("window.scrollTo({ top: 0, behavior: 'smooth' });")
                time.sleep(0.1)
            time.sleep(1)
            self.update_stacks()
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
        self.stack_count = 0
        self.message_ids = []
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
        #response = response.replace(self.driver.page_source)
        #for id in self.data_list_ids:
        #    yield (SeleniumRequest(url="https://vk.com/?sel=" + id,
        #                           callback=self.parse_dialogue,
        #                           script='window.scrollTo(0, document.body.scrollHeight);'))
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

    def update_stacks(self):
        soup = BeautifulSoup(self.driver.page_source, 'lxml')
        self.message_stacks = soup.find_all('div',
                               {'class': lambda x: x
                                and 'im-mess-stack' in x.split()
                               })
        self.stack_count = 0 # only new stacks?
        for stack in self.message_stacks:
            # print("stack: ")
            self.stack_count += 1 # only new stacks?
            author_id = stack["data-peer"]
            messages = stack.find_all("li")
            #print("author_id: ", author_id)
            #print()

            for message in messages:  # removing forwarded messages from message_list
                replied_to_message = message.find("div", {"class": "im-replied--text"})
                replied_to_msg_id = None
                if replied_to_message:
                    replied_to_msg = message.find("div", {"class": lambda x: x
                                                                             and "im-replied" in x.split()
                                                          })
                    replied_to_msg_id = replied_to_msg["data-msgid"]
                    replied_to_msg.extract()
                if "im-mess_fwd" not in message["class"]:
                    forwarded_messages = None
                    forwarded_messages = message.find_all("li", {"class": lambda x: x
                                                                                    and "im-mess_fwd" in x.split()
                                                                 })
                    forwarded_messages_list = []
                    if (forwarded_messages):
                        for fwd_message in forwarded_messages:
                            #pprint("FORWARDED MESSAGE")
                            forwarded_messages_list.append(self.handle_message(fwd_message, fwd_message["data-peer"],
                                                                               author_id))
                        # pprint(forwarded_messages_list)
                    receiver_id = message["data-peer"]
                    self.handle_message(message, author_id, receiver_id, replied_to_msg_id, forwarded_messages_list)  # HANDLE AFTER FWD MESSAGES IN REAL CODE
                #print()

    def handle_message(self, message, author_id, receiver_id, replied_to_msg_id=None, forwarded_msg_ids=[]):
        message_id = message["data-msgid"]
        if message_id not in self.message_ids:
            message_ts = message["data-ts"]
            message_text = message.find("div", {"class": lambda x: x
                                                                   and "im-mess--text" in x.split()
                                                }).text.strip()

            self.message_ids.append(message_id)
            print("author_id", author_id)
            print("message_id: ", message_id)
            print("replied_to_msg_id: ", replied_to_msg_id)
            print("receiver_id: ", receiver_id)
            print("message_ts: ", message_ts)
            print("message_text: ", message_text)
            print("forwarded_msg_ids: ", forwarded_msg_ids)
        return message_id
