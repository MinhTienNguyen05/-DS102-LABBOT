import ast
import random
import re
import json
import pickle
import base64
import os
from pathlib import Path
import time
import dotenv
import threading
# from bs4 import BeautifulSoup
# from datetime import datetime
# from shared.globals import TERMINAL_WIDTH, CHECKPOINTS_PATH, COOKIES_PATH, DRIVER_PATH, LOCK_LINK_LIST, UPDATE_TIME, CHECKPOINTS_PATH_TEST
# from msgraph_onedrive.operations import upload_file, upload_img, create_folder, search_file_id, download_file
# from msgraph_onedrive.syn import update_crawl_info, update_link_list, update_extract_info
from shared.colorful import print_banner_colored

def string_to_dict(text: str):
    # print(text)
    # Erase indent start and end of string (if not -> IndentationError: unexpected indent)
    text = text.strip()
    # Some marks are wrong
    text = text.replace('`', "'").replace('"', "'")
    # Key need to be in quotes
    text = re.sub(r'(\w+): ', r"'\1': ", text)
    # Change to dict
    value_dict_type = ast.literal_eval(text)

    return value_dict_type

def get_data_safe(soup, text_selector = None, multi_value = False, return_text = False, attr = ''):
    try:
        if multi_value:
            elements = soup.select(text_selector) if text_selector else soup

            if len(elements) == 0: return None

            if return_text:
                return [element.get_text() for element in elements]
            elif attr:
                return [element[attr] for element in elements if element[attr]]
            else:
                return elements 
        else:
            element = soup.select_one(text_selector)  if text_selector else soup
            if return_text:
                return element.get_text()
            elif attr:
                return element[attr]
            else:
                return element 
    except:
        return None
    

# def get_base64_imgs(driver, img_links):
#     driver.execute_script('''
#         window.getBase64FromImageUrl = async function(url) {
#             return new Promise((resolve, reject) => {
#                 var img = new Image();
#                 img.crossOrigin = 'anonymous'; // CORS bypass
#                 img.onload = function () {
#                     var canvas = document.createElement("canvas");
#                     canvas.width = this.width;
#                     canvas.height = this.height;

#                     var ctx = canvas.getContext("2d");
#                     ctx.drawImage(this, 0, 0);

#                     var dataURL = canvas.toDataURL("image/jpeg"); // Export Base64 as JPEG
#                     resolve(dataURL);
#                 };

#                 img.onerror = function () {
#                     reject("Failed to load image from URL.");
#                 };

#                 img.src = url;
#             });
#         };
#     ''')   

#     imgs_base64 = []

#     for i in range(len(img_links)):
#         base64_data = driver.execute_script(f'return getBase64FromImageUrl("{img_links[i]}")')
#         imgs_base64.append(base64_data)

#     return imgs_base64

def get_base64_imgs(driver, img_links):
    try_again = 0
    while True:
        try:
            driver.execute_script('''
                window.getBase64FromImageUrl = async function(url) {
                    return new Promise((resolve, reject) => {
                        var img = new Image();
                        img.crossOrigin = 'anonymous'; // CORS bypass
                        img.onload = function () {
                            var canvas = document.createElement("canvas");
                            canvas.width = this.width;
                            canvas.height = this.height;

                            var ctx = canvas.getContext("2d");
                            ctx.drawImage(this, 0, 0);

                            var dataURL = canvas.toDataURL("image/jpeg"); // Export Base64 as JPEG
                            resolve(dataURL);
                        };

                        img.onerror = function () {
                            reject("Failed to load image from URL.");
                        };

                        img.src = url;
                    });
                };
            ''')

            script = f'''
                return await Promise.all([
                    {','.join([f'getBase64FromImageUrl("{link}")' for link in img_links])}
                ]);
            '''

            base64_data = driver.execute_script(script)
            return base64_data
        except KeyboardInterrupt:
            raise KeyboardInterrupt('STOP GET BASE64 FROM URL BY KEYBOARD!')
        except Exception as e:
            time.sleep(2)
            print_banner_colored('Thử lại lấy base64 từ url', 'danger')
            try_again += 1
            if try_again >= 5:
                raise Exception(e)


def base64_to_binary(base64_list):
    binary_list = []

    for index in range(len(base64_list)):
        if base64_list[index].lstrip().startswith('data:image'):
            base64_data = base64_list[index].split(',')[1]
        else:
            base64_data = base64_list[index]
        
        binary_data = base64.b64decode(base64_data)

        binary_list.append(binary_data)
    
    return binary_list
