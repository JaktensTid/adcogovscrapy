import os
import scrapy
from selenium import webdriver
from datetime import datetime, timedelta
from selenium.common.exceptions import TimeoutException, NoSuchElementException



class RecordsLinksSpider(scrapy.Spider):
    name = 'linksspider'
    date_formatter = "%m/%d/%Y"
    start_date = datetime.strptime('01/01/1860', date_formatter)
    #end_date = datetime.strptime('03/01/1960', date_formatter)
    #end_date = datetime.today()
    end_date = datetime.strptime('02/07/2017', date_formatter)

    start_urls = [
        'https://apps.adcogov.org/oncoreweb/Search.aspx']

    def __init__(self):
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
            return list(set([e.get_attribute('href')
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
            print('Next date')
            next_date(total)
            print('Next date over')
            total += 1
            yield {date.strftime(self.date_formatter): get_hrefs(), 'page' : 1}
            print('get hrefs over')
            next = next_page()
            print('next page over')
            while next:
                page = next.text
                try:
                    next.click()
                except TimeoutException:
                    self.driver.refresh()
                    next = next_page()
                    next.click()
                print('next click over')
                hrefs = get_hrefs()
                print('get hrefs over')
                yield {date.strftime(self.date_formatter): hrefs, 'page' : page }
                next = next_page()
                print('next page over')

        self.driver.close()

    def dates(self):
        date = self.end_date
        yield date
        while date != self.start_date:
            date -= timedelta(days=1)
            yield date