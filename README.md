# reviews-scraper

[Blog post about this project](https://dagaji.netlify.app/p/scraping-game-reviews-websites-with-scrapy-and-selenium/)

## Installation

To install python dependencies type: 

`pip install -r requeriments.txt`

Installation of [chromedriver](https://chromedriver.chromium.org/) and/or [geckodriver](https://github.com/mozilla/geckodriver) is also required.

## Usage

* Modify `scraper/settings.py` according to your needs.
* Create you our own Spider subclassing **BaseSpider** and implementing `get_reviews_url()` and `process_review()` methods.
* Create your own Middleware subcalssing **SeleniumMiddleware** implementing `_process_request()` and optinally `_page_source()` methods.
* To start crawling type: `scrapy crawl YOUR_SPYDER_NAME`.


