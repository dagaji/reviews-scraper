from scrapy import Spider, Request
from scraper.scrapy_selenium import DynamicContentMiddleware
import pdb


class BaseSpider(Spider):

    target_platforms = ['Xbox Series X','Xbox One', 'PS5', 'PS4', 'PC', 'Nintendo Switch']

    review_page_middleware = None
    listing_page_middleware = None
    start_url = ""

    def __init__(self, name=None, **kwargs):
        super(BaseSpider, self).__init__(name=name, **kwargs)

        assert self.review_page_middleware != None
        assert self.listing_page_middleware != None
        assert self.start_url != ""

    def get_reviews_url(self, response):
        raise NotImplementedError()

    def process_review(self, response):
        raise NotImplementedError()

    def start_requests(self,):
        return [self.request_next_page()]

    def request_next_page(self,):
        return Request(url=self.start_url, 
                        meta={"target_middleware": self.listing_page_middleware,},
                        callback=self.parse)

    def send_request(self, url, game_review, callback):
        return Request(url=url,
                       meta={
                           "game_review": game_review,
                           "target_middleware": self.review_page_middleware,
                       },
                       callback=callback)

    def parse(self, response):
        urls, game_reviews = self.get_reviews_url(response)
        for url, game_review in zip(urls, game_reviews):
            print(url)
            game_review["reviewer"] = self.name
            yield self.send_request(url, game_review, self.process_review)
        yield self.request_next_page()
