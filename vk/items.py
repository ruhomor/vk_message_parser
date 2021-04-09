# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

from scrapy import Item, Field


class VkMessage(Item):
    messageId = Field()
    message = Field()
    author = Field()
    recieverId = Field()
    time = Field()
    repliedId = Field()
    forwardedMessagesIds = Field()
    pass

class VkDialogue(Item):
    dialogueType = Field()
    dialogueId = Field()
    name = Field()
    pass