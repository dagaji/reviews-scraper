"""This module contains the ``SeleniumMiddleware`` scrapy middleware"""

from importlib import import_module

from scrapy import signals
from scrapy.exceptions import NotConfigured
from scrapy.http import HtmlResponse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import scraper.settings as settings
from random import uniform

from .request import Request
import time
import pdb

from bs4 import BeautifulSoup


class SeleniumMiddleware:
    """Scrapy middleware handling the requests using selenium"""

    def __init__(self, driver_name, driver_arguments):
        """Initialize the selenium webdriver

        Parameters
        ----------
        driver_name: str
            The selenium ``WebDriver`` to use
        driver_arguments: list
            A list of arguments to initialize the driver
        """

        driver_class, driver_options_class = {'firefox': (webdriver.Firefox, webdriver.FirefoxOptions),
                                              'chrome': (webdriver.Chrome, webdriver.ChromeOptions)}[driver_name]

        driver_options = driver_options_class()
        for argument in driver_arguments:
            driver_options.add_argument(argument)
        self.driver = driver_class(
            **{f'{driver_name}_options': driver_options})
        self.first_request = True

    def spider_closed(self):
        """Shutdown the driver when spider is closed"""
        self.driver.quit()

    @classmethod
    def from_crawler(cls, crawler):
        """Initialize the middleware with the crawler settings"""

        driver_name = crawler.settings.get('SELENIUM_DRIVER_NAME')
        driver_arguments = crawler.settings.get('SELENIUM_DRIVER_ARGUMENTS')

        if driver_name not in ["firefox", "chrome"]:
            raise NotConfigured(
                'SELENIUM_DRIVER_NAME must be set to either "firefox" or "chrome"')

        middleware = cls(
            driver_name=driver_name,
            driver_arguments=driver_arguments
        )

        crawler.signals.connect(
            middleware.spider_closed, signals.spider_closed)

        return middleware

    def _process_request(self, request, spider):
        raise NotImplementedError()

    def _page_source(self,):
        raise NotImplementedError()

    def process_request(self, request, spider):
        """Process a request using the selenium driver if applicable"""
        if request.middleware_cls == self.__class__:
            self._process_request(request, spider)
            response_html = self._page_source()
            self.first_request = False
            return HtmlResponse(
                self.driver.current_url,
                body=response_html,
                encoding='utf-8',
                request=request
            )
        return None


class DynamicContentMiddleware(SeleniumMiddleware):
    """Scrapy middleware handling the requests using selenium"""

    def __init__(self, driver_name, driver_arguments, max_delay=10.0, min_delay=7.0):
        super(DynamicContentMiddleware, self).__init__(
            driver_name, driver_arguments)
        self.get_delay = lambda: uniform(max_delay, min_delay)

    def _process_request(self, request, spider):
        """Process a request using the selenium driver if applicable"""
        delay = self.get_delay()
        print(f"Waiting {delay} seconds ...")
        time.sleep(delay)
        self.driver.get(request.url)

    def _page_source(self,):
        return str.encode(self.driver.page_source)


class DynamicContentMiddlewareHobby(DynamicContentMiddleware):

    def _process_request(self, request, spider):
        super(DynamicContentMiddlewareHobby,
              self)._process_request(request, spider)

        if self.first_request:
            WebDriverWait(self.driver, 10).until(EC.frame_to_be_available_and_switch_to_it(
                (By.XPATH, "//iframe[contains(@id,'sp_message_iframe')]")))
            WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable(
                (By.XPATH, "//button[contains(text(),'Aceptar')]"))).click()
            self.driver.switch_to.default_content()


class InfiniteScrollMiddleware(SeleniumMiddleware):

    def _page_source(self,):
        if self.first_request:
            return str.encode(self.driver.page_source)

        soup = BeautifulSoup(self.driver.page_source, 'lxml')
        for ul in soup.find_all("ul", {"class": "article-list type-3"})[:-1]:
            ul.decompose()
        return str(soup).encode()

    def _process_request(self, request, spider):

        if self.first_request:
            self.driver.get(request.url)
            WebDriverWait(self.driver, 10).until(EC.frame_to_be_available_and_switch_to_it(
                (By.XPATH, "//iframe[contains(@id,'sp_message_iframe')]")))
            WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable(
                (By.XPATH, "//button[contains(text(),'Aceptar')]"))).click()
            self.driver.switch_to.default_content()
        else:
            num_pages = len(self.driver.find_elements(
                By.XPATH, "//ul[@class='article-list type-3']"))
            WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable(
                (By.XPATH, "//a[@class='button' and text()='Cargar más']"))).click()
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH,
                                                                                 "//ul[@class='article-list type-3']['{}']/following-sibling::ul[@class='article-list type-3']".format(num_pages))))


class InfiniteScrollIGN(SeleniumMiddleware):

    def _page_source(self,):
        if self.first_request:
            return str.encode(self.driver.page_source)

        soup = BeautifulSoup(self.driver.page_source, 'lxml')
        # soup.find("section", {"class": "wrap herogrid"}).decompose()
        for section in soup.find_all("section", {"class": "broll wrap"})[:-1]:
            section.decompose()
        return str(soup).encode()

    def _process_request(self, request, spider):

        if self.first_request:
            self.driver.get(request.url)
            WebDriverWait(self.driver, 10).until(EC.presence_of_all_elements_located((By.XPATH,
                                                                                      "//section[@class='broll wrap']//article//h3/a")))
        else:
            previus_pagenum = int(self.driver.find_elements(
                By.XPATH, "//section[@class='broll wrap']")[-1].get_attribute("data-pagenum"))
            next_pagenum = previus_pagenum + 1
            anchor = self.driver.find_element(
                By.XPATH, "//div[@id='infinitescrollanchor']")
            self.driver.execute_script(
                "arguments[0].scrollIntoView(true)", anchor)
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH,
                                                                                 "//section[@class='broll wrap' and @data-pagenum='{}']".format(next_pagenum))))
