# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import pandas as pd
import psycopg2

class VkPipeline:
    def process_item(self, item, spider):
        return item

class PipelineAppendOneByOne:  # TODO fix indices

    def __init__(self, spider):
        spider.logger.info('Opening csvs for appending')
        spider.logger.info('WARNING appending data without filtering')
        self.df = pd.DataFrame(columns=["dialogueId", "name", "dialogueRef", "messages"])
        self.df2 = pd.DataFrame(columns=["messageId", "author", "text", "receiverId",
                                         "time", "repliedToMessageId", "forwardedMessagesIds"])
        self.file = open('dialogues.csv', 'a')
        self.file2 = open('messages.csv', 'a')

    def close_spider(self, spider):
        spider.logger.info('Closing csvs')
        spider.logger.info('WARNING appending data without filtering')
        self.file.close()
        self.file2.close()

    def process_item(self, item, spider):
        spider.logger.info('Processing dialogue: %s' % item["name"])
        dialogueDic = dict(item)
        dialogueDic["messages"] = [dialogueDic["messages"][i]["messageId"]
                                   for i in range(len(dialogueDic["messages"]))]
        self.df.append(dict(item), ignore_index=True).to_csv(self.file, header=False)
        self.df2.append(dict(item)["messages"], ignore_index=True).to_csv(self.file, header=False)
        return item

class WriteToPostgre:

    def open_spider(self, spider):
        spider.logger.info('Opening postgres connection')
        spider.logger.info('WARNING appending data without filtering')
        hostname = 'localhost'
        username = 'ruslan'
        password = ''  # none???
        database = 'dialogues'
        database2 = 'messages'
        self.connection = psycopg2.connect(host=hostname, user=username, password=password, dbname=database)
        self.connection2 = psycopg2.connect(host=hostname, user=username, password=password, dbname=database2)
        self.cur = self.connection.cursor()
        self.cur2 = self.connection2.cursor()

    def close_spider(self, spider):
        spider.logger.info('Closing postgres connection')
        spider.logger.info('WARNING appending data without filtering')
        self.cur.close()
        self.cur2.close()
        self.connection.close()
        self.connection2.close()

    def process_item(self, item, spider):
        spider.logger.info('Processing dialogue: %s' % item["name"])
        spider.logger.info('WARNING appending data without filtering')
        self.cur.execute("insert into reddit_content2(link,author,date,title) values(%s,%s,%s,%s)",
                         (item['dialogueId'],item['name'],item['dialogueRef'], [item['messages'][i]['messageId']
                                                                     for i in range(len(item['messages']))]))
        self.connection.commit()
        self.cur2.execute("insert into reddit_content2(link,author,date,title) values(%s,%s,%s,%s)",
                         (item['messageId'], item['author'], item['text'], item['receiverId'],
                          item['time'], item['repliedToMessageId'], item['forwardedMessagesIds']))
        self.connection2.commit()
        return item
