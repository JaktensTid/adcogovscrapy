import os
import re
import scrapy
import logging
from selenium import webdriver
from datetime import datetime, timedelta
from selenium.webdriver.remote.remote_connection import LOGGER
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class RecordsLinksSpider(scrapy.Spider):
    name = 'linksspider'
    date_formatter = "%m/%d/%Y"
    start_date = datetime.strptime('01/01/1860', date_formatter)
    #end_date = datetime.strptime('03/01/1960', date_formatter)
    #end_date = datetime.today()
    end_date = datetime.strptime('05/05/2017', date_formatter)

    start_urls = [
        'https://apps.adcogov.org/oncoreweb/Search.aspx']

    def __init__(self):
        LOGGER.setLevel(logging.ERROR)
        self.driver = webdriver.PhantomJS(os.path.join(os.path.dirname(__file__), 'bin/phantomjs'))
        self.driver.set_page_load_timeout(30)
        self.driver.set_script_timeout(30)

    def parse(self, response):
        exception_message = '- - - - No Such Element Exception'
        elements_by_xpath = self.driver.find_elements_by_xpath
        element_by_xpath = self.driver.find_element_by_xpath
        by_id = self.driver.find_element_by_id
        total = 0
        def next_page():
            next_pages = None
            try:
                next_pages = [page
                         for page in elements_by_xpath(
                        ".//tr[@class='stdFontPager'][position()=1]/td//a[preceding-sibling::span]")]
            except NoSuchElementException:
                if '400 Bad Request' in self.driver.page_source:
                    print(exception_message)
                    self.driver.delete_all_cookies()
                    self.driver.refresh()
                    return next_page()
            if next_pages: return next_pages[0]
            else: return next_pages

        def get_hrefs():
            return list(set([e.get_attribute('href').replace('showdetails', 'details')
                    for e in elements_by_xpath(".//a[@class='stdFontResults']")]))

        def next_date(total):
            if total % 5 == 0:
                self.driver.delete_all_cookies()
                total = 0
            search_selector = element_by_xpath(".//table[@id='Table2']/tbody/tr[position() = last() - 1]//a")
            search_selector.click()
            submit = by_id('cmdSubmit')
            date_input = by_id('txtRecordDate')
            date_input.clear()
            date_input.send_keys(date.strftime(self.date_formatter))
            submit.click()

        self.driver.get(response.url)

        for date in self.dates():
            next_date(total)
            total += 1
            hrefs = get_hrefs()
            for href in hrefs:
                request = scrapy.Request(href,
                                         callback=self.parse_item)
                yield request
            next = next_page()
            while next:
                try:
                    next.click()
                except TimeoutException:
                    self.driver.refresh()
                    next = next_page()
                    next.click()
                hrefs = get_hrefs()
                for href in hrefs:
                    request = scrapy.Request(href,
                                             callback=self.parse_item)
                    yield request
                next = next_page()

        self.driver.close()

    def parse_item(self, response):
        item = {}
        search_pattern = [('instrument', 'lblCfn'), ('docType', 'lblDocumentType'), ('modifyDate', 'lblModifyDate'),
                          ('recordDate', 'lblRecordDate'), ('acknowledgementDate', 'lblAcknowledgementDate'),
                          ('grantor', 'lblDirectName'), ('grantee', 'lblReverseName'), ('bookType', 'lblBookType'),
                          ('bookPage', 'lblBookPage'), ('numberPages', 'lblNumberPages'),
                          ('consideration', 'lblConsideration'), ('comments', 'lblComments'),
                          ('comments2', 'lblComments2'), ('marriageDate', 'lblMarriageDate'),
                          ('legal', 'lblLegal'), ('address', 'lblAddress'), ('caseNumber', 'lblCaseNumber'),
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

        item['recep'] = item['instrument'][:-7].lstrip('0')
        item['year'] = item['instrument'][:4]
        item['Reception No'] = item['recep'] + '-' + item['year']
        item['book'] = item['bookPage'].split('/')[0].strip()
        item['page'] = item['bookPage'].split('/')[1].strip()
        if item['legal']:
            item.update(self.get_sec_twp_rng(item['legal']))

        yield item

    def ternaty(self, regexp, str, replace1, replace2):
        value = re.findall(regexp, str)
        value = '' if not value else value[0].replace(replace1, '')
        if replace2:
            return value.replace(replace2, '')
        else:
            return value

    def get_sec_twp_rng(self, legal):
        subdivision = ''
        matches = re.findall(r'( [0-9]{1,2}(-| )[0-9]{1,2}(-| )[0-9]{1,2})|(^[0-9]{1,2}(-| )[0-9]{1,2}(-| )[0-9]{1,2})',
                             legal)
        if matches:
            return matches[0].strip().split('-')

        lower = legal.lower()
        sec_reg = r'(sec [0-9]{1,2})|(sec:[0-9]{1,2})'
        twp_reg = r'(tp [0-9]{1,2})|(tp:[0-9]{1,2})'
        rng_reg = r'(rng [0-9]{1,2})|(rng:[0-9]{1,2})'
        blk_reg = r'(blk[s]? [0-9]{1,2}&[0-9]{1,2})|(blk[s]? [0-9]{1,2}-[0-9]{1,2})|(blk[s]? [0-9]{1,2})'
        lot_reg = r'(lot[s]? [0-9]{1,2}&[0-9]{1,2})|(lot[s]? [0-9]{1,2}-[0-9]{1,2})|(lot[s]? [0-9]{1,2})'
        sec = self.ternaty(sec_reg, lower, 'sec ', 'sec1')
        twp = self.ternaty(twp_reg, lower, 'tp ', 'tp:')
        rng = self.ternaty(rng_reg, lower, 'rng ', 'rng:')
        blk = self.ternaty(blk_reg, lower, 'blk ', '')
        lot = self.ternaty(lot_reg, lower, 'lot ', 'lots ')
        if lot and blk:
            subdivision = self.ternaty('((' + blk_reg + ') .*)', lower, 'blk ' + blk + ' ', '')
        elif lot:
            subdivision = self.ternaty('((' + lot_reg + ') .*)', lower, 'lot ' + lot + ' ', 'lots ' + lot + ' ')
        return {'sec' : sec, 'twp' : twp, 'rng' : rng, 'blk' : blk, 'lot' : lot, 'subdivision' : subdivision.upper()}

    def dates(self):
        date = self.end_date
        yield date
        while date != self.start_date:
            date -= timedelta(days=1)
            yield date