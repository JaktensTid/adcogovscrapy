import scrapy
from lxml import html
from pymongo import MongoClient
from scrapy.conf import settings

class ItemsSpider(scrapy.Spider):
    name = 'itemsspider'
    connection = MongoClient(settings['MONGODB_URI'])
    db = connection[settings['MONGODB_DB']]
    collection = db[settings['MONGODB_COLLECTION']]
    items = collection.find({"data" : {"$exists" : False}})
    items.batch_size(1000)
    start_urls = [item['link'].replace('showdetails', 'details') for item in items]

    def parse(self, response):
        item = {}
        search_pattern = [('instrument', 'lblCfn'), ('docType', 'lblDocumentType'), ('modifyDate', 'lblModifyDate'),
                          ('recordDate', 'lblRecordDate'), ('acknowledgementDate', 'lblAcknowledgementDate'),
                          ('grantor', 'lblDirectName'), ('grantee', 'lblReverseName'), ('bookType', 'lblBookType'),
                          ('bookPage', 'lblBookPage'), ('numberPages', 'lblNumberPages'),
                          ('consideration', 'lblConsideration'), ('comments', 'lblComments'),
                          ('comments2', 'lblComments2'), ('marriageDate', 'lblMarriageDate'),
                          ('legal', 'lblLegal'),('address', 'lblAddress'), ('caseNumber', 'lblCaseNumber'),
                          ('parse1Id', 'lblParcelId'), ('furureDocs', 'pnlFutureDocs'), ('prevDocs', 'pnlPrevDocs'),
                          ('unresolvedLinks', 'lblUnresolvedLinks'), ('relatedDocs', 'pnlRelatedDocs'),
                          ('docHistory', 'pnlDocHistory'), ('refNum', 'lblRefNum'), ('rerecord', 'lblRerecord')]

        for key, id in search_pattern:
            value = response.selector.xpath(".//span[@id='%s']//text()" % id).extract()
            if value:
                if len(value) > 1:
                    item[key] = value
                else:
                    item[key] = value[0]
            else:
                item[key] = ''

        item['link'] = response.url
        item['recep'] = item['instrument'][:-7].lstrip('0')
        item['year'] = item['instrument'][:4]
        item['Reception No'] = item['recep'] + '-' + item['year']
        item['book'] = item['bookPage'].split('/')[0].strip()
        item['page'] = item['bookPage'].split('/')[1].strip()

        yield item