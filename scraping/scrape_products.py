import requests
import json
from bs4 import BeautifulSoup
from typing import Dict, List
from tqdm import tqdm
from selenium.webdriver import ChromeOptions, Chrome
from selenium.webdriver.common.by import By
import time
from scraping.file_manager import FileManager


class ScrapeProducts:
    @staticmethod
    def __click_cookie_accept(driver: Chrome):
        try:
            button = driver.find_element(By.ID, "onetrust-accept-btn-handler")
            button.click()
        except:
            pass

    @staticmethod
    def __get_title(soup: BeautifulSoup) -> str:
        try:
            return soup.find("h1", class_="pip-price-module__name")\
                .find("span", class_="pip-price-module__name-decorator notranslate")\
                .text
        except:
            return None

    @staticmethod
    def __get_subtitle(soup: BeautifulSoup) -> str:
        try:
            descrption = soup.find("h1", class_="pip-price-module__name")\
                .find("span", class_="pip-price-module__description")\
                .find("span")
            return descrption.text + descrption.find("a").text
        except:
            return None

    @staticmethod
    def __get_price(soup: BeautifulSoup) -> float:
        integer = None
        decimal = None

        for tag in ["span", "em"]:
            try:
                price_div = soup.find("div", class_="pip-price-module__price")\
                    .find("div")\
                    .find(tag)\
                    .find("span", class_="notranslate")
                integer = price_div.find("span", class_="pip-price__nowrap")\
                    .find("span", class_="pip-price__integer").text
                decimal = price_div.find("span", class_="pip-price__decimal").text
                break
            except:
                continue
        else:
            return None

        try:
            integer = float(integer)
        except:
            integer = .0
    
        try:
            decimal = float(decimal)
        except:
            decimal = .0

        return integer + decimal / 100

    @staticmethod
    def __get_description(soup: BeautifulSoup) -> str:
        try:
            return soup.find("p", class_="pip-product-summary__description").text
        except:
            return None

    @staticmethod
    def __get_product_id(soup: BeautifulSoup) -> str:
        try:
            return soup.find("span", class_="pip-product-identifier__value").text
        except:
            return None

    @staticmethod
    def __get_designer(soup: BeautifulSoup) -> str:
        try:
            description = soup.find("div", class_="pip-product-details__container")
            return description.find("div").find("p", class_="pip-product-details__label").text
        except:
            return None

    @staticmethod
    def __get_informations_about_product(soup: BeautifulSoup) -> Dict:
        informations = {}

        try:
            # Description
            description = soup.find("div", class_="pip-product-details__container")
            paragraphs = description.find_all("p", class_="pip-product-details__paragraph")
            for paragraph in paragraphs:
                if "description" not in informations:
                    informations["description"] = paragraph.get_text(separator="\n", strip=True)
                else:
                    informations["description"] += paragraph.get_text(separator="\n", strip=True)

            # Good to know
            good_to_know = soup.find("li", id="product-details-good-to-know")
            if good_to_know:
                informations["good_to_know"] = good_to_know.get_text(separator="\n", strip=True)

            # Materials and care
            material_and_care = soup.find("li", id="product-details-material-and-care")
            if material_and_care:
                informations["material_and_care"] = material_and_care.get_text(separator="\n", strip=True)

            # Security and compliance
            safety_and_compliance = soup.find("li", id="product-details-safety-and-compliance")
            if safety_and_compliance:
                informations["safety_and_compliance"] = safety_and_compliance.get_text(separator="\n", strip=True)

            # Assembly and documents
            assembly_and_documents = soup.find("li", id="product-details-assembly-and-documents")
            if assembly_and_documents:
                informations["assembly_and_documents"] = assembly_and_documents.get_text(separator="\n", strip=True)
        except:
            return None

        if informations:
            return informations
        else:
            return None

    @staticmethod
    def __get_items_in_the_set(soup: BeautifulSoup) -> str:
        try:
            product_list = soup.find("div", class_="pip-included-products__list")\
            .find_all("div", class_="pip-included-products__container")
        
            products = []
            for product in product_list:
                product = product.find("div", class_="pip-product-card")\
                                .find("a", class_="pip-product-card__link pip-link")\
                                .find("div", class_="pip-product-card__info-container")
                title = product.find("span", class_="pip-product-card__title")\
                            .get_text(separator="\n", strip=True)
                measurement = product.find("span", class_="pip-product-card__measurement-text")\
                                    .get_text(separator="\n", strip=True)
                products.append({
                    "title": title,
                    "measurement": measurement
                })
            return products
        except:
            return None

    @staticmethod
    def __get_sizes(soup: BeautifulSoup) -> Dict:
        try:
            dimensions = soup.find("div", class_="pip-product-dimensions")
            dimensions = dimensions.find("ul", class_="pip-product-dimensions__dimensions-container")
            return dimensions.get_text(separator="\n", strip=True)
        except:
            return None

    @staticmethod
    def __get_image(soup: BeautifulSoup, file_folder: str, product_id: str) -> str:
        try:
            image_url = soup.find("span", class_="pip-aspect-ratio-box pip-aspect-ratio-box--square")\
                .find("img")["src"]
            image_url = image_url.split("?")[0]
            extension = image_url.split(".")[-1]
            file_path = f"{file_folder}/{product_id}.{extension}"
            image_url = image_url + "?f=xl"
            response = requests.get(image_url)

            if response.status_code == 200:
                with open(file_path, 'wb') as f:
                    f.write(response.content)
                return file_path
            else:
                return None
        except:
            return None
        
    @staticmethod
    def __check_sections_availability(soup: BeautifulSoup):
        available_sections = []

        try:
            if soup.find("li", class_="pip-chunky-header__details"):
                available_sections.append("details")
        except:
            pass

        try:
            if soup.find("li", class_="pip-chunky-header__included-products"):
                available_sections.append("included-products")
        except:
            pass

        try:
            if soup.find("li", class_="pip-chunky-header__measurement"):
                available_sections.append("measurement")
        except:
            pass

        return available_sections

    @staticmethod
    def __scrape_product(product_url: str, driver: Chrome) -> Dict:
        driver.get(product_url)
        html_code = driver.page_source
        soup = BeautifulSoup(html_code, "html.parser")

        title = ScrapeProducts.__get_title(soup)
        subtitle = ScrapeProducts.__get_subtitle(soup)
        price = ScrapeProducts.__get_price(soup)
        description = ScrapeProducts.__get_description(soup)
        product_id = ScrapeProducts.__get_product_id(soup)
        designer = ScrapeProducts.__get_designer(soup)
        image_path = ScrapeProducts.__get_image(soup, "imgs", product_id)

        available_sections = ScrapeProducts.__check_sections_availability(soup)
        informations_about_product = None
        items_in_the_set = None
        sizes = None

        if "details" in available_sections:
            try:
                li_element = driver.find_element(By.CLASS_NAME, "pip-chunky-header__details")
                button = li_element.find_element(By.TAG_NAME, "button")
                button.click()
                time.sleep(0.1)

                html_code = driver.page_source
                soup = BeautifulSoup(html_code, "html.parser")
                informations_about_product = ScrapeProducts.__get_informations_about_product(soup)
            except:
                pass

        if "included-products" in available_sections:
            try:
                driver.get(product_url)

                li_element = driver.find_element(By.CLASS_NAME, "pip-chunky-header__included-products")
                button = li_element.find_element(By.TAG_NAME, "button")
                button.click()
                time.sleep(0.1)

                html_code = driver.page_source
                soup = BeautifulSoup(html_code, "html.parser")
                items_in_the_set = ScrapeProducts.__get_items_in_the_set(soup)
            except:
                pass

        if "measurement" in available_sections:
            try:
                driver.get(product_url)

                li_element = driver.find_element(By.CLASS_NAME, "pip-chunky-header__measurement")
                button = li_element.find_element(By.TAG_NAME, "button")
                button.click()
                time.sleep(0.1)

                html_code = driver.page_source
                soup = BeautifulSoup(html_code, "html.parser")
                sizes = ScrapeProducts.__get_sizes(soup)
            except:
                pass

        product = {}
        if title:
            product["title"] = title

        if subtitle:
            product["subtitle"] = subtitle

        if price:
            product["price"] = price

        if description:
            product["description"] = description

        if product_id:
            product["product_id"] = product_id

        if designer:
            product["designer"] = designer

        if informations_about_product:
            product["informations_about_product"] = informations_about_product

        if items_in_the_set:
            product["items_in_the_set"] = items_in_the_set

        if sizes:
            product["sizes"] = sizes

        if image_path:
            product["image_path"] = image_path

        return product
    
    @staticmethod
    def __scrape_products(products_urls: List[str], unscraped_path: str) -> List[Dict]:
        options = ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--window-size=1920x1080")
        options.add_argument("--disable-notifications")
        options.add_argument("--log-level=3")
        options.add_argument('--no-sandbox')
        options.add_argument("--disable-logging")
        options.add_experimental_option("excludeSwitches", ['enable-logging'])
        driver = Chrome(options=options)

        driver.get(products_urls[0].get("url"))
        time.sleep(5)
        print()

        ScrapeProducts.__click_cookie_accept(driver)

        products_metadata = []
        for product_data in tqdm(products_urls, desc="Downloading products info"):
            product = None

            for _ in range(5):
                try:
                    product = ScrapeProducts.__scrape_product(product_data.get("url"), driver)
                except:
                    time.sleep(5)
                    continue
                else:
                    break
            else:
                print(f"Unable to scrape product: {product_data.get("url")}")
                FileManager.add(product_data, unscraped_path)
                continue

            product["url"] = product_data.get("url")
            product["category"] = product_data.get("category")
            product["sub_category"] = product_data.get("sub_category")
            products_metadata.append(product)
        return products_metadata
        
    @staticmethod
    def scrape(input_path: str, output_path: str):
        products = FileManager.read(input_path)
        unscraped_path = "/".join(output_path.split("/")[:-1]) + "/products_unscraped.json"
        products_metadata = ScrapeProducts.__scrape_products(products, unscraped_path)
        FileManager.save(products_metadata, output_path)
