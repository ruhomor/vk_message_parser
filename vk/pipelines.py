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

    def create_db(self, spider):  # so bad
        spider.logger.info("Checking if Database exists")
        self.cur.execute("SELECT datname FROM pg_database;")
        list_database = self.cur.fetchall()
        if ("vkdata",) in list_database:
            spider.logger.info("'{}' Database already exists".format("vkdata"))
        else:
            spider.logger.info("'{}' Database did not exist.".format("vkdata"))
            self.cur.execute(sql.SQL("CREATE DATABASE {dbname}").format(
                dbname=sql.Identifier("vkdata")))
            self.con.commit()

    def create_role(self, spider):
        spider.logger.info("Checking if role exists")
        self.cur.execute("SELECT rolname FROM pg_roles;")
        self.con.commit()
        list_users = self.cur.fetchall()
        if (spider.name,) in list_users:
            spider.logger.info("'{}' Role already exists".format(spider.name))
        else:
            spider.logger.info("'{}' Role did not exist.".format(spider.name))
            query = sql.SQL("CREATE USER {username} WITH PASSWORD {password}").format(
                username=sql.Identifier(spider.name),
                password=sql.Placeholder()
            )
            self.cur.execute(query, (spider.name,))
            self.con.commit()

    def grant_priviliges(self, spider):
        spider.logger.info("Granting priviliges to {username}".format(username=spider.name))
        self.cur.execute(sql.SQL("GRANT ALL ON DATABASE {db_name} TO {username};").format(
            db_name=sql.Identifier("vkdata"),
            username=sql.Identifier(spider.name)))
        self.con.commit()

    def disconnect_from_db(self, spider):
        spider.logger.info("Disconnecting from Database")
        self.cur.close()
        self.con.close()

    def create_tables(self, spider):
        self.cur.execute("SELECT tablename FROM pg_tables;")
        list_tables = self.cur.fetchall()
        if ("messagestable",) in list_tables:
            spider.logger.info("'{}' already exists".format("messagestable"))
        else:
            spider.logger.info("'{}' table did not exist.".format("dialoguestable"))
            spider.logger.info("CREATING TABLE FOR MESSAGES")
            query = '''CREATE TABLE messagestable(
                            messageId               INT NOT NULL,
                            author                  TEXT NOT NULL,
                            messageText             TEXT,
                            receiverId              INT NOT NULL,
                            ts                      INT NOT NULL,
                            repliedToMessageId      INT,
                            forwardedMessagesIds    INT[],
                            PRIMARY KEY (messageId)
                        );'''
            self.cur.execute(query)

        if ("messagestable",) in list_tables:
            spider.logger.info("'{}' already exists".format("messagestable"))
        else:
            spider.logger.info("'{}' table did not exist.".format("dialoguestable"))
            spider.logger.info("CREATING TABLE FOR MESSAGES")

            query = '''CREATE TABLE dialoguestable(
                            dialogueId      INT NOT NULL,
                            dialogueName    TEXT NOT NULL,
                            dialogueRef     TEXT NOT NULL,
                            messageIds      INT[],
                            PRIMARY KEY     (dialogueId)
                        );'''
            self.cur.execute(query)

    def connect_to_db(self, spider, hostname, username, password, database):
        spider.logger.info('Connecting to {dbname} as {username}'.format(dbname=database, username=username))
        self.con = psycopg2.connect(host=hostname, user=username, password=password, dbname=database)
        self.cur = self.con.cursor()

    def open_spider(self, spider):
        self.connect_to_db(spider, 'localhost', 'postgres', '', 'postgres')
        self.con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

        self.create_db(spider)
        self.disconnect_from_db(spider)

        self.connect_to_db(spider, 'localhost', 'postgres', '', 'vkdata')
        self.con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

        self.create_tables(spider)
        # self.create_role(spider)
        # self.grant_priviliges(spider)
        # self.disconnect_from_db(spider)

        # self.connect_to_db(spider, 'localhost', spider.name, spider.name, 'vkdata')

    def process_item(self, item, spider):
        if isinstance(item, VkMessage):
            return self.handleVkMessage(item, spider)
        if isinstance(item, VkDialogue):
            return self.handleVkDialogue(item, spider)
        return item

    def close_spider(self, spider):
        self.disconnect_from_db(spider)

    def check_item(self, item, key):
        if item[key]:
            return sql.SQL(item[key])
        else:
            return sql.SQL("NULL")

    def handleVkMessage(self, item, spider):
        spider.logger.info('APPENDING MESSAGE TO DATABASE')
        query = sql.SQL(('''INSERT INTO messagestable (messageid, author, messagetext, receiverid, ts,
                            repliedtomessageid, forwardedmessagesids)
                            VALUES ({messageId},{author},'{messageText}',
                            {receiverId},{ts},{repliedToMessageId}, %s)''')).format(
            messageId=self.check_item(item, "messageId"),
            author=self.check_item(item, "author"),
            messageText=self.check_item(item, "text"),
            receiverId=self.check_item(item, "receiverId"),
            ts=self.check_item(item, "time"),
            repliedToMessageId=self.check_item(item, "repliedToMessageId"))
        self.cur.execute(query, (list(map(int, item["forwardedMessagesIds"])),))
        self.con.commit()
        return item

    def handleVkDialogue(self, item, spider):
        spider.logger.info('Processing dialogue: %s' % item["name"])
        spider.logger.info('APPENDING DIALOGUE TO DATABASE')
        query = sql.SQL(('''INSERT INTO dialoguestable (dialogueid, dialoguename, dialogueref, messageids) VALUES
                            ({dialogueId},'{dialogueName}','{dialogueRef}', %s)''')).format(
            dialogueId=self.check_item(item, "dialogueId"),
            dialogueName=self.check_item(item, "name"),
            dialogueRef=self.check_item(item, "dialogueRef"))
        self.cur.execute(query, (list(map(int, item["messages"])),))
        self.con.commit()
        return item
