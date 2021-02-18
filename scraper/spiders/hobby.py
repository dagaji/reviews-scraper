import scrapy
from .spider import BaseSpider
import pdb
import scraper.scrapy_selenium as scrapy_selenium
from urllib.parse import urljoin
from scraper.items import GameReview


class HobbySpider(BaseSpider):
    name = "hobby"
    allowed_domains = ["hobbyconsolas.com"]
    base_url = "https://www.hobbyconsolas.com/"
    start_url = "https://www.hobbyconsolas.com/analisis"
    review_page_middleware = scrapy_selenium.DynamicContentMiddlewareHobby
    listing_page_middleware = scrapy_selenium.InfiniteScrollMiddleware

    def get_reviews_url(self, response):
        all_articles = response.xpath("//ul[@class='article-list type-3']/li")

        all_urls = []
        all_reviews = []
        for article in all_articles:
            if article.xpath(".//div[@class='article-item-vertical games']"):
                url = urljoin(self.base_url, article.xpath(
                    ".//h2[@class='article-item-title']/a/@href").extract_first())
                review = GameReview()
                review["url"] = url
                review["title"] = article.xpath(
                    ".//h2[@class='article-item-title']/a/@title").extract_first().strip()
                review["description"] = article.xpath(
                    ".//p[@class='article-item-lead']/text()").extract_first().strip()

                all_urls.append(url)
                all_reviews.append(review)

        return all_urls, all_reviews

    def process_review(self, response):
        game_review = response.meta["game_review"]

        try:
            info_div = response.xpath(
                "//aside[@class='cards-list']//div[@class='block-mini-card']")
            game_review['game_name'] = info_div.xpath(
                './h2/text()').extract_first().strip()
            follow_up_url = urljoin(self.base_url, info_div.xpath(
                ".//a[contains(text(), 'Ficha completa')]/@href").extract_first())
            platforms_str = info_div.xpath(
                ".//div[@class='info-platform']//span[2]/text()").extract_first()
            game_review["platforms"] = [el.strip() for el in platforms_str.split(",") if el.strip() in self.target_platforms]

            header = response.xpath("//header[@class='article-header']")
            release_date = header.xpath(".//time/text()").extract_first().strip()
            game_review['release_date'] = release_date.split(' ')[0]

            review_header, review_resume = response.xpath(
                "//div[@class='article-content-review']/div")
            score = review_header.xpath(
                "./div[contains(@class, 'bubble')]/p[contains(@class, 'rate')]/text()").extract_first()
            game_review['score'] = float(score)
            game_review['text'] = review_header.xpath(
                "./p/text()").extract_first().strip()
            game_review['best'] = review_resume.xpath(
                ".//div[contains(@class, 'best-text')]/p/text()").extract_first().split('.')
            game_review['worst'] = review_resume.xpath(
                ".//div[contains(@class, 'worst-text')]/p/text()").extract_first().split('.')

            yield self.send_request(follow_up_url, game_review, self.process_review_2)

        except Exception as exception:
            print(exception)
            yield

    def process_review_2(self, response):
        try:
            game_review = response.meta["game_review"]
            game_review['genres'] = [response.xpath(
                "//ul[@class='information-list']/li/p[preceding-sibling::p[contains(text(), 'Género')]]/text()").extract_first().strip()]
            yield game_review
        except Exception as exception:
            print(exception)
            yield
