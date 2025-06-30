from typing import Iterable

import scrapy
from scrapy import Request
import pandas as pd
from ..settings import INPUT_FILE, VALID_URL_PREFIXES
from ..items import LaptopItem

class LaptopSpider(scrapy.Spider):
    name = "laptop"

    def start_requests(self) -> Iterable[Request]:
        try:
            dataframe = pd.read_csv(INPUT_FILE)
            for _, row in dataframe.iterrows():
                url = row['url']
                if (isinstance(url, str) and
                        any(url.startswith(prefix) for prefix in VALID_URL_PREFIXES)):
                    yield scrapy.Request(
                        url=url.strip(),
                        callback=self.parse)
                else:
                    self.logger.error('URL is not valid: %s', url)

        except Exception as error:
            self.logger.error('Error with reading csv file: %s', error)

    def parse(self, response):
        items = []
        # Laptop's general information
        root_laptop_id = response.css('#block-comment-cps::attr(product-id)').get()

        for variant in response.css('.list-variants li'):
            item = LaptopItem()

            item['root_laptop_id'] =  root_laptop_id
            item['child_laptop_id'] = variant.attrib.get('data-product-id')
            item['child_laptop_name'] = variant.css('img::attr(alt)').get()
            item['child_laptop_link'] = variant.css('a::attr(href)').get()
            item['child_laptop_image'] = variant.css('img::attr(src)').get()
            item['child_laptop_color'] = variant.xpath('.//strong[@class="item-variant-name"]/text()').get()
            price = variant.xpath('.//span[@class="item-variant-price"]/text()').get()
            item['child_laptop_price'] = price.strip() if price else None
            item['special_features'] = response.css('.mobile ul li::text').getall()

            items.append(item)

        return items