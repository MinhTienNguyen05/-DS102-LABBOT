import os
import threading
from pathlib import Path

# Get terminal size -> print more beautiful :>
TERMINAL_WIDTH = os.get_terminal_size().columns

# CHECK HTML PAGE SOURCE
CHECK_FORMATTED_PAGE_SOURCE_PATH = Path('./check_page_source/formatted.html')

# CHECKPOINT PATH
CHECKPOINTS_PATH = {
    'THEGIOIDIDONG': {
        'NAME': 'THEGIOIDIDONG',
        # 'CHECKPOINT': Path('./data/checkpoints_thegioididong'),
        # 'CRAWL': Path('./data/checkpoints_thegioididong/previous_crawl_info.json'),
        # 'EXTRACT': Path('./data/checkpoints_thegioididong/previous_extract_info.json'),
        # 'LINK_LIST': Path('./data/checkpoints_thegioididong/previous_link_list.json'),
        'FOLDER_FRAUD_DETECTION_ENV_NAME': 'FOLDER_FRAUD_DETECTION_ID',
        'FOLDER_WEB_ENV_NAME': 'FOLDER_THEGIOIDIDONG',
        'FOLDER_STORAGE_ID_ENV_NAME': 'FOLDER_THEGIOIDIDONG_STORAGE_ID',
        'FOLDER_IMG_STORAGE_ID_ENV_NAME': 'FOLDER_THEGIOIDIDONG_IMG_STORAGE_ID',
        'FOLDER_SCRAPING_ENV_NAME': 'FOLDER_THEGIOIDIDONG_SCRAPING'
    },
}

# DATA PATH
ORIGINAL_PATH_FUNC = lambda web_name, name = '': Path(f'./data/data_{web_name.lower()}/' + name)
DATA_PATH_FUNC = lambda web_name, name = '': Path(f'./data/data_{web_name.lower()}/page_source/' + name)
IMG_PATH_FUNC = lambda web_name, name = '': Path(f'./data/data_{web_name.lower()}/images/' + name)

# ACCESS TOKEN PATH
ACCESS_TOKEN_PATH = Path('./data/access_token/access_token.json')
TOKEN_CACHE_PATH = Path('./data/access_token/token_cache.bin')

# DRIVER
DRIVER_PATH = lambda num: Path(f'/Users/hoangvinh/OneDrive/Workspace/Support/Driver/chromedriver-mac-x64_{str(num)}/chromedriver')

# COOKIES PATH
COOKIES_PATH = Path('./data/cookies/cookies.json')

MAX_WORKERS = 2