import os
import asyncio
from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import BrowserConfig

BASE_URL = "https://sso.agc.gov.sg"

class SsoScraper:
    def __init__(self, download_dir):
        self.base_url = BASE_URL

    async def scrape(self, start_page=1, end_page=5):
        all_links = []
        for page_index in range(start_page, end_page + 1):
            page_url = BASE_PAGE_URL.format(page_index=page_index)
            print(f"Scraping page: {page_url}")
            links = await self.crawl_page(page_url)
            all_links.extend(links)
        
        print(f"Total documents found: {len(all_links)}")
        return all_links

    async def crawl_page(self, url):
        links = []
        try:
            page = await self.crawler.crawl(url)
            anchor_elements = await page.query_selector_all("a[href*='/ViewPDF']")
            for anchor in anchor_elements:
                href = await anchor.get_attribute("href")
                if href:
                    full_url = f"https://sso.agc.gov.sg{href}"
                    links.append(full_url)
                    print(f"Found document link: {full_url}")
            await page.close()
        except Exception as e:
            print(f"Error crawling page {url}: {str(e)}")
        return links

if __name__ == "__main__":
    asyncio.run(main())