# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy

class PharmpriceItem(scrapy.Item):
    # define the fields for your item here like:
    link = scrapy.Field()
    tradeName = scrapy.Field()
    regNumber = scrapy.Field()
    MNN = scrapy.Field()
    manufacturer = scrapy.Field()
    groupATH = scrapy.Field()

    drugGenericName = scrapy.Field()
    drugForm = scrapy.Field()
    drugContent = scrapy.Field()
    drugProperties = scrapy.Field()
    drugIndication = scrapy.Field()
    drugDosage = scrapy.Field()
    drugSide = scrapy.Field()
    drugContrIndication = scrapy.Field()
    drugInteractions = scrapy.Field()
    drugSpecial = scrapy.Field()
    drugExpiry = scrapy.Field()
    drugRetailCondition = scrapy.Field()