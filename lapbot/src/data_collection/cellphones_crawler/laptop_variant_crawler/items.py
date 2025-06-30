# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class LaptopItem(scrapy.Item):

    root_laptop_id = scrapy.Field()
    child_laptop_id = scrapy.Field()
    child_laptop_name = scrapy.Field()
    child_laptop_link = scrapy.Field()
    child_laptop_image = scrapy.Field()
    child_laptop_color = scrapy.Field()
    child_laptop_price = scrapy.Field()
    special_features = scrapy.Field()


