# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface

import csv
from itemadapter import ItemAdapter

class LaptopPipeline:
    def open_spider(self, spider):
        self.file = open('output/laptop_info.csv', 'w', newline='', encoding='utf-8')
        self.write = csv.writer(self.file)
        self.write.writerow([
            'root-laptop_id', 'child-laptop_id', 'child_laptop_name', 'child_laptop_image',
            'child_laptop_link', 'child_laptop_color','child_laptop_price','special_features'
        ])


    def process_item(self, item, spider):
        self.write.writerow([
            item.get('root_laptop_id', ''),
            item.get('child_laptop_id', ''),
            item.get('child_laptop_name', ''),
            item.get('child_laptop_image', ''),
            item.get('child_laptop_link', ''),
            item.get('child_laptop_color', ''),
            item.get('child_laptop_price', ''),
            item.get('special_features', ''),
        ])
        return item

    def close_spider(self, spider):
        self.file.close()

