from pymongo import MongoClient
from scrapy.conf import settings
from scrapy import log

total = 0
class MongodbPipeLine(object):
    def __init__(self):
        connection = MongoClient(settings['MONGODB_URI'])
        db = connection[settings['MONGODB_DB']]
        self.collection = db[settings['MONGODB_COLLECTION']]

    def process_item(self, item, spider):
        if 'instrument' in item:
            if item:
                self.collection.insert_one(item)
                log.msg('Record added to database. Total: ' + str(total), level=log.INFO, spider=spider)
            return item
