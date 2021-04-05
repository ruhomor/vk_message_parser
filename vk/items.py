# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

from scrapy import Item, Field


class VkMessage(Item):
    messageId = Field()
    message = Field()
    author = Field()
    time = Field()
    repliedId = Field()
    pass

class VkDialogue(Item):
    dType = Field()
    id = Field()
    name = Field()