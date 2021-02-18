import calendar
from scrapy import Request
from .spider import BaseSpider
import pdb
import scraper.scrapy_selenium as scrapy_selenium
from scraper.items import GameReview
from urllib.parse import urljoin
import re
from urllib.parse import urlparse
import locale
locale.setlocale(locale.LC_ALL, 'es_ES.utf8')
month_name = [month for month in calendar.month_name]


class IGNSpider(BaseSpider):
    name = "ign"
    allowed_domains = ["es.ign.com"]
    start_url = "https://es.ign.com/article/review"
    review_page_middleware = scrapy_selenium.DynamicContentMiddleware
    listing_page_middleware = scrapy_selenium.InfiniteScrollIGN

    def get_reviews_url(self, response):
        articles = response.xpath("//section[@class='broll wrap']//article")

        all_urls = []
        all_reviews = []
        for article in articles:
            url = article.xpath(".//h3/a/@href").extract_first()
            if "analisis" in url:
                review = GameReview()
                review["url"] = url
                review["title"] = article.xpath(
                    ".//div[@class='m']/h3/a/text()").extract_first()
                review["description"] = article.xpath(
                    ".//div[@class='m']/p/text()").extract_first()

                all_urls.append(url)
                all_reviews.append(review)

        return all_urls, all_reviews

    def process_review(self, response):

        try:
            game_review = response.meta["game_review"]
            
            review_div = response.xpath("//div[@class='review']")
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
                
            platforms_str = summary_section.xpath(
                ".//div[@class='platformdivider']/text()[2]").extract_first()
            game_review["platforms"] = [el.strip() for el in platforms_str.split(",") if el.strip() in self.target_platforms]
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

            yield self.send_request(follow_up_url, game_review, self.process_review_2)

        except Exception as exception:
            print(exception)
            yield

    def process_review_2(self, response):
        try:
            game_review = response.meta["game_review"]
            genres = response.xpath(
                "//dd[@class='keyword-genre']/text()").extract_first()
            genres = [genre.strip() for genre in genres.split('/')]
            game_review["genres"] = genres
            yield game_review
        except Exception as exception:
            print(exception)
            yield

