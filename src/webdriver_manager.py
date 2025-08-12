import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options


class WebDriverManager:
    def __init__(self, headless: bool = True):
        options = Options()
        if headless:
            options.add_argument("--headless")
        service = Service()
        self.driver = webdriver.Chrome(service=service, options=options)

    def get_page_source(self, url: str, wait: float = 2.0) -> str:
        self.driver.get(url)
        time.sleep(wait)
        return self.driver.page_source

    def quit(self):
        self.driver.quit()
