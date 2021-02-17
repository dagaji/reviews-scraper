import scrapy
from .spider import BaseSpider
import pdb
import scrapy_prueba.scrapy_selenium as scrapy_selenium
from urllib.parse import urljoin
from scrapy_prueba.items import GameReview
import re
from urllib.parse import urlparse
import locale; locale.setlocale(locale.LC_ALL, 'es_ES.utf8')
import calendar; month_name = [month for month in calendar.month_name]


platforms_alias = {'xbox-series-x': 'Xbox Series X',
                   'xbox-one': 'Xbox One',
                   'ps5': 'PS5',
                   'ps4': 'PS4',
                   'pc': 'PC',
                   'nintendo-switch': 'Nintendo Switch'
                  }


class IGNSpider(BaseSpider):
    name = "ign"
    allowed_domains = ["es.ign.com"]

    def start_requests(self):
        return [scrapy_selenium.Request(url="https://es.ign.com/article/review",
                                        middleware_cls=scrapy_selenium.InfiniteScrollIGN)]

    def get_reviews_url(self, response):
        articles = response.xpath("//section[@class='broll wrap']//article")

        all_urls = []
        all_reviews = []
        for article in articles:
            url = article.xpath(".//h3/a/@href").extract_first()
            if "analisis" in url:

                review = GameReview()
                review["url"] = url
                img = article.xpath(".//div[@class='t']/a/img")
                img_srcset = img.xpath("@srcset").extract_first()
                if img_srcset:
                    img_srcset = [el.strip() for el in img_srcset.split(',')]
                    img_url = img_srcset[-1].split(' ')[0]
                else:
                    img_url = img.xpath("@src").extract_first()
                review["img_url"] = img_url
                review["title"] = article.xpath(
                    ".//div[@class='m']/h3/a/text()").extract_first()
                review["description"] = article.xpath(
                    ".//div[@class='m']/p/text()").extract_first()

                all_urls.append(url)
                all_reviews.append(review)

        return all_urls, all_reviews

    def parse_review_1(self, response):
        game_review = self.game_reviews[response.request.url]

        sub_url = urlparse(response.request.url).path.split('/')[1]
        game_review['platforms'] = [platforms_alias[alias]
                                    for alias in platforms_alias if alias in sub_url]

        review_div = response.xpath("//div[@class='review']")
        score = review_div.xpath(
            "./figure//span[@class='side-wrapper side-wrapper hexagon-content']/text()").extract_first()
        if not (game_review['platforms'] and score):
            self.game_reviews.pop(response.request.url)
            return

        game_review['score'] = float(review_div.xpath(
            "./figure//span[@class='side-wrapper side-wrapper hexagon-content']/text()").extract_first()) * 10
        game_review['text'] = response.xpath(
            "//div[@class='details']//div[@class='blurb']/text()").extract_first().strip()
        game_review['best'] = response.xpath(
            "//h3[contains(text(), 'Pros')]/following-sibling::ul/li/text()").extract()
        game_review['worst'] = response.xpath(
            "//h3[contains(text(), 'Contras')]/following-sibling::ul/li/text()").extract()

        summary_section = response.xpath(
            "//section[@class='object-summary embed']")
        game_review['game_name'] = summary_section.xpath(
            ".//h2[@class='object-title']/a/text()").extract_first().strip()
        follow_up_url = summary_section.xpath(
            ".//h2[@class='object-title']/a/@href").extract_first()

        release_date_div = response.xpath(
            "//div[@class='article-modified-date']")
        if not release_date_div:
            release_date_div = response.xpath(
                "//div[@class='article-publish-date']")
        release_date = release_date_div.xpath(
            "./span/text()").extract_first().strip()
        release_date = re.search(r' el (.*?) a las ', release_date).group(1)
        release_date = [el.strip() for el in release_date.split('de')]
        release_date[1] = "{:02d}".format(
            month_name.index(release_date[1].lower()))
        release_date = '-'.join(release_date)
        game_review['release_date'] = release_date

        yield scrapy_selenium.Request(url=follow_up_url,
                                      middleware_cls=scrapy_selenium.DynamicContentMiddleware,
                                      callback=self.parse_review_2,
                                      meta=dict(review_url=response.request.url))

    def parse_review_2(self, response):
        game_review = self.game_reviews[response.meta["review_url"]]
        genres = response.xpath(
            "//dd[@class='keyword-genre']/text()").extract_first()
        genres = [genre.strip() for genre in genres.split('/')]
        game_review["genres"] = genres
        yield game_review

    def request_review(self, url):
        return scrapy_selenium.Request(url=url,
                                       middleware_cls=scrapy_selenium.DynamicContentMiddleware,
                                       callback=self.parse_review_1,)

    def request_next_page(self, response):
        return scrapy_selenium.Request.from_response(response)
