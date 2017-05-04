import os
import scrapy
from selenium import webdriver
from datetime import datetime, timedelta


class AdamscountyscraperSpider(scrapy.Spider):
    date_formatter = "%d/%m/%Y"
    start_date = datetime.strptime('01/01/1960', date_formatter)
    end_date = datetime.today().strftime(date_formatter)

    start_urls = [
        'https://apps.adcogov.org/oncoreweb/Search.aspx']

    def __init__(self):
        self.driver = webdriver.PhantomJS(os.path.join(os.path.dirname(__file__), 'bin/phantomjs'))

    def parse(self, response):
        self.driver.get(response.url)
        submit = self.driver.find_element_by_id('cmdSubmit')
        date_input = self.driver.find_element_by_id('txtRecordDate')
        date_input.clear()
        for date in self.dates():
            date_input.send_keys(date.strftime(self.date_formatter))
            yield []

    def dates(self):
        date = self.start_date
        while date != self.end_date:
            yield date + timedelta(days=1)
