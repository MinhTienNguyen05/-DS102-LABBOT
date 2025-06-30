from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import os
import time

def set_up_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-blink-feature=AutomationControlled")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    service = Service(executable_path = "./Chromedriver")
    driver = webdriver.Chrome(service = service, options = chrome_options)

    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

def click_show_more(driver):
    while True:
        try:
            # Wait for button arrive
            show_more_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(@class, 'btn-show-more')]"))
            )
            # Scroll to that button
            ActionChains(driver).move_to_element(show_more_button).perform()
            time.sleep(0.5)

            # Click button
            driver.execute_script("arguments[0].click();", show_more_button)
            print("Clicked 'Xem them'")

            # Wait for loading
            time.sleep(2)
        except Exception as e:
            print(f'No more "Xem them" button or having errors: {e}')
            break

def get_url(driver, output_file):
    try:
        # urls = driver.find_elements(By.XPATH, "//div[@class='block-product-list-filter']//a[@class='product__link button__link']"))
        urls = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, "//div[@class='block-product-list-filter']//a[@class='product__link button__link']"))
        )
        # Create file if file is not exist
        if not os.path.exists(output_file):
            with open(output_file, "w", encoding = "utf-8") as f:
                f.write('url\n')

        # Write url to output_file
        with open(output_file, 'a', encoding = "utf-8") as f:
            for url in urls:
                link = url.get_attribute('href')
                f.write(link.strip() + '\n')

    except Exception as e:
        import traceback
        print(f'Error in collect laptop url: ')
        traceback.print_exc()

def main():
    driver = set_up_driver()
    url = "https://cellphones.com.vn/laptop.html"
    output_file = "CellphoneS_Laptop_url.csv"
    driver.get(url)
    click_show_more(driver)
    get_url(driver,output_file)
    driver.quit()

if __name__ == "__main__":
    main()