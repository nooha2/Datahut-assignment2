import scrapy
import json
from urllib.parse import urljoin

class AgentsSpider(scrapy.Spider):
    name = 'agents'
    allowed_domains = ['bhhsamb.com']
    start_urls = [
        'https://www.bhhsamb.com/CMS/CmsRoster/RosterSearchResults?layoutID=963&pageSize=10&pageNumber=1&sortBy=random'
    ]

    def parse(self, response):
        # Log the status code
        self.logger.debug(f"Response status: {response.status}")

        # Log headers
        self.logger.debug(f"Response headers: {response.headers}")

        # Check content type
        content_type = response.headers.get('Content-Type').decode('utf-8')
        if 'application/json' not in content_type:
            self.logger.error(f"Unexpected content type: {content_type}")
            self.logger.debug(f"Response text: {response.text}")
            return

        # Try to parse the JSON response
        try:
            data = json.loads(response.text)
            self.logger.debug(f"Parsed JSON data: {data}")
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to decode JSON response: {e}")
            self.logger.debug(f"Response text: {response.text}")
            return

        # Check if 'Html' key is in the JSON response
        html_content = data.get('Html')
        if not html_content:
            self.logger.error("'Html' key is missing in the JSON response")
            self.logger.debug(f"JSON data: {data}")
            return

        # Parse HTML content to extract agent profile URLs
        yield from self.parse_office_roster(response, html_content)

    def parse_office_roster(self, response, html_content):
        # Parse the HTML content to extract agent profile URLs
        selector = scrapy.Selector(text=html_content)
        agent_links = selector.css('a.cms-int-roster-card-image-container')
        base_url = "https://www.bhhsamb.com"
        
        # Extract profile URLs for each agent
        for agent_link in agent_links:
            profile_url = agent_link.css('a::attr(href)').get()
            if profile_url:
                full_url = urljoin(base_url, profile_url)
                self.logger.debug(f"Following agent profile URL: {full_url}")
                yield response.follow(full_url, self.parse_profile)

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

        self.logger.debug(f"Scraped agent profile: {item}")
        yield item
