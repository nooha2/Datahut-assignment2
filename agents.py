import json
import scrapy
from scrapy.http import HtmlResponse

class AgentsSpider(scrapy.Spider):
    name = "agents"
    allowed_domains = ["bhhsamb.com"]
    start_urls = [
        "https://www.bhhsamb.com/CMS/CmsRoster/RosterSearchResults?layoutID=963&pageSize=10&pageNumber=1&sortBy=random"
    ]

    def parse(self, response):
        self.logger.debug(f"Response status: {response.status}")
        self.logger.debug(f"Response headers: {response.headers}")

        content_type = response.headers.get('Content-Type').decode('utf-8')
        if 'application/json' not in content_type:
            self.logger.error(f"Unexpected content type: {content_type}")
            self.logger.debug(f"Response text: {response.text}")
            return

        try:
            data = json.loads(response.text)
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to decode JSON response: {e}")
            self.logger.debug(f"Response text: {response.text}")
            return

        self.logger.debug(f"Parsed JSON data: {data}")

        if not isinstance(data, dict):
            self.logger.error("Parsed data is not a dictionary")
            self.logger.debug(f"Data: {data}")
            return

        html_content = data.get('Html', '')
        if not html_content:
            self.logger.error("No 'Html' content found in the data")
            self.logger.debug(f"JSON data: {data}")
            return

        html_response = HtmlResponse(url=response.url, body=html_content, encoding='utf-8')

        # Extract profile URLs for each agent
        profile_urls = []
        articles = html_response.css('article')
        for article in articles:
            # Find the <a> tag within each <article>
            agent_link = article.css('.cms-int-roster-card-image-container.site-roster-card-image-link::attr(href)').get()
            if agent_link:
                profile_urls.append(agent_link)

        # Print the extracted profile URLs
        self.logger.info(f"Found {len(profile_urls)} profile URLs")
        for profile_url in profile_urls:
            full_profile_url = response.urljoin(profile_url)
            self.logger.info(f"Found Profile URL: {full_profile_url}")
            yield scrapy.Request(url=full_profile_url, callback=self.parse_profile)

        total_count = data.get('TotalCount', 0)
        current_page = int(response.url.split('pageNumber=')[-1].split('&')[0])
        page_size = 10
        if current_page * page_size < total_count:
            next_page = current_page + 1
            next_page_url = f"https://www.bhhsamb.com/CMS/CmsRoster/RosterSearchResults?layoutID=963&pageSize=10&pageNumber={next_page}&sortBy=random"
            yield scrapy.Request(url=next_page_url, callback=self.parse)

    def parse_profile(self, response):
        item = {}
        item['name'] = response.xpath('//h2[contains(@class, "agent-name")]/text()').get(default='').strip()
        item['job_title'] = response.xpath('//span[contains(@class, "agent-title")]/text()').get(default='').strip()
        item['image_url'] = response.xpath('//div[@class="agent-image"]/img/@src').get(default='')
        item['address'] = response.xpath('//div[contains(@class, "agent-address")]/text()').get(default='').strip()
        item['contact_details'] = {
            'Office': response.xpath('//span[contains(text(), "Office")]/following-sibling::text()').get(default='').strip(),
            'Cell': response.xpath('//span[contains(text(), "Cell")]/following-sibling::text()').get(default='').strip(),
            'Fax': response.xpath('//span[contains(text(), "Fax")]/following-sibling::text()').get(default='').strip(),
        }
        item['social_accounts'] = {
            'facebook': response.xpath('//a[contains(@href, "facebook")]/@href').get(default=''),
            'twitter': response.xpath('//a[contains(@href, "twitter")]/@href').get(default=''),
            'linkedin': response.xpath('//a[contains(@href, "linkedin")]/@href').get(default=''),
            'youtube': response.xpath('//a[contains(@href, "youtube")]/@href').get(default=''),
            'pinterest': response.xpath('//a[contains(@href, "pinterest")]/@href').get(default=''),
            'instagram': response.xpath('//a[contains(@href, "instagram")]/@href').get(default=''),
        }
        item['offices'] = [office.strip() for office in response.xpath('//div[@class="agent-office"]/text()').getall() if office.strip()]
        item['languages'] = [language.strip() for language in response.xpath('//div[@class="agent-languages"]/text()').getall() if language.strip()]
        item['description'] = response.xpath('//div[@class="agent-description"]/text()').get(default='').strip()

        yield item
