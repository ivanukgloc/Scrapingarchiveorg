#!/usr/bin/env python
# -*- coding: utf-8 -*-

import scrapy
import re
import requests

from ArchiveOrg.items import ArchiveorgItem

is_empty = lambda x, y=None: x[0] if x else y

class ArchiveSpider(scrapy.Spider):
    name = "archive_product"
    allowed_domains = ["https://archive.org", "www.45worlds.com"]

    start_urls = ['https://archive.org/details/georgeblood?sort=-publicdate']

    PAGE_LINK = 'https://archive.org/details/georgeblood?&sort=-publicdate&page={page_number}'
    item_per_page = 75  # display the number of items per page

    TITLE = ''
    PERFORMER = ''
    PUBLISHER = ''
    CATALOG_NUM = ''
    MORE_URL = ''

    def start_requests(self):
        yield scrapy.Request(url=self.start_urls[0], callback=self.parse_pages)

    def parse_pages(self, response):
        page_links = []

        # total count is number of results
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
        item = ArchiveorgItem()

        href_links = response.xpath('//div[contains(@class, "item-ttl")]'
                                    '/a/@href').extract()

        for href in href_links:
            link = 'https://archive.org%s' % href
            item['archiveURL'] = link
            yield scrapy.Request(url=link, meta={"item": item},
                                 callback=self.parse_product, dont_filter=True)

    def parse_product(self, response):
        item = response.meta["item"]

        item['title'] = self._parse_title(response)
        item['performer'] = self._parse_performer(response)
        item['publisher'] = self._parse_publisher(response)
        item['catalog_num'] = self._parse_catalog_num(response)

        # Parse Release date
        release_date = self._parse_release_date(response)
        item['release_date'] = release_date

        # Parse 78discography URL
        more_link = self._parse_search_link(response)
        item['google_url'] = more_link

        yield item

    def _parse_title(self, response):
        title = response.xpath('//div[contains(@class, "relative-row")]'
                               '//div[contains(@class, "thats-left")]'
                               '/h1/text()')[1].extract()
        title = self._clean_text(title)
        self.TITLE = title
        return title

    def _parse_release_date(self, response):
        release_date = is_empty(response.xpath('//div[contains(@class, "relative-row")]'
                                               '//div[contains(@class, "thats-left")]'
                                               '//div[@class="key-val-big"]'
                                               '/a/text()').extract())
        if release_date == '78rpm':
            if self.CATALOG_NUM:
                world_catalog = re.search('\d+', self.CATALOG_NUM).group()
                url = 'http://www.45worlds.com/78rpm/record/' + str(world_catalog)
                response_data = requests.get(url)
                if str(response_data) == '<Response [404]>':
                    date = ""
                else:
                    original_date = re.search('<td>Date:(.*?)</tr>', response_data.content).group(1)\
                        .replace('<td>', '').replace('</td>', '')
                    if original_date:
                        date = re.search('19(\d+)', original_date).group()
                    else:
                        date = ""
                release_date = date
            else:
                release_date = ""
        return release_date

    def _parse_performer(self, response):
        performer = is_empty(response.xpath('//div[contains(@class, "relative-row")]'
                                            '//div[contains(@class, "thats-left")]'
                                            '//div[@class="key-val-big"]'
                                            '/span[@class="value"]/a/text()').extract())
        self.PERFORMER = performer
        return self.PERFORMER

    def _parse_publisher(self, response):
        publisher = is_empty(response.xpath('//div[contains(@class, "relative-row")]'
                                            '//div[contains(@class, "thats-left")]'
                                            '/span[@class="value"]'
                                            '/a/text()').extract())
        self.PUBLISHER = publisher
        return self.PUBLISHER

    def _parse_catalog_num(self, response):
        catalog_num = ''
        catalog_num_standard = response.xpath('//div[contains(@class, "relative-row")]'
                                              '//div[contains(@class, "thats-left")]'
                                              '//div[@id="descript"]'
                                              '/p[5]/text()[2]')
        catalog_num_other = response.xpath('//div[contains(@class, "relative-row")]'
                                           '//div[contains(@class, "thats-left")]'
                                           '//div[@id="descript"]'
                                           '/p[4]/text()[2]')
        catalog_num_special = response.xpath('//div[contains(@class, "relative-row")]'
                                             '//div[contains(@class, "thats-left")]'
                                             '//div[@id="descript"]'
                                             '/p[3]/text()[2]')
        catalog_num_ospecial = response.xpath('//div[contains(@class, "relative-row")]'
                                              '//div[contains(@class, "thats-left")]'
                                              '//div[@id="descript"]'
                                              '/p[2]/text()[2]')
        if catalog_num_standard:
            catalog_num = catalog_num_standard[0].extract()
        elif catalog_num_other:
            catalog_num = catalog_num_other[0].extract()
        elif catalog_num_special:
            catalog_num = catalog_num_special[0].extract()
        elif catalog_num_ospecial:
            catalog_num = catalog_num_ospecial[0].extract()

        self.CATALOG_NUM = self._clean_text(catalog_num)
        return self.CATALOG_NUM

    def _parse_search_link(self, response):
        google_url = 'https://www.google.com/search?' \
                     'q=site:{reference_url}' + " " + \
                     '{publisher}' + " " + \
                     '{catalog_num}' + " " + '{title}' + " " + '{performer}'

        url = google_url.format(reference_url="www.78discography.com",
                                publisher=self.PUBLISHER,
                                catalog_num=self.CATALOG_NUM,
                                title=self.TITLE,
                                performer=self.PERFORMER)
        return url

    def _clean_text(self, text):
        text = re.sub("[\n\t]", "", text)
        text = re.sub(",", "", text).strip()
        return text

