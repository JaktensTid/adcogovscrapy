import os
import scrapy
from selenium import webdriver
from datetime import datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException
from selenium.webdriver.common.by import By
from lxml import html


class RecordsLinksSpider(scrapy.Spider):
    name = 'linksspider'
    date_formatter = "%d/%m/%Y"
    start_date = datetime.strptime('01/01/1860', date_formatter)
    #end_date = datetime.strptime('03/01/1960', date_formatter)
    end_date = datetime.today()

    start_urls = [
        'https://apps.adcogov.org/oncoreweb/Search.aspx']

    def __init__(self):
        self.driver = webdriver.PhantomJS(os.path.join(os.path.dirname(__file__), 'bin/phantomjs'))

    def parse(self, response):
        self.driver.get(response.url)

        for date in self.dates():
            search_selector = self.driver.find_element_by_xpath(
                ".//table[@id='Table2']/tbody/tr[position() = last() - 1]//a")
            search_selector.click()
            submit = self.driver.find_element_by_id('cmdSubmit')
            date_input = self.driver.find_element_by_id('txtRecordDate')
            date_input.clear()
            date_input.send_keys(date.strftime(self.date_formatter))
            submit.click()
            hrefs = self.driver.find_elements_by_xpath(".//a[@class='stdFontResults']")
            if hrefs:
                link_first = hrefs[0]
                link_first.click()
                item = {}
                search_pattern = [('instrument', 'lblCfn'), ('docType', 'trDocumentType'), ('modifyDate', 'trModifyDate'),
                                  ('recordDate', 'trRecordDate'), ('acknowledgementDate', 'trAcknowledgementDate'),
                                  ('grantor', 'trGrantor'), ('grantee', 'trGrantee'), ('bookType', 'trBookType'),
                                  ('bookPage', 'trBookPage'), ('numberPages', 'trNumberPages'),
                                  ('consideration', 'trConsideration'), ('comments', 'trComments'),
                                  ('comments2', 'trComments2'), ('marriageDate', 'trMarriageDate'),
                                  ('legal', 'trLegal'),('address', 'trAddress'), ('caseNumber', 'trCaseNumber'),
                                  ('parse1Id', 'trParcelId'), ('furureDocs', 'trFutureDocs'), ('prevDocs', 'trPrevDocs'),
                                  ('unresolvedLinks', 'trUnresolvedLinks'), ('relatedDocs', 'trRelatedDocs'),
                                  ('docHistory', 'trDocHistory'), ('refNum', 'trRefNum'), ('rerecord', 'trRerecord')]

                for key, id in search_pattern:
                    item[key] = self.driver.find_element_by_id(id).text
                item['date'] = date
                item['link'] = self.driver.current_url
                item['recep'] = item['instrument'][:-7].lstrip('0')
                item['year'] = item['instrument'][:4]
                item['Reception No'] = item['recep'] + '-' + item['year']
                item['book'] = item['bookPage'].split('/')[0].strip()
                item['page'] = item['bookPage'].split('/')[1].strip()

                yield item

                WebDriverWait(self.driver, timeout=10).until(frame_available_cb("frame name"))

    def dates(self):
        date = self.end_date
        yield date
        while date != self.start_date:
            date -= timedelta(days=1)
            yield date
