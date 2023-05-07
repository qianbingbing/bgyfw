# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class HghspiderItem(scrapy.Item):
    # define the fields for your item here like:
    file_name = scrapy.Field()
    save_flag = scrapy.Field()
    # source_data = scrapy.Field()
    # income = scrapy.Field()
    # loan = scrapy.Field()
    # cash = scrapy.Field()
    # risk = scrapy.Field()
    invoice_info = scrapy.Field()
    result_list = scrapy.Field()
    pass
