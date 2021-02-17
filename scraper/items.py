# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

from scrapy.item import Item, Field

class GameReview(Item):
    game_name = Field()
    release_date = Field()
    reviewer = Field()
    text = Field()
    score = Field()
    best = Field()
    worst = Field()
    url = Field()
    genres = Field()
    platforms = Field()
    title = Field()
    description = Field()