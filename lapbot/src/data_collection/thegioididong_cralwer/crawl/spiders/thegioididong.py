import scrapy
from urllib.parse import urlencode
import os
from check_page_source.format import format_html_page_source
from shared.colorful import print_banner_colored
from shared.support_func import get_data_safe
from shared.globals import DRIVER_PATH, DATA_PATH_FUNC
import dotenv
import time
from datetime import datetime
import json
import clickhouse_connect
import functools
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver import ActionChains
from selenium.webdriver.common.keys import Keys
import math
import pyautogui
from bs4 import BeautifulSoup
import random

from fake_useragent import UserAgent
ua = UserAgent()

def get_driver():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument(f"user-agent={ua.random}")
    chrome_options.add_argument('--disable-web-security')
    chrome_options.add_argument('--allow-running-insecure-content')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    chrome_options.add_argument("--start-maximized")
    # chrome_options.add_argument('--headless')

    driver_num = 1
    chrome_service = Service(DRIVER_PATH(driver_num))

    driver = webdriver.Chrome(options=chrome_options, service=chrome_service)
    driver.implicitly_wait(5)

    return driver

def get_link_page(base_link, page_num):
    return f'{base_link}&pi={page_num}'

def typing(text, include_typo=True):
    for char in text:
        delay = random.uniform(0.1, 0.4)
        pyautogui.typewrite(char, interval=delay)

def find_all_links(base_link):
    driver = get_driver()
    driver.get(f'{base_link}&pi={0}')

    # Lấy được number page cần
    try:
        button = driver.find_element(By.CSS_SELECTOR, '.see-more-btn .remain')
        remain_laptop = int(button.text)
    except Exception as e:
        print('ERROR: ', e)
        raise ValueError('KHÔNG TÌM THẤY BUTTON CLICK??')

    last_page = math.ceil(float(remain_laptop) / 20.0)
    new_url = f'{base_link}&pi={last_page}'

    # Thao tác thanh url -> load được page đó
    pyautogui.moveTo(520, 90)
    time.sleep(1)
    pyautogui.click()
    time.sleep(1)

    print(new_url)
    pyautogui.write(new_url, interval=0.5)
    pyautogui.press("enter")
    time.sleep(2)

    driver.refresh()
    time.sleep(2)

    # Nhận diện được khi nào nó hết load
    while True:
        try:
            element = driver.find_element(By.CSS_SELECTOR, '#preloader')
            style = element.get_attribute('style')
            if 'block' in style:
                time.sleep(4)
            elif 'none' in style:
                break
            else:
                raise ValueError('Block và None đều không phải, có khả năng đã thay đổi class!!')
        except KeyboardInterrupt:
            print_banner_colored('ĐÃ OUT VÌ KEYBOARD!')
        except ValueError as ve:
            print_banner_colored(ve, 'danger')
        except:
            time.sleep(4)
            print_banner_colored('Vẫn chưa load xong!', 'danger')
                

    # format_html_page_source(driver.page_source)

    soup = BeautifulSoup(driver.page_source, 'html.parser')
    links_get_from_ps = get_data_safe(soup, '.__cate_44 > a', multi_value=True, attr='href')
    urls_extracted_from_links = ['https://www.thegioididong.com' + link for link in links_get_from_ps]
    print_banner_colored(f'LINK HIỆN ĐANG CÓ TRONG PAGE: {len(urls_extracted_from_links)}')
    for i in range(5):
        print(urls_extracted_from_links[i])

    driver.quit()

    return urls_extracted_from_links




class ThegioididongSpider(scrapy.Spider):
    name = "thegioididong"

    base_link = 'https://www.thegioididong.com/laptop#c=44&o=13'
    time_start_run_str = datetime.now().strftime("%Y%m%d-%H%M%S")
    time_start_run_datetime = datetime.now()
    links_crawled = []
    page_crawled = []

    custom_settings = {
        'USER_AGENT': ua.random
    }

    def get_link_page(self, page_num):
        return f'{self.base_link}?pi={page_num}'
    
    def start_requests(self):
        print_banner_colored('ĐÃ VÀO THEGIOIDIDONG', 'success')

        # links = [
        #     'https://www.thegioididong.com/laptop/asus-vivobook-go-15-e1504fa-r5-nj776w',
        #     'https://www.thegioididong.com/laptop/hp-15-fc0085au-r5-a6vv8pa'
        # ]
        # links = [] # Nếu link có sẵn rồi và không muốn tìm link nữa
        links = find_all_links(self.base_link)

        self.client = clickhouse_connect.get_client(host='localhost', username='default')
        # Create database
        self.client.command('''
            CREATE DATABASE IF NOT EXISTS THEGIOIDIDONG
        ''')

        self.client.command('USE THEGIOIDIDONG')
        # Create table crawled
        self.client.command('''
            CREATE TABLE IF NOT EXISTS THEGIOIDIDONG.CRAWLED_STATUS (
                name String,
                link String,
                link_num UInt32,
                status Bool,
                time_crawled DateTime
            )
            ENGINE = ReplacingMergeTree(time_crawled)
            PRIMARY KEY link
        ''')

        self.client.command('''
            CREATE TABLE IF NOT EXISTS THEGIOIDIDONG.COLOR_PAGE (
                name String,
                filename_color String,
                color_code String,
                color_link String,
                time_crawled DateTime
            )
            ENGINE = ReplacingMergeTree(time_crawled)
            PRIMARY KEY color_link
        ''')

        # Merge replace old -> new
        self.client.command('''
            OPTIMIZE TABLE THEGIOIDIDONG.CRAWLED_STATUS FINAL
        ''')
        self.client.command('''
            OPTIMIZE TABLE THEGIOIDIDONG.COLOR_PAGE FINAL
        ''')

        # Get page minimun in pending status, then run from that page to inf
        page_not_crawled = self.client.query('''
            SELECT *
            FROM THEGIOIDIDONG.CRAWLED_STATUS AS pcs
            WHERE pcs.status = 0
        ''')
        
        # self.page_crawl_not_done = page_not_crawled.result_columns[0] if page_not_crawled.result_columns else []
        self.page_crawl_not_done = page_not_crawled.result_rows if page_not_crawled.result_rows else []

        # Get page crawled done
        page_crawled = self.client.query('''
            SELECT pcs.link
            FROM THEGIOIDIDONG.CRAWLED_STATUS AS pcs
            WHERE pcs.status = 1
        ''')

        self.page_crawl_done = page_crawled.result_columns[0] if page_crawled.result_columns else []

        # Column
        columns = self.client.query('''DESCRIBE TABLE THEGIOIDIDONG.CRAWLED_STATUS''')
        columns = columns.result_columns[0]

        # print('Not done: ', self.page_crawl_not_done)
        # print('Done: ', self.page_crawl_done)
        # print('Columns: ', columns)
        # Insert new
        links_new = []
        for idx in range(len(links)):
            if links[idx] not in self.page_crawl_done:
                links_new.append(['NN', link, idx, 0, self.time_start_run_datetime])
        # print('Link news: ', links_new)
        # for idx, link in enumerate(links_new):
        #     print(['NN', link, idx, 0, self.time_start_run_datetime])
        self.client.insert(
            table='THEGIOIDIDONG.CRAWLED_STATUS',
            data=links_new, 
            column_names=columns
        )
        print_banner_colored("ĐẾN ĐÂY RỒI!", 'success')
        self.page_crawl_not_done.extend(links_new)
        # Start to run query
        for link in self.page_crawl_not_done:
            yield scrapy.Request(
                url=link[1],
                callback=functools.partial(self.handle_link, url_origin=link[1], link_info=link)
            )

    def handle_link(self, response, url_origin, link_info):
        print_banner_colored(f'VÀO LINK: {url_origin}', 'small')
        print(link_info)
        # print_banner_colored(f'Bắt đầu xử lí page_{page_num} link_{link_num} url_{url_origin}', 'wait')
        format_html_page_source(response.text)   # Nếu cần check html
        soup = BeautifulSoup(response.text, 'html.parser')
                
        color_links = get_data_safe(soup, '.box03.color > a', multi_value=True, attr='href')
        color_links = ['https://www.thegioididong.com' + link for link in color_links]
        color_code = get_data_safe(soup, '.box03.color > a', multi_value=True, attr='data-code')

        print('ALL LINK CON MÀU : ')
        print(color_links, color_code)
            
        time_crawled = datetime.now()
        link_num = link_info[2]

        file_name = f'l{link_num}_{self.time_start_run_str}' + '.json'
        if link_info[0] != 'NN': file_name = link_info[0]
        
        if color_links:
            print('FILENAME ORIGINAL: ', file_name)
            for link, code in zip(color_links, color_code):
                yield scrapy.Request(
                    url=link,
                    callback=functools.partial(self.handle_link_color, code=code, filename=file_name, url=link)
                )
        else:
            yield scrapy.Request(
                url=link_info[1],
                callback=functools.partial(self.handle_link_color, code='0', filename=file_name, url=link_info[1])
            )

        print('LƯU LINK LÊN CLICKHOUSE')
        # # Lưu lại status lên Clickhouse
        status_data_crawled = [
            [file_name, url_origin, link_num, 1, time_crawled]
        ]
        self.client.insert(
            table='THEGIOIDIDONG.CRAWLED_STATUS', 
            data=status_data_crawled, 
            column_names=['name', 'link', 'link_num', 'status', 'time_crawled']
        )

    def handle_link_color(self, response, code, filename, url): 
        print_banner_colored(f'VÀO LINK CON: {url}', 'wait')     
        time_crawled = datetime.now()
        
        data = {
            'link': url,
            'time_crawled': time_crawled.isoformat(),
            'page_source': response.text
        }

        filename_color = code + '__' + filename
        # print('FILENAME_COLOR: ', filename_color)

        # Lưu page source local
        with open(DATA_PATH_FUNC('thegioididong', filename_color), 'w') as file:
            print('VÀO ĐỂ LƯU DATA VÀO PAGE SOURCE')
            json.dump(data, file)

        # Lưu lại status lên Clickhouse
        status_data_crawled = [
            [filename, filename_color, code, url, time_crawled]
        ]
        print('CRAWL INFO: ', status_data_crawled)

        self.client.insert(
            table='THEGIOIDIDONG.COLOR_PAGE', 
            data=status_data_crawled, 
            column_names=['name', 'filename_color', 'color_code', 'color_link', 'time_crawled']
        )

        print_banner_colored(f'XONG LINK CON: {url}', 'success')


