from bs4 import BeautifulSoup
from shared.colorful import print_banner_colored
from shared.support_func import string_to_dict, get_data_safe, get_base64_imgs, base64_to_binary
from shared.globals import IMG_PATH_FUNC, DATA_PATH_FUNC, DRIVER_PATH
import re
import requests
import sys
import json
import clickhouse_connect
import pprint
from check_page_source.format import format_html_page_source
from datetime import datetime
import threading
import asyncio
from fake_useragent import UserAgent
from selenium import webdriver
from selenium.webdriver.chrome.service import Service

ua = UserAgent()

def get_driver():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument(f"user-agent={ua.random}")
    # chrome_options.add_argument('--disable-web-security')
    # chrome_options.add_argument('--allow-running-insecure-content')
    # chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    # chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
    # chrome_options.add_experimental_option("useAutomationExtension", False)
    # chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument('--headless')

    driver_num = 1
    chrome_service = Service(DRIVER_PATH(driver_num))

    driver = webdriver.Chrome(options=chrome_options, service=chrome_service)
    driver.implicitly_wait(5)

    return driver

def save_img(binary_img_links, web_name, name):
    folder_path = IMG_PATH_FUNC(web_name, name)
    folder_path.mkdir(exist_ok=True)

    for idx, binary_img_link in enumerate(binary_img_links):
        file_path = folder_path / f'{name}_{str(idx)}.jpg'
        with open(file_path, 'wb') as file:
            file.write(binary_img_link)
                
def extract_one_page_source(driver, page_source_raw, file_name):
    page_source_data = page_source_raw['page_source']
    format_html_page_source(page_source_data)
    try:
        data = {}
        soup = BeautifulSoup(page_source_data, 'html.parser')
        data['Link'] = page_source_raw['link']
        data['Tiêu đề'] = get_data_safe(soup, '.product-name > h1', return_text=True)
        data['Đã bán'] = get_data_safe(soup, '.quantity-sale', return_text=True)

        if get_data_safe(soup, '.bs_price', return_text=True):
            data['Giá hiện tại'] = get_data_safe(soup, '.bs_price > strong', return_text=True)
            data['Giá cũ'] = get_data_safe(soup, '.bs_price > em', return_text=True)
            data['Giảm giá (%)'] = get_data_safe(soup, '.bs_price > i', return_text=True)
        else:
            data['Giá hiện tại'] = get_data_safe(soup, '.box-price-present', return_text=True)
            data['Giá cũ'] = get_data_safe(soup, '.box-price-old', return_text=True)
            data['Giảm giá (%)'] = get_data_safe(soup, '.box-price-percent', return_text=True)

        # specification-item
        spec_items = get_data_safe(soup, '.specification-item > .box-specifi', multi_value=True)
        for spec_item in spec_items:
            items = get_data_safe(spec_item, 'ul > li', multi_value=True)
            for item in items:
                key = get_data_safe(item, 'aside:nth-child(1)', return_text=True)
                value = get_data_safe(item, 'aside:nth-child(2)', return_text=True)
                data[key] = value
        # detail
        content_detail = get_data_safe(soup, '.text-detail', return_text=True)
        if content_detail is not None:
            describe_pattern = re.compile("["
                    u"\U0001F600-\U0001F64F"  # emoticons
                    u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                    u"\U0001F680-\U0001F6FF"  # transport & map symbols
                    u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                "]+", flags=re.UNICODE)
            data['Chi tiết'] = describe_pattern.sub(r'', content_detail) # no emoji
            data['Chi tiết'] = re.sub("'", '"', data['Chi tiết'])
        else:
            data['Chi tiết'] = None
        
        data['Màu'] = get_data_safe(soup, '.box03 > a.act', return_text=True)

        # img
        
        url_imgs_element = get_data_safe(soup, '.gallery-img .item-img > img', multi_value=True)
        if url_imgs_element:
            url_imgs = []
            for element in url_imgs_element:
                url_imgs.append(get_data_safe(element, attr='src') or get_data_safe(element, attr='data-src'))
            data['Url ảnh'] = ';'.join(url_imgs)
            # Save ảnh local
            # base64_imgs = get_base64_imgs(driver, url_imgs)
            # binary_imgs = base64_to_binary(base64_imgs)
            # save_img(binary_imgs, 'thegioididong', file_name)

        print_banner_colored(f'Scraping successful {file_name}!', 'success')
        return data
    except KeyboardInterrupt:
        sys.exit("NGẮT CHƯƠNG TRÌNH TỪ BÀN PHÍM !!")
    except Exception as e:
        print_banner_colored(f'Scraping failed {file_name}!', 'danger')
        raise Exception(e)


def main():
    driver = None
    # driver = get_driver()
    client = clickhouse_connect.get_client(host='localhost', username='default')

    # Create database
    client.command('''
        CREATE DATABASE IF NOT EXISTS THEGIOIDIDONG
    ''')

    client.command('USE THEGIOIDIDONG')

    # Create table crawled
    client.command('''
        CREATE TABLE IF NOT EXISTS THEGIOIDIDONG.RAW_DATA (
            `filename` String,                  -- Tên file lưu (để lấy ra so sánh cho nhanh)
            `filename_origin` String,
            `time_scraping` String
        )
        ENGINE = MergeTree()
        PRIMARY KEY (`filename`);
    ''')

    columns = client.query('''DESCRIBE TABLE THEGIOIDIDONG.RAW_DATA ''')
    columns = columns.result_columns[0]

    link_scraped = client.query('''
        SELECT r.filename, r.filename_origin
        FROM THEGIOIDIDONG.RAW_DATA as r
    ''')

    link_scraped = link_scraped.result_rows if link_scraped.result_rows else []
    link_scraped_filename = [link[0] for link in link_scraped]

    for file_path in DATA_PATH_FUNC('thegioididong').iterdir():
        if file_path.stem in link_scraped_filename:
            continue
        
        with open(file_path, 'r') as file:
            data_page_source_raw = json.load(file)
            data_scraped = extract_one_page_source(driver, data_page_source_raw, file_path.stem) 
            data_scraped.update({
                'filename': file_path.stem,
                'filename_origin': file_path.stem.split('__')[1],
                'time_scraping': datetime.now()
            })

            data_keys = list(data_scraped.keys())
            data_values = list(data_scraped.values())

            for index, key in enumerate(data_keys):
                if key not in columns:
                    columns.append(key)

                    client.command(f'''
                        ALTER TABLE THEGIOIDIDONG.RAW_DATA 
                        ADD COLUMN `{key}` Nullable(String)
                    ''')

                    data_values[index] = str(data_values[index])
            client.command(f'''INSERT INTO THEGIOIDIDONG.RAW_DATA ({', '.join([f'`{key}`' for key in data_keys])}) VALUES ({', '.join([f"'{value}'" for value in data_values])})''')

            # Này thiết cột thì chạy lại không được ??
            # client.insert(
            #     table='THEGIOIDIDONG.RAW_DATA',
            #     data=data_values,
            #     column_names=data_keys
            # )

    
def test():
    # driver = get_driver()
    driver = None
    with open('./data/data_thegioididong/page_source/0220042002611__L285_20250402-105034.json', 'r') as file:
        data = json.load(file)
        format_html_page_source(data['page_source'])
        # Chú ý cho time_scraped vào !!
        pprint.pprint(extract_one_page_source(driver, data, 'helooooo'))


if __name__ == '__main__':
    main()
    # test()