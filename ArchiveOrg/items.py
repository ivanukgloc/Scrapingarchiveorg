# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class ArchiveorgItem(scrapy.Item):
    # define the fields for your item here like:
    title = scrapy.Field()
    release_date = scrapy.Field()
    performer = scrapy.Field()
    archiveURL = scrapy.Field()
    catalog_num = scrapy.Field()
    more_link = scrapy.Field()
