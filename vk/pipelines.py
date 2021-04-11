# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from vk.items import VkMessage, VkDialogue
import pandas as pd
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


class PipelineAppendOneByOne:  # TODO fix indices

    def open_spider(self, spider):
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
        if isinstance(item, VkMessage):
            return self.handleVkMessage(item, spider)
        if isinstance(item, VkDialogue):
            return self.handleVkDialogue(item, spider)
        return item

    def handleVkMessage(self, item, spider):
        spider.logger.info('APPENDING MESSAGE')
        self.df2.append(dict(item), ignore_index=True).to_csv(self.file2, header=False)

    def handleVkDialogue(self, item, spider):
        spider.logger.info('Processing dialogue: %s' % item["name"])
        spider.logger.info('APPENDING DIALOGUE')
        self.df.append(dict(item), ignore_index=True).to_csv(self.file, header=False)

class WriteToPostgre:

    def create_db(self, spider): # so bad
        spider.logger.info("CREATING DATABASE")
        con = psycopg2.connect(dbname='postgres',
                               user='postgres',
                               host='localhost',
                               password='')
        con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = con.cursor()

        cur.execute(sql.SQL("CREATE DATABASE {dbname}").format(dbname=sql.Identifier("VkData")))
        cur.execute(sql.SQL("CREATE USER {username} WITH PASSWORD {password}").format(
            username=sql.Identifier(spider.name),
            password=sql.Identifier("")))
        cur.execute(sql.SQL("GRANT ALL ON {table_name} TO {username};").format(table_name=sql.Identifier("VkData"),
                                                                               username=sql.Identifier(spider.name)))
        cur.close()
        con.close()

    def create_tables(self, spider):
        spider.logger.info("CREATING TABLES")
        sql = '''CREATE TABLE messagesTable(
                messageId               INT NOT NULL,
                author                  TEXT NOT NULL,
                messageText             TEXT,
                receiverId              INT NOT NULL,
                ts                      INT NOT NULL,
                repliedToMessageId      INT,
                forwardedMessagesIds    INT[],
                PRIMARY KEY (messageId)
            );'''
        self.cur.execute(sql)
        sql = '''CREATE TABLE dialoguesTable(
                dialogueId      INT NOT NULL,
                dialogueName    TEXT NOT NULL,
                dialogueRef     TEXT NOT NULL,
                messageIds      INT[],
                PRIMARY KEY     (dialogueId)
            );'''
        self.cur.execute(sql)

    def open_spider(self, spider):
        spider.logger.info('Opening postgres connection')
        spider.logger.info('WARNING appending data without filtering')
        hostname = 'localhost'
        username = spider.name
        password = ''  # none???
        database = 'VkData'
        self.df = pd.DataFrame(columns=["dialogueId", "name", "dialogueRef", "messages"])
        self.df2 = pd.DataFrame(columns=["messageId", "author", "text", "receiverId",
                                         "time", "repliedToMessageId", "forwardedMessagesIds"])
        self.connection = psycopg2.connect(host=hostname, user=username, password=password, dbname=database)
        self.cur = self.connection.cursor()
        self.create_tables()

    def close_spider(self, spider):
        spider.logger.info('Closing postgres connection')
        spider.logger.info('WARNING appending data without filtering')
        self.cur.close()
        self.connection.close()

    def process_item(self, item, spider):
        if isinstance(item, VkMessage):
            return self.handleVkMessage(item, spider)
        if isinstance(item, VkDialogue):
            return self.handleVkDialogue(item, spider)
        return item

    def handleVkMessage(self, item, spider):
        spider.logger.info('APPENDING MESSAGE TO DATABASE')
        self.cur.execute(sql.SQL("insert into messagestable({},{},{},{},{},{})").format())

    def handleVkDialogue(self, item, spider):
        spider.logger.info('Processing dialogue: %s' % item["name"])
        spider.logger.info('APPENDING DIALOGUE TO DATABASE')
        self.df.append(dict(item), ignore_index=True).to_csv(self.file, header=False)



        self.cur.execute(sql.SQL("insert into reddit_content2(link,author,date,title)").format(
                         (item['dialogueId'],item['name'],item['dialogueRef'], [item['messages'][i]['messageId']
                                                                     for i in range(len(item['messages']))])))
        self.connection.commit()
        self.cur.execute("insert into reddit_content2(link,author,date,title) values(%s,%s,%s,%s)",
                         (item['messageId'], item['author'], item['text'], item['receiverId'],
                          item['time'], item['repliedToMessageId'], item['forwardedMessagesIds']))
        self.connection.commit()
        return item
