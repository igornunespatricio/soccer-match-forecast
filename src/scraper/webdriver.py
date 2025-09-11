import os
import random
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from webdriver_manager.chrome import (
    ChromeDriverManager as WDM_ChromeDriverManager,
)  # Renamed import


class ChromeDriverWrapper:
    """Enhanced Chrome WebDriver manager with anti-blocking and performance features"""

    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/118.0",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
    ]

    PROXIES = [
        "http://user:pass@proxy1:port",
        "http://user:pass@proxy2:port",
    ]

    def __init__(self, headless=True, timeout=30, use_proxy=False):
        self.headless = headless
        self.timeout = timeout
        self.use_proxy = use_proxy
        self.driver = None

    def _configure_options(self):
        """Configure Chrome options with anti-blocking and performance settings"""
        options = ChromeOptions()

        # Anti-blocking features
        options.add_argument(f"user-agent={random.choice(self.USER_AGENTS)}")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        if self.use_proxy:
            options.add_argument(f"--proxy-server={self._get_random_proxy()}")

        # Performance optimizations
        if self.headless:
            options.add_argument("--headless=new")
            options.add_argument("--disable-software-rasterizer")

        options.add_argument("--disable-extensions")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-default-apps")
        options.add_argument("--disable-translate")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--blink-settings=imagesEnabled=false")
        options.add_argument("--disable-javascript")

        return options

    def _get_random_proxy(self):
        """Get a random proxy from the list"""
        return random.choice(self.PROXIES)

    def _configure_environment(self):
        """Configure environment variables"""
        os.environ["WDM_LOG_LEVEL"] = "0"
        os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

    def _configure_driver(self, options):
        """Configure the WebDriver instance"""
        service = ChromeService(
            WDM_ChromeDriverManager().install(),  # Use the renamed import
            service_args=["--silent"],
            log_path=os.devnull,
        )

        driver = webdriver.Chrome(service=service, options=options)
        driver.set_page_load_timeout(self.timeout)
        driver.implicitly_wait(2)
        driver.set_window_size(random.randint(1200, 1920), random.randint(800, 1080))

        # Set user agent via CDP
        user_agent = options.arguments[0].split("=")[1]
        driver.execute_cdp_cmd(
            "Network.setUserAgentOverride",
            {"userAgent": user_agent, "platform": random.choice(["Win32", "MacIntel"])},
        )

        return driver

    def get_driver(self):
        """Get a configured Chrome WebDriver instance"""
        self._configure_environment()
        options = self._configure_options()
        self.driver = self._configure_driver(options)
        return self.driver

    def close(self):
        """Close the WebDriver instance"""
        if self.driver:
            self.driver.quit()
            self.driver = None


class EnhancedChromeDriver(ChromeDriverWrapper):
    """Extended version with additional features"""

    def human_interaction(self, scroll_pixels=500, delay_range=(1, 3)):
        """Simulate human-like interactions"""
        if not self.driver:
            raise ValueError("Driver not initialized")

        self.driver.execute_script(f"window.scrollBy(0, {scroll_pixels})")
        time.sleep(random.uniform(*delay_range))


if __name__ == "__main__":
    # Example usage
    driver_manager = EnhancedChromeDriver(headless=True, timeout=45, use_proxy=False)

    try:
        driver = driver_manager.get_driver()
        driver.get("https://www.wikipedia.org")

        # Simulate human interaction
        driver_manager.human_interaction()

        print(f"Page title: {driver.title}")

    finally:
        driver_manager.close()
