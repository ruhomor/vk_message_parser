# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

from scrapy import Item, Field


class VkMessage(Item):
    messageId = Field()
    author = Field()
    text = Field()
    receiverId = Field()
    time = Field()
    repliedToMessageId = Field()
    forwardedMessagesIds = Field()
    pass

class VkDialogue(Item):
    dialogueId = Field()
    name = Field()
    dialogueRef = Field()
    messages = Field()
    pass