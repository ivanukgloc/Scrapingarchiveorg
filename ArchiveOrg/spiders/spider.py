#!/usr/bin/env python
# -*- coding: utf-8 -*-

import scrapy

from ArchiveOrg.items import ArchiveorgItem

is_empty = lambda x, y=None: x[0] if x else y

class ArchiveSpider(scrapy.Spider):
    name = "archive_product"
    start_urls = ['https://archive.org/details/georgeblood?sort=-publicdate']

    def start_requests(self):
        yield scrapy.Request(url=self.start_urls[0], callback=self.parse_links)

    def parse_links(self, response):
        href_links = response.xpath('//div[contains(@class, "item-ttl")]'
                                    '/a/@href').extract()
        for href in href_links:
            link = 'https://archive.org' + href
            yield scrapy.Request(url=link, callback=self.parse_product, dont_filter=True)

    def parse_product(self, response):
        item = ArchiveorgItem()

        # Parse title
        title = self._parse_title(response)
        item['title'] = title

        # Parse release date
        release_date = self._parse_release_date(response)
        item['release_date'] = release_date

        # Pare more information link
        more_link = self._parse_more_link(response)
        item['more_link'] = more_link

        yield item

    @staticmethod
    def _parse_title(response):
        title = response.xpath('//div[contains(@class, "relative-row")]'
                               '//div[contains(@class, "thats-left")]'
                               '/h1/text()')[1].extract()
        return title

    def _parse_release_date(self, response):
        release_date = is_empty(response.xpath('//div[contains(@class, "relative-row")]'
                                               '//div[contains(@class, "thats-left")]'
                                               '//div[@class="key-val-big"]'
                                               '/a/text()').extract())
        if release_date == "78rpm":
            release_date = "None"

        return release_date

    def _parse_more_link(self, response):
        more_link = is_empty(response.xpath('//div[contains(@class, "relative-row")]'
                                            '//div[contains(@class, "thats-left")]'
                                            '//div[@class="key-val-big"]'
                                            '/a/@href').extract())

        if 'date' in more_link:
            more_link = 'https://archive.org' + more_link

        else:
            more_link = "None"

        return more_link


