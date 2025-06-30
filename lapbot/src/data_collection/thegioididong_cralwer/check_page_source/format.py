from bs4 import BeautifulSoup
from shared.globals import CHECK_FORMATTED_PAGE_SOURCE_PATH, DATA_PATH_FUNC
import json
import requests


def format_html_page_source(page_source):
    soup = BeautifulSoup(page_source, 'html.parser')

    page_source_formatted = soup.prettify()

    with open(CHECK_FORMATTED_PAGE_SOURCE_PATH, 'w') as file:
        file.write(page_source_formatted)

if __name__ == '__main__':
    # with open(DATA_PATH_FUNC('thegioididong', 'l2_20250402-105034.json')) as file:
    #     data = json.load(file)
    
    # page_source = data['page_source']
    # format_html_page_source(page_source)
    response = requests.get('https://fptshop.com.vn/may-tinh-xach-tay/asus-tuf-gaming-a15-fa506ncr-hn047w-r7-7435hs')
    format_html_page_source(response.text)