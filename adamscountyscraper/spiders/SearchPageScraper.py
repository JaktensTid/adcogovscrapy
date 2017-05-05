import os
import scrapy
from selenium import webdriver
from datetime import datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
from selenium.webdriver.common.by import By
from lxml import html


class RecordsLinksSpider(scrapy.Spider):
    name = 'linksspider'
    date_formatter = "%d/%m/%Y"
    start_date = datetime.strptime('01/01/1960', date_formatter)
    end_date = datetime.strptime('03/01/1960', date_formatter)
    #end_date = datetime.today().strftime(date_formatter)

    start_urls = [
        'https://apps.adcogov.org/oncoreweb/Search.aspx']

    def __init__(self):
        self.driver = webdriver.PhantomJS(os.path.join(os.path.dirname(__file__), 'bin/phantomjs'))

    def parse(self, response):
        def get_hrefs():
            return [e.get_attribute('href')
                    for e in self.driver.find_elements_by_xpath(".//a[@class='stdFontResults']")]
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

            el_number_of_records = self.driver.find_element_by_xpath(".//span[@id='lblRecordCount']")
            if el_number_of_records.text == '':
                continue
            number_of_records = int(el_number_of_records.text.strip())
            number_of_pages = 1
            if number_of_records > 30:
                number_of_pages = int(number_of_records / 30)
                if number_of_records % 30 != 0:
                    number_of_pages += 1

            hrefs = get_hrefs()
            yield {date.strftime(self.date_formatter) + ' - 0' : list(set(hrefs))}
            counter = 31
            for page in range(1, number_of_pages):
                script = "__doPostBack('dgResults$ctl01$ctl%s','')" % str(page).zfill(2)
                self.driver.execute_script(script)
                #
                WebDriverWait(self.driver, 1).until(
                    EC.text_to_be_present_in_element((By.ID, "lblRecordPos"), str(counter) + ' - '))
                hrefs = get_hrefs()
                yield {date.strftime(self.date_formatter) + ' - ' + str(page): list(set(hrefs))}
                counter += 30

        self.driver.close()

    def dates(self):
        date = self.start_date
        yield date
        while date != self.end_date:
            date += timedelta(days=1)
            yield date
