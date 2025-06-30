# Scrapy settings for cellphones project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html
import random
import os
from pathlib import Path
from unittest.mock import DEFAULT

from dotenv import load_dotenv
from scrapy.settings.default_settings import DOWNLOAD_DELAY, USER_AGENT, DEFAULT_REQUEST_HEADERS, LOG_FILE, LOG_LEVEL

base_folder = Path(__file__).parent.parent.absolute() # determine the path of root folder
load_dotenv(os.path.join(str(base_folder), ".env"))

BOT_NAME = "cellphones"

SPIDER_MODULES = ["cellphones.spiders"]
NEWSPIDER_MODULE = "cellphones.spiders"


# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = "cellphones (+http://www.yourdomain.com)"

# Obey robots.txt rules
ROBOTSTXT_OBEY = True

# Configure maximum concurrent requests performed by Scrapy (default: 16)
#CONCURRENT_REQUESTS = 32

# Configure a delay for requests for the same website (default: 0)
# See https://docs.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
#DOWNLOAD_DELAY = 3
# The download delay setting will honor only one of:
#CONCURRENT_REQUESTS_PER_DOMAIN = 16
#CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
#COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
#TELNETCONSOLE_ENABLED = False

# Override the default request headers:
#DEFAULT_REQUEST_HEADERS = {
#    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
#    "Accept-Language": "en",
#}

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
#SPIDER_MIDDLEWARES = {
#    "cellphones.middlewares.CellphonesSpiderMiddleware": 543,
#}

# Enable or disable downloader middlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#DOWNLOADER_MIDDLEWARES = {
#    "cellphones.middlewares.CellphonesDownloaderMiddleware": 543,
#}

# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
#EXTENSIONS = {
#    "scrapy.extensions.telnet.TelnetConsole": None,
#}

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
#ITEM_PIPELINES = {
#    "cellphones.pipelines.CellphonesPipeline": 300,
#}

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
#AUTOTHROTTLE_ENABLED = True
# The initial download delay
#AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
#AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
#AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
#AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
#HTTPCACHE_ENABLED = True
#HTTPCACHE_EXPIRATION_SECS = 0
#HTTPCACHE_DIR = "httpcache"
#HTTPCACHE_IGNORE_HTTP_CODES = []
#HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"

# Store log but not print in terminal
LOG_LEVEL = 'INFO'
LOG_FILE = 'output/log.txt'


# Set settings whose default value is deprecated to a future-proof value
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED = {
    "output/cellphones_laptop.csv": {
        "format": "csv",
        "encoding": "utf8",
        "overwrite": True,
    },
}
DOWNLOAD_DELAY = 2 # Avoid being banned
USER_AGENT = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0"
]

DEFAULT_REQUEST_HEADERS = {
    "User-Agent": random.choice(USER_AGENT)
}
HTTP_PROXY_LIST = [
    "http://user:password@proxy1.com:8000",
    "http://user:password@proxy2.com:8000",
    "http://user:password@proxy3.com:8000",
]

VALID_URL_PREFIXES = os.getenv('VALID_URL_PREFIXES')
INPUT_FILE = os.getenv('INPUT_FILE')
OUTPUT_DIR = os.getenv('OUTPUT_DIR')
OUTPUT_FILES = os.getenv('OUTPUT_FILES')
BATCH_SIZE = os.getenv('BATCH_SIZE')
NUM_THREADS = os.getenv('NUM_THREADS')

ITEM_PIPELINES = {
    'cellphones.pipelines.LaptopPipeline': 300,
}
