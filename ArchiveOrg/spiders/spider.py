#!/usr/bin/env python
# -*- coding: utf-8 -*-

import scrapy
import re

from ArchiveOrg.items import ArchiveorgItem

is_empty = lambda x, y=None: x[0] if x else y

class ArchiveSpider(scrapy.Spider):
    name = "archive_product"
    start_urls = ['https://archive.org/details/georgeblood?sort=-publicdate']
    PAGE_LINK = 'https://archive.org/details/georgeblood?&sort=-publicdate&page={page_number}'
    item_per_page = 75

    def start_requests(self):
        yield scrapy.Request(url=self.start_urls[0], callback=self.parse_pages)

    def parse_pages(self, response):
        page_links = []
        total_count = response.xpath('//div[@class="columns-facets"]'
                                     '/h3/text()').extract()
        total_count = self._clean_text(total_count[0])
        total_count = re.search('\d+', total_count).group(0)
        range_count = int(total_count) / self.item_per_page

        for page_num in range(1, range_count):
            link = self.PAGE_LINK.format(page_number=page_num)
            page_links.append(link)

        for page_link in page_links:
            yield scrapy.Request(url=page_link, callback=self.parse_links, dont_filter=True)

    def parse_links(self, response):
        href_links = response.xpath('//div[contains(@class, "item-ttl")]'
                                    '/a/@href').extract()
        for href in href_links:
            link = 'https://archive.org%s' % href
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

    @staticmethod
    def _parse_release_date(response):
        release_date = is_empty(response.xpath('//div[contains(@class, "relative-row")]'
                                               '//div[contains(@class, "thats-left")]'
                                               '//div[@class="key-val-big"]'
                                               '/a/text()').extract())
        if release_date == "78rpm":
            release_date = "None"

        return release_date

    @staticmethod
    def _parse_more_link(response):
        more_link = is_empty(response.xpath('//div[contains(@class, "relative-row")]'
                                            '//div[contains(@class, "thats-left")]'
                                            '//div[@class="key-val-big"]'
                                            '/a/@href').extract())

        if 'date' in more_link:
            more_link = 'https://archive.org%s' % more_link

        else:
            more_link = "None"

        return more_link

    def _clean_text(self, text):
        text = re.sub("[\n\t]", "", text)
        text = re.sub(",", "", text).strip()
        return text

