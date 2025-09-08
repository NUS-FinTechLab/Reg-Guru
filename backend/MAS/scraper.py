import os
import asyncio
from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import BrowserConfig

# Build a basic scraper.
BASE_PAGE_URL = "https://sso.agc.gov.sg/Browse/Act/Current/All/{page_index}?PageSize=10&SortBy=Title&SortOrder=ASC"
DOWNLOAD_DIR = "downloads"

config = BrowserConfig(accept_downloads=True, downloads_path=DOWNLOAD_DIR)

async def main():
    async with AsyncWebCrawler(config=config) as crawler:
        for page_index in range(0, 53):
            result = await crawler.arun(
                url=BASE_PAGE_URL.format(page_index=page_index),
            )
            for link in result.links["internal"]:
                if link["href"].endswith("=Pdf"):
                    print(f"Downloading {link['text']}...")
                    pdf_url = link["href"]
                    pdf_name = link["text"].replace(" ", "_") + ".pdf"
                    pdf_path = os.path.join(DOWNLOAD_DIR, pdf_name)

                    print(pdf_url)
                    
                    result = await crawler.arun(
                        url=pdf_url,
                    )
                    if result.success:
                        # Save PDF
                        if result.pdf:
                            with open(pdf_path, "wb") as f:
                                f.write(result.pdf)
                            print(f"Saved {pdf_name} to {DOWNLOAD_DIR}")
                        else:
                            print(f"No PDF found for {pdf_name}")
                    else:
                        print(f"Failed to download {pdf_name}: {result}")
            

if __name__ == "__main__":
    asyncio.run(main())