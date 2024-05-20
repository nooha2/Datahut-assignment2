import scrapy


class BhssSpider(scrapy.Spider):
    name = "bhss"
    allowed_domains = ["bhhsamb.com"]
    start_urls = ["https://bhhsamb.com/roster/Agents"]

    def parse(self, response):
        pass
