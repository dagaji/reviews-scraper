# reviews-scraper

Web Scraping utilities to extract reviews from video game webesites. If you want to know more about this project, check out this 
[blog post](https://dagaji.netlify.app/p/scraping-game-reviews-websites-with-scrapy-and-selenium/)

## Installation

To install python dependencies type: 

`pip install -r requeriments.txt`

Installation of [chromedriver](https://chromedriver.chromium.org/) and/or [geckodriver](https://github.com/mozilla/geckodriver) is also required.

## Usage

* Modify `scraper/settings.py` according to your needs.
* Create you our own Spider inheriting from **BaseSpider** and implementing `get_reviews_url()` and `process_review()` methods.
* Create your own Middleware inheriting from **SeleniumMiddleware** and implementing `_process_request()` and optionally `_page_source()` methods.
* To start crawling type: `scrapy crawl YOUR_SPYDER_NAME`.


