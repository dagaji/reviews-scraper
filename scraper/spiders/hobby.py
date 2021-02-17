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

    def start_requests(self):
        return [scrapy_selenium.Request(url="https://www.hobbyconsolas.com/analisis", 
                                        middleware_cls=scrapy_selenium.InfiniteScrollMiddleware)]

    def get_reviews_url(self, response):
        all_articles = response.xpath("//ul[@class='article-list type-3']/li")

        all_urls = []
        all_reviews = []
        for article in all_articles:
            if article.xpath(".//div[@class='article-item-vertical games']"):
                url = urljoin(self.base_url, article.xpath(".//h2[@class='article-item-title']/a/@href").extract_first())
                review = GameReview()
                review["url"] = url
                picture_src = article.xpath(".//figure[@class='media-wrapper image']//picture/source[contains(@media, 'all')]")
                img_srcset = picture_src.xpath("@srcset").extract_first()
                if not img_srcset:
                    img_srcset = picture_src.xpath("@data-srcset").extract_first()
                img_srcset = [el.strip() for el in img_srcset.split(',')]
                img_url = img_srcset[-1].split(' ')[0]
                review["img_url"] = img_url
                review["title"] = article.xpath(".//h2[@class='article-item-title']/a/@title").extract_first().strip()
                review["description"] = article.xpath(".//p[@class='article-item-lead']/text()").extract_first().strip()

                all_urls.append(url)
                all_reviews.append(review)

        return all_urls, all_reviews

    def parse_review_1(self, response):
        game_review = self.game_reviews[response.request.url]

        info_div = response.xpath("//aside[@class='cards-list']//div[@class='block-mini-card']")
        game_review['game_name'] = info_div.xpath('./h2/text()').extract_first().strip()
        follow_up_url = urljoin(self.base_url, info_div.xpath(".//a[contains(text(), 'Ficha completa')]/@href").extract_first())

        header = response.xpath("//header[@class='article-header']") 
        release_date = header.xpath(".//time/text()").extract_first().strip()
        game_review['release_date'] = release_date.split(' ')[0]
        platform_str = header.xpath(".//following-sibling::p/text()").extract_first()
        platform = platform_str.split(":")[1].strip()
        game_review['platforms'] = [platform]

        review_header, review_resume = response.xpath("//div[@class='article-content-review']/div")
        score = review_header.xpath("./div[contains(@class, 'bubble')]/p[contains(@class, 'rate')]/text()").extract_first()
        if not (platform in self.target_platforms and score):
            self.game_reviews.pop(response.request.url)
            return

        game_review['score'] = float(score)
        game_review['text'] = review_header.xpath("./p/text()").extract_first().strip()
        game_review['best'] = review_resume.xpath(".//div[contains(@class, 'best-text')]/p/text()").extract_first().split('.')
        game_review['worst'] = review_resume.xpath(".//div[contains(@class, 'worst-text')]/p/text()").extract_first().split('.')

        # yield scrapy.Request(follow_up_url, callback=self.parse_review_2, meta=dict(game_url=response.request.url))
        yield scrapy_selenium.Request(url=follow_up_url, 
                                      middleware_cls=scrapy_selenium.DynamicContentMiddlewareHobby,
                                      callback=self.parse_review_2,
                                      meta=dict(game_url=response.request.url),)

    def parse_review_2(self, response):
        game_review = self.game_reviews[response.meta['game_url']]
        game_review['genres'] = [response.xpath("//ul[@class='information-list']/li/p[preceding-sibling::p[contains(text(), 'Género')]]/text()").extract_first().strip()]
        yield game_review


    def request_review(self, url):
        # return scrapy.Request(url, callback=self.parse_review_1)
        return scrapy_selenium.Request(url=url, 
                                      middleware_cls=scrapy_selenium.DynamicContentMiddlewareHobby,
                                      callback=self.parse_review_1)

    def request_next_page(self, response):
        return scrapy_selenium.Request.from_response(response, callback=self.parse)