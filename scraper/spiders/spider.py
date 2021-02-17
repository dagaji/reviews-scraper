from scrapy import Spider
import pdb


class BaseSpider(Spider):

    target_platforms = ['Xbox Series X','Xbox One', 'PS5', 'PS4', 'PC', 'Nintendo Switch']

    def __init__(self, name=None, **kwargs):
        super(BaseSpider, self).__init__(name=name, **kwargs)
        self.game_reviews = {}

    def get_reviews_url(self, response):
        raise NotImplementedError()

    def request_next_page(self, response):
        raise NotImplementedError()

    def request_review(self, url):
        raise NotImplementedError()

    def parse(self, response):
        urls, game_reviews = self.get_reviews_url(response)
        for url, game_review in zip(urls, game_reviews):
            print(url)
            game_review["reviewer"] = self.name
            self.game_reviews[url] = game_review
            yield self.request_review(url)
        yield self.request_next_page(response)