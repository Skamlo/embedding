import requests
import json
from bs4 import BeautifulSoup
from typing import List, Dict, Iterable
import math
from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver import ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
import time
import os
from scraping.file_manager import FileManager


class ScrapeUrls:
    @staticmethod
    def __scrape_categories_webpage_url(website_url: str) -> str:
        """
        Retrieves the URL of the categories page from the main IKEA website.

        Args:
            website_url (str): The main IKEA website URL.

        Returns:
            str: URL of the categories page.
        """
        response = requests.get(website_url)
        soup = BeautifulSoup(response.text, 'html.parser')

        aside = soup.find("aside", class_="hnf-mobile-menu hnf-mobile-menu--hidden")
        script = aside.find("script")
        aside_dict = json.loads(script.text)
        categories_url = aside_dict.get("primary")[0].get("link")
        return categories_url
    
    @staticmethod
    def __scrape_categories_data(categories_url: str) -> List[Dict]:
        """
        Extracts all subcategories and categories with their names and URLs from the categories page.

        Args:
            categories_url (str): The URL of the categories page.

        Returns:
            List[Dict]: A list of dictionaries with category data.
        """
        response = requests.get(categories_url)
        soup = BeautifulSoup(response.text, 'html.parser')

        container = soup.find("nav", class_="vn-nav vn-p-grid vn-accordion")
        slides = container.find_all("div", class_="vn-p-grid-gap vn-accordion__item")

        categories = []
        for slide in slides:
            sub_category_name = slide.find("h2").find("button").find("span").text
            sub_category_url = slide.find("a")["href"]
            for category in slide.find("ul").find_all("li"):
                category = category.find("a")
                category_url = category["href"]
                category_name = category.text

                if category_url == sub_category_url:
                    continue

                categories.append({
                    "sub_category_name": sub_category_name,
                    "name": category_name,
                    "url": category_url
                })
        
        return categories
    
    @staticmethod
    def __get_total_number_of_products(category_url: str) -> int:
        """
        Retrieves the total number of products listed under a specific category.

        Args:
            category_url (str): URL of the category page.

        Returns:
            int: Total number of products.
        """
        response = requests.get(category_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        product_total_count = soup.find("div", class_="catalog-product-list__total-count")
        product_total_count = product_total_count.text
        products_number = [int(word) for word in product_total_count.split() if word[0].isdigit()]
        return products_number[-1]
    
    @staticmethod
    def __get_number_of_pages(number_of_products: int) -> int:
        """
        Calculates the number of pages for a given total number of products.

        Args:
            number_of_products (int): Total number of products.

        Returns:
            int: Total number of pages needed to display all products.
        """
        return math.ceil((number_of_products - 12) / 48) + 1

    @staticmethod
    def __scrape_products(categories: List[Dict]) -> List[str]:
        """
        Scrapes product URLs for all categories using Selenium.

        Args:
            categories (List[Dict]): A list of category data (name, sub_category_name, and URL).

        Returns:
            List[str]: A list of dictionaries containing product URLs and their corresponding category info.
        """
        products_urls = []

        # Create web driver
        options = ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--log-level=3")
        options.add_argument('--no-sandbox')
        options.add_argument("--disable-logging")
        options.add_experimental_option("excludeSwitches", ['enable-logging'])
        service = Service(service_log_path=os.devnull)
        driver = webdriver.Chrome(options=options, service=service)

        driver.get(categories[0].get("url"))
        time.sleep(5)
        print()

        # Get number of products
        number_of_products = []
        for category in tqdm(categories, desc="Collecting number of products"):
            url = category.get("url")
            number_of_products.append(ScrapeUrls.__get_total_number_of_products(url))
        total_products = sum(number_of_products)

        # Get products
        progress_bar = tqdm(total=total_products, desc="Scraping products")

        for i, category in enumerate(categories):
            url = category.get("url")
            pages_number = ScrapeUrls.__get_number_of_pages(number_of_products[i])
            n_products = 0
            for page_number in range(1, pages_number+1):
                page_url = url + f"?page={page_number}"
                driver.get(page_url)

                time.sleep(3)

                try:
                    product_list = driver.find_element(By.CLASS_NAME, "plp-product-list__products")
                    product_wrappers = product_list.find_elements(By.CLASS_NAME, "plp-fragment-wrapper")
                except Exception as e:
                    print(f"Error extracting product list: {e}")
                    continue

                if not isinstance(product_wrappers, Iterable):
                    print(f"Error extracting product list: {e}")
                    continue

                progress_bar.update(len(product_wrappers))
                n_products += len(product_wrappers)

                for wrapper in product_wrappers:
                    try:
                        inner_div = wrapper.find_element(By.CLASS_NAME, "plp-mastercard__item.plp-mastercard__price")
                        product_link = inner_div.find_element(By.TAG_NAME, "a").get_attribute("href")
                        products_urls.append({
                            "url": product_link,
                            "category": category.get("name"),
                            "sub_category": category.get("sub_category_name")
                        })
                    except Exception as e:
                        print(f"Error extracting product URL: {e}")
                        continue
            
            progress_bar.update(number_of_products[i] - n_products)

        driver.quit()
        progress_bar.close()
        return products_urls
    
    @staticmethod
    def scrape(ikea_website_url: str, output_path: str):
        """
        Scrape products urls from IKEA website. Output will be saved in `output_path` file.

        Args:
            ikea_website_url (str): The URL of the IKEA website homepage.
            output_path (str): The path where the scraped data will be saved.
        """
        categories_url = ScrapeUrls.__scrape_categories_webpage_url(ikea_website_url)
        categories = ScrapeUrls.__scrape_categories_data(categories_url)
        products_urls = ScrapeUrls.__scrape_products(categories)
        FileManager.save(products_urls, output_path)
