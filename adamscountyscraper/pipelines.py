from pymongo import MongoClient
from scrapy.conf import settings
from scrapy.exceptions import DropItem
from scrapy import log


class MongodbPipeLine(object):
    def __init__(self):
        connection = MongoClient(settings['MONGODB_URI'])
        db = connection[settings['MONGODB_DB']]
        self.collection = db[settings['MONGODB_COLLECTION']]

    def process_item(self, item, spider):

        if 'instrument' in item:
            self.object_processor(item, spider)
        else:
            self.list_processor(item, spider)

    def object_processor(self, item, spider):
        if item:
            self.collection.update_one({'href' : item['href']}, item)
            log.msg('Record added to database', level=log.DEBUG, spider=spider)
        return item

    def list_processor(self, item, spider):
        date = [key for key in item if key != 'page'][0]
        objects = [{'link' : link, 'date' : date, 'page' : item['page']} for link in item[date]]
        print(' - - - - Got items' + date)
        if objects:
            self.collection.insert_many(objects)
            log.msg('Record added to database', level=log.DEBUG, spider=spider)
        return item