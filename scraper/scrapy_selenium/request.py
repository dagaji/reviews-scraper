import scrapy
import enum

class Request(scrapy.Request):
    def __init__(self, url, middleware_cls, *args, expected_conditions=None, **kwargs):
        super().__init__(url, *args, **kwargs, dont_filter=True)
        self.middleware_cls = middleware_cls
        self.expected_conditions = expected_conditions

    @classmethod
    def from_response(cls, response, *args, url=None, middleware_cls=None, expected_conditions=None, **kwargs):
        if url is None:
            url = response.request.url
        if middleware_cls is None:
            middleware_cls = response.request.middleware_cls
        request = cls(url, middleware_cls, *args, expected_conditions=expected_conditions, **kwargs)
        request.cookies = dict(response.request.cookies)
        return request
