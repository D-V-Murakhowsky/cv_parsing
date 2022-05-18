import json
import scrapy
from scrapy import signals
from scrapy.crawler import CrawlerProcess
from scrapy.signalmanager import dispatcher
from scrapy.utils.project import get_project_settings
import csv  

class CompanyLinksSpider(scrapy.Spider):
    name = 'companies'

    custom_settings = {
        'DOWNLOAD_DELAY': 3,
        'LOG_LEVEL': 'WARNING'
    }

    def start_requests(self):
        for i in range(0, 63):
            past = 10 * i
            pagination = f"&start={past}" if i>0 else ""
            request_url = f'https://ca.indeed.com/jobs?q=data+science{pagination}'
            print(request_url)
            yield scrapy.Request(request_url, cookies={'s_seven':'ybcrSH2VmFjWCdWvCKLVQESOhpFXkJwHrSKql-RgkF0'}, dont_filter=True)

    def parse(self, response):
        # print(response.body.decode("utf-8"))
        response_text = response.body.decode("utf-8")
        if "Captcha solve page" in response_text:
            print("ERROR: CAPTCHA FORM!!!!!!!!!!!!")
        else:
            ad_links = response.xpath('//a[contains(@class, "result")]/@href').getall()
            print(ad_links)
            yield from response.follow_all(ad_links, callback=self.parse_company)

    def parse_company(self, response):
        print("----------------------------")
        print("Url: " + response.url)
        # print("Response: " + response.body.decode("utf-8"))
        company_link = response.xpath('//a[contains(@href, "https://ca.indeed.com/cmp/")]/@href').extract_first()
        if company_link is not None:
            company_link_clean = company_link.split("?")[0]
            yield {'url': company_link_clean}


class CompaniesSpider(scrapy.Spider):
    name = 'companies_parse'

    custom_settings = {
        'DOWNLOAD_DELAY': 3,
        'LOG_LEVEL': 'WARNING'
    }

    def __init__(self) -> None:
        super().__init__()
        self.scrData = []

    def start_requests(self):
        with open('c:/tmp/company_urls.json', 'r', encoding='utf-8') as f:
            company_url_list = json.load(f)
            for company_url_item in company_url_list:
                url = company_url_item["url"]
                yield scrapy.Request(url, dont_filter=True)

    def parse(self, response):
        print("----------------------------")
        print("Url: " + response.url)
        salaries_tags = response.css('.css-1tvxdp1')
        salaries = ''
        for tag in salaries_tags:
            salaries += tag.css('.css-1tvxdp1 span.css-5q1oz8::text').get()
            salaries += ' -- '
            salaries += ' '.join([_.strip() for _ in tag.css('.css-1tvxdp1 div ::text').getall()])
            salaries += '\n'

        try:
            size = ''.join(response.css('[data-testid="companyInfo-employee"] div ::text').getall()[1:])
        except IndexError:
            size = None
        try:
            revenue = ''.join(response.css('[data-testid="companyInfo-revenue"] div ::text').getall()[1:])
        except IndexError:
            revenue = None

        data = {
            'url': response.url,
            'name': response.css('[itemprop="name"]::text').get(),
            'rating': response.css('.css-8l8558 span:nth-child(2)::text').get(),
            'reviews count': response.css('[data-tn-element="reviews-countLink"]::text').get(),
            'founded': response.css('[data-testid="companyInfo-founded"] div:nth-child(2)::text').get(),
            'Company size': size,
            'Revenue': revenue,
            'Industry': response.css('[data-testid="companyInfo-industry"] div:nth-child(2)::text').get(),
            'Salaries': salaries,
        }

        self.scrData.append(data);
        yield data

def company_url_results():
    company_urls = []

    def crawler_results(signal, sender, item, response, spider):
        if not any(elem["url"] == item["url"] for elem in company_urls):
            company_urls.append(item)
            with open('c:/tmp/company_urls.json', 'w', encoding='utf-8') as f:
                json.dump(company_urls, f, ensure_ascii=False, indent=4)

    dispatcher.connect(crawler_results, signal=signals.item_scraped)

    process = CrawlerProcess(get_project_settings())
    process.crawl(CompanyLinksSpider)
    process.start()  # the script will block here until the crawling is finished

    with open('c:/tmp/company_urls.json', 'w', encoding='utf-8') as f:
        json.dump(company_urls, f, ensure_ascii=False, indent=4)
    

def company_info_results():
    results = []

    def crawler_results(signal, sender, item, response, spider):
        results.append(item)

    dispatcher.connect(crawler_results, signal=signals.item_scraped)

    process = CrawlerProcess(get_project_settings())
    process.crawl(CompaniesSpider)
    process.start()  # the script will block here until the crawling is finished
    return results

if __name__ == '__main__':

    # crawl company URLs and save them to file
    # company_url_results()

    # crawl company data based on previosly saved URLs
    comp_infos = company_info_results()

    # write to CSV
    fieldnames = ['url', 'name', 'rating', 'reviews count', 'founded', 'Company size', 'Revenue', 'Industry', 'Salaries']
    with open('c:/tmp/companies_data.csv', 'w', encoding='UTF8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(comp_infos)