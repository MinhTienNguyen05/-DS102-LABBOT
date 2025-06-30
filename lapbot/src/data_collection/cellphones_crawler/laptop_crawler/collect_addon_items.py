#!/usr/bin/env python3
"""
Script to collect add_on items with root product_id

Step 01: Fetch list of add_on products id by recommendation query using root product_id
Step 02: Save list of add_on products id to json file with key: root product key and value: list of add_on products
step 03: Fetch add_on items detail and save to csv

"""
import csv
import html
import time
import re

from pandas.io.common import file_exists
from tqdm import tqdm
import requests
import json
import os

from urllib3.filepost import writer

INPUT_CSV_FILE = 'cellphones_laptops_category_380.csv'
OUTPUT_CSV_FILE = 'laptop_addon_products_test.csv'

RECOMMENDATION_API_URL = 'https://api.cellphones.com.vn/recommendation/v1/recommend?product_id={}'
GRAPHQL_API_URL = 'https://api.cellphones.com.vn/v2/graphql/query'

HEADERS_GET = {
    "accept": "application/json, text/plain, */*", # Chấp nhận nhiều loại content hơn
    "accept-language": "en-US,en;q=0.9,vi;q=0.8",
    "origin": "https://cellphones.com.vn",
    "priority": "u=1, i",
    "referer": "https://cellphones.com.vn/",
    "sec-ch-ua": "\"Chromium\";v=\"124\", \"Google Chrome\";v=\"124\", \"Not-A.Brand\";v=\"99\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\"",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-site",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "x-guest-token": "your_guest_token_if_needed", # Thêm guest token nếu API yêu cầu
    # Thêm các headers cần thiết khác nếu API GET yêu cầu
}

HEADERS_POST = {
    "accept": "application/json",
    "accept-language": "en-US,en;q=0.9",
    "cache-control": "no-cache",
    "content-type": "application/json",
    "origin": "https://cellphones.com.vn",
    "pragma": "no-cache",
    "priority": "u=1, i",
    "referer": "https://cellphones.com.vn/",
    "sec-ch-ua": "\"Chromium\";v=\"124\", \"Google Chrome\";v=\"124\", \"Not-A.Brand\";v=\"99\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\"",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-site",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}

QUERY_TEMPLATE = '''
    query getProductListByArrayId{
        products(
            filter: {
                static: {
                  is_parent: "true",
                  province_id: 30,
                  product_id: {addon_product_ids_str},
                  stock: {
                    from: 1
                  },
                  stock_available_id: [46, 4920]
               }
            },
            sort: [{view: desc}]
            size: {dynamic_size}
        ){
            general{
                product_id
                url_path
                name
                child_product
                doc_quyen
                attributes
                categories {
                    categoryId
                    level
                    name
                    uri
                    similar
                }
            },
            filterable{
              sticker
              is_installment
              stock_available_id
              company_stock_id
              is_parent
              price
              prices
              special_price
              promotion_information
              thumbnail
              promotion_pack
              flash_sale_types
            },
        }
      }
'''
def read_product_ids_from_csv(filename):
    '''Fetch root product_id from input csv file'''
    root_ids = []
    if not os.path.exists(filename):
        print(f'{filename} is not exist')
        return None
    print(f'Reading root laptop id from {filename}')
    try:
        with open(filename, mode ='r', encoding='utf-8-sig') as csvfile:
            reader = csv.DictReader(csvfile)
            if "product_id" not in reader.fieldnames:
                csvfile.seek(0)
                plain_reader = csv.reader(csvfile)
                header = next(plain_reader, None) # Read header, return None if file is empty
                if not header:
                    print(f'Could not find header in {filename}')
                    return None
                print(f'Could not find "product_id" column. Use first column instead: {header[0]}')
                for row in plain_reader:
                    if row and row[0]:
                        root_ids.append(row[0].strip()) # Make sure not empty
            else:
                for row in reader:
                    if row.get('product_id'):
                        root_ids.append(row['product_id'].strip())
        unique_ids = list(set(root_ids)) # Remove duplicated ids
        print(f'Read {len(root_ids)} root laptop id, {len(unique_ids)} unique ids')
        return unique_ids

    except Exception as e:
        print(f'Error in reading {filename}: {str(e)}')
        return None




def fetching_recommendation(root_laptop_id):
    """Fetch add-on products ids for each laptop product id using GET requests"""

    url = RECOMMENDATION_API_URL.format(root_laptop_id)
    addon_ids = []
    try:
        response = requests.get(url, headers=HEADERS_GET, timeout=15)
        response.raise_for_status()
        data = response.json()

        if data and 'data' in data and isinstance(data['data'], list):
            for item in data['data']:
                if 'product_id' in item:
                    addon_ids.append(str(item['product_id']))
        return addon_ids

    except requests.exceptions.Timeout:
        print(f'Timeout with {root_laptop_id}')
        return []

    except requests.exceptions.HTTPError as e:
        print(f'HTTP error with {root_laptop_id}: {e}')
        return []

    except requests.exceptions.RequestException as e:
        print(f'Request error with {root_laptop_id}: {str(e)}')
        return []

    except json.JSONDecodeError:
        print(f'Could decode JSON response for {root_laptop_id}')
        return []

    except Exception as e:
        print(f'Unwanted error with {root_laptop_id}: {str(e)}')
        return []

def fetch_addon_products_details(addon_products_ids):
    """Fetches details for a list of add_on products"""
    if not addon_products_ids:
        print('No add_on product id to fetch')
        return []

    # Format list of addon product into Json
    product_ids_json_list = json.dumps(addon_products_ids)
    size = len(addon_products_ids)

    # Create query
    query = QUERY_TEMPLATE.replace('{addon_product_ids_str}', product_ids_json_list)
    query =  query.replace('{dynamic_size}', str(size))

    payload = {
        'query': query,
        'variables': {}
    }
    try:
        response = requests.post(GRAPHQL_API_URL, headers=HEADERS_POST, json=payload, timeout=50)
        response.raise_for_status()
        data = response.json()


        if 'errors' in data:
            print(f'Error GraphQL API for product id {addon_products_ids}: {data["errors"]}')
            return []

        if 'data' in data and 'products' in data['data'] and data['data']['products'] is not None:
             return data['data']['products']

        else:
            print(f'No data for {addon_products_ids}')
            return []

    except requests.exceptions.Timeout:
        print(f'Error Timeout for {addon_products_ids}')
        return []
    except requests.exceptions.HTTPError as e:
        print(f"HTTP error for {addon_products_ids}: {str(e)}")
        return []
    except requests.exceptions.RequestException as e:
        print(f"Request error for {addon_products_ids}: {str(e)}")
        return []
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON response from GraphQL for {addon_products_ids}")
    except Exception as e:
        print(f"Error: Unexpected error during GraphQL request for {addon_products_ids}: {str(e)}")
        return []

def clean_html(raw_html):
    """
    Unescape HTML entities and remove HTML tags iin string
    Return text
    """
    if not isinstance(raw_html, str):
        return raw_html

    # Unescape HTML entities
    text = html.unescape(raw_html)

    # Remove HTML tags with regex
    clean_text = re.sub(r'<[^>]>', '', text)

    # Remove space
    clean_text = clean_text.strip()
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()
    return clean_text

def process_and_flatten_data(root_laptop_id, addon_detail_list):
    """
    Process and flatten product form GraphQL for CSV export
    Return a list of dictionaries, where each dictionary represent a product with fixed fields and dynamically added attribute fields
    """
    processed_data = []
    attribute_keys_found = set() # Store all key attributes

    for addon in addon_detail_list:
        general = addon.get('general', {})
        filterable = addon.get('filterable', {})
        # Fix prices type if None
        prices_raw = filterable.get('prices', {})
        prices = prices_raw if isinstance(prices_raw, dict) else {}

        # Handle categories
        categories = general.get('categories', [])
        category_names = "|".join([cat.get('name', '') for cat in categories if isinstance(cat, dict)]) if categories else ''
        category_ids = "|".join([str(cat.get('categoryId', '')) for cat in categories if isinstance(cat, dict)]) if categories else ''
        category_levels = "|".join([str(cat.get('level', '')) for cat in categories if isinstance(cat, dict)]) if categories else ''
        category_similars = "|".join([str(cat.get('similar', '')) for cat in categories if isinstance(cat, dict)]) if categories else ''


        product_record = {
            'root_laptop_id': root_laptop_id,
            'addon_product_id': general.get('product_id', ''),
            'addon_url_path': general.get('url_path', ''),
            'addon_product_name': general.get('name', ''),
            'addon_product_child': json.dumps(general.get('child_product', []), ensure_ascii=False, separators=(',', ':')),
            'doc_quyen': general.get('doc_quyen', ''),
            # Dynamic-attributes:

            # Categories:
            'addon_category_ids': category_ids,
            'addon_category_names': category_names,
            'addon_category_level': category_levels,
            'addon_category_similars': category_similars,

            # Filterable:
            'addon_stock_available_id': filterable.get('stock_available_id', ''),
            'addon_company_stock_id': filterable.get('company_stock_id, '),
            'addon_is_parent': filterable.get('is_parent', ''),
            'addon_price': filterable.get('price', ''),
            'addon_root_price': json.dumps(prices.get('root', {})),
            'addon_smem_price': json.dumps(prices.get('smem', {})),
            'addon_snew_price': json.dumps(prices.get('snew', {})),
            'addon_special_price': json.dumps(prices.get('special', {})),
            'addon_svip_price': json.dumps(prices.get('svip', {})),
            'addon_thumbnail': str(filterable.get('thumbnail', '')),  #
            'addon_promotion_info': html.unescape(filterable.get('promotion_information', ''))
            # Do not fetch thumbnail, promotion pack and flash_sale_types
        }
        # Handling dynamic attributes
        attributes = general.get('attributes', {})
        if isinstance(attributes, dict):
            for attr_code, attr_value in attributes.items():
                column_name = f"attr_{attr_code.lower().replace(' ', '_').replace('-', '_')}"
                if isinstance(attr_value, (list, dict)):
                    try:
                        processed_value = json.dumps(attr_value, ensure_ascii=False, separators=(',', ':'))
                    except TypeError:
                        processed_value = str(attr_value)

                elif isinstance(attr_value, bool):
                    processed_value = str(attr_value)
                elif attr_value is None:
                    processed_value = ''
                elif isinstance(attr_value, str):
                    processed_value = clean_html(attr_value)
                else:
                    processed_value = str(attr_value)

                product_record[column_name] = processed_value
                attribute_keys_found.add(column_name)
        processed_data.append(product_record)
    return processed_data, attribute_keys_found

def save_to_csv(all_data, all_field_names, filename):
    """Save everything to CSV"""
    if not all_data:
        print('No data to save')
        return

    # Append missing data
    file_exists = os.path.exists(filename)
    if file_exists:
        print(f'File {filename} exists. Appending {len(all_data)} new add-on products')
    else:
        print(f'Create new file')

    print(f'Using {len(all_field_names)} columns for writing')
    try:
        with open(filename, 'a', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=all_field_names, extrasaction='ignore', restval='')
            if not file_exists:
                writer.writeheader()
            writer.writerows(all_data)
        print(f'Successfully appended data into {filename}')
    except IOError as e:
        print(f'I/O Error in saving {filename}: {str(e)}')
    except Exception as e:
        print(f"Unwanted error in saving file CSV '{filename}': {str(e)}")

    # print(f'Saving {len(all_data)} add-on products in to {filename}')
    # print(f'Number of column will be: {len(all_field_names)}')
    # try:
    #     with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
    #         writer = csv.DictWriter(csvfile, fieldnames=all_field_names)
    #         writer.writeheader()
    #         writer.writerows(all_data)
    #     print(f'Successfully saved into {filename}')
    #
    # except IOError as e:
    #     print(f'I/O Error in saving {filename}: {str(e)}')
    # except Exception as e:
    #     print(f"Unwanted error in saving file CSV '{filename}': {str(e)}")


def main():
    """ Main function to orchestrate the process"""
    start_time = time.time()

    # # Step 01: Read root laptop id
    # root_laptop_ids = read_product_ids_from_csv(INPUT_CSV_FILE)
    # if not root_laptop_ids:
    #     print('Error in fetching root laptop ids')
    #     return

    # Handling missing data due to timeout --> continue
    root_laptop_ids_to_process = ['71560']
    print(f"Processing specific root laptop IDs: {root_laptop_ids_to_process}")



    # # Test
    # test_ids_count = 10
    # root_laptop_ids_to_process = root_laptop_ids[:test_ids_count]
    # print(f'Only test {len(root_laptop_ids_to_process)}')
    # print(f'Root laptop ids are: {root_laptop_ids_to_process}')
    # # -------------------------------

    all_processed_addons = [] # list for all processed add-on product details
    master_attribute_key = set() # set include all dynamic attribute

    # Step 02: Loop through each root laptop id
    print(f'Fetch and process add-on product for {len(root_laptop_ids_to_process)} laptops')
    for root_id in tqdm(root_laptop_ids_to_process, desc='Processing laptops'):
        # Step 03: Fetch add-on list
        recommended_addon_ids = fetching_recommendation(root_id)
        if not recommended_addon_ids:
            time.sleep(0.2)
            continue

        # Step 04: Fetch addon detail
        batch_size = 50
        detailed_addons = []
        for i in range(0, len(recommended_addon_ids), batch_size):
            batch_ids = recommended_addon_ids[i:i + batch_size]
            batch_details = fetch_addon_products_details(batch_ids)
            if batch_details:
                detailed_addons.extend(batch_details)
                # for key in batch_details:
                #     if key not in master_attribute_key:
                #         master_attribute_key.add(key)
            time.sleep(0.5)

        if not detailed_addons:
            print(f'No details for add-on product with root laptop id: {root_id}')
            continue
        # Process and flatten
        processed_batch, batch_attr_key = process_and_flatten_data(root_id, detailed_addons)
        all_processed_addons.extend(processed_batch)
        master_attribute_key.update(batch_attr_key)
        time.sleep(0.3)


    # Save to CSV file
    if not all_processed_addons:
        print('No add-on products is stored')
        return
    print(f'Successfully processed {len(all_processed_addons)} add-on products')

    # Fixed columns
    final_fieldnames = [
    'root_laptop_id',
    'addon_product_id',
    'addon_url_path',
    'addon_product_name',
    'addon_product_child',
    'addon_additional_info',
    'ads_base_image',
    'doc_quyen',
    # Dynamic-attributes:

    # Categories:
    'addon_category_ids',
    'addon_category_names',
    'addon_category_level',
    'addon_category_similars',

    # Filterable:
    'addon_stock_available_id',
    'addon_company_stock_id',
    'addon_is_parent',
    'addon_price',
    'addon_root_price',
    'addon_smem_price',
    'addon_snew_price',
    'addon_special_price',
    'addon_svip_price',
    'addon_promotion_info',
    'addon_thumbnail'
    ]
    # Dynamic attribute
    final_fieldnames.extend(sorted(list(master_attribute_key)))

    save_to_csv(all_processed_addons, final_fieldnames, OUTPUT_CSV_FILE)
    end_time = time.time()
    print(f'Finish in {end_time - start_time: .2f} seconds')


if __name__ == '__main__':
    main()