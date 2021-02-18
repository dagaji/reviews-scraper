# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem
from scraper.db import get_db, get_collection, insert_one
import pdb
import json
import os.path
from datetime import date

required_fields = ["score", "game_name", "title",
                   "description", "url", "genres",
                   "release_date", "platforms"]


def check_item(review_item):
    for req_field in required_fields:
        if not req_field in review_item:
            return False
    return True


class GamesReviewsPipelineJSON:
    def __init__(self, max_num_items, dst_file):
        self.max_num_items = max_num_items
        self.dst_file = dst_file
        self.items = []
        self.closed_spider = False

    @classmethod
    def from_crawler(cls, crawler):
        settings = crawler.settings
        max_num_items = settings.get("MAX_NUM_ITEMS", 15)
        dst_dir = os.path.join(settings.get(
            "DST_DIR", './data'), crawler.spider.name)
        if not os.path.exists(dst_dir):
            os.makedirs(dst_dir)
        dst_file = os.path.join(dst_dir, str(date.today())+'.json')
        return cls(max_num_items, dst_file)

    def save_json(self):
        with open(self.dst_file, "w") as dst_file:
            json.dump(self.items, dst_file)

    def process_item(self, item, spider):

        if self.closed_spider:
            return

        if not check_item(item):
            print("dropped item")
            return

        self.items.append(dict(item))
        if len(self.items) >= self.max_num_items:
            self.save_json()
            self.closed_spider = True
            spider.crawler.engine.close_spider(
                self, reason='Scrapping finished.')


class GamesReviewsPipelineMongoDB:
    def __init__(self, max_num_items, coll):
        self.max_num_items = max_num_items
        self.inserted_items = 0
        self.coll = coll
        self.closed_spider = False

    @classmethod
    def from_crawler(cls, crawler):
        settings = crawler.settings
        max_num_items = settings.get("MAX_NUM_ITEMS", 15)
        coll = get_collection(get_db(settings, drop=False),
                              settings.get('MONGODB_COLLECTION'))
        return cls(max_num_items, coll)

    def process_item(self, item, spider):

        if self.closed_spider:
            return

        if not check_item(item):
            print("dropped item")
            return

        if insert_one(self.coll, item):
            self.inserted_items += 1
            if self.inserted_items >= self.max_num_items:
                self.closed_spider = True
        else:
            self.closed_spider = True

        if self.closed_spider:
            spider.crawler.engine.close_spider(
                self, reason='Scrapping finished.')
