from scraping.scrape_urls import ScrapeUrls
from scraping.scrape_products import ScrapeProducts

ScrapeUrls.scrape("https://ikea.com/pl/pl/", "./data/products_urls.json")
ScrapeProducts.scrape("./data/products_urls.json", "./data/products_metadata.json")
