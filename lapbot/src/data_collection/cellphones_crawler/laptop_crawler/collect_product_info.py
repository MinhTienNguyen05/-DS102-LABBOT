#!/usr/bon/env python3


"""
Script to collect product data from CellphoneS API and save to csv
This script uses the GraphQL API to fetch products by category ID of laptop and save the results to a CSV file
"""
from dataclasses import field

import requests
import json
import csv
import time
import html
from tqdm import tqdm

# API endpoint
API_URL = 'https://api.cellphones.com.vn/v2/graphql/query'

# Headers
HEADERS = {
    "accept": "application/json",
    "accept-language": "en-US,en;q=0.9",
    "cache-control": "no-cache",
    "content-type": "application/json",
    "origin": "https://cellphones.com.vn",
    "pragma": "no-cache",
    "priority": "u=1, i",
    "referer": "https://cellphones.com.vn/",
    "sec-ch-ua": "\"Chromium\";v=\"134\", \"Not:A-Brand\";v=\"24\", \"Google Chrome\";v=\"134\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"macOS\"",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-site",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
}

# GraphQL query template for getting products by category id (380)
QUERY_TEMPLATE = """
    query GetProductsByCateId{
        products(
                filter: {
                    static: {
                        categories: ["380"],
                        province_id: 30,
                        stock: {
                           from: 0
                        },
                        stock_available_id: [46, 56, 152, 4920],
                       
                    },
                    dynamic: {
                        
                        
                    }
                },
                page: 1,
                size: 5000,
                sort: [{view: desc}]
            )
        {
            general{
                product_id
                name
                attributes
                sku
                doc_quyen
                manufacturer
                url_key
                url_path
                categories{
                    categoryId
                    name
                    uri
                }
                review{
                    total_count
                    average_rating
                }
            },
            filterable{
                is_installment
                stock_available_id
                company_stock_id
                filter {
                   id
                   Label
                }
                is_parent
                price
                prices
                special_price
                promotion_information
                thumbnail
                promotion_pack
                sticker
                flash_sale_types
            },
        }
    }
"""

def fetch_laptop_products():
    """Fetch laptop products with category 380 from API"""
    # Prepare payload for the request
    payload = {
        'query': QUERY_TEMPLATE,
        'variables': {}
    }

    try:
        # Send request POST to API
        response = requests.post(API_URL, headers=HEADERS, json=payload, timeout=60)

        # Check for HTTP status
        if response.status_code == 200:
            data = response.json() # Check for returned data structure from GraphQL
            if 'data' in data and 'products' in data['data'] and data['data']['products'] is not None:
                print (f"Successfully fetched {len(data['data']['products'])} products")
                return data['data']['products'] # Return list of item

            elif 'errors' in data:
                print(f"API returned errors: {data['errors']}")
                return []

            else:
                print("No 'products' data found in the response, or it is null")
                return []

        else:
            # Print error if status = 200
            print(f"Error fetching data. Status code: {response.status_code}")
            # Print error detail
            print("Response content: ", response.text)
            return []
    except requests.exceptions.RequestException as e:
        # Find error related to request (ex: timeout, connect error)
        print(f"An error occured durring the request: {str(e)}")
        return []
    except json.JSONDecodeError as e:
        # Find error if response is not valid JSON
        print(f'Error decoding JSON response: {str(e)}')
        print('Response content:', response.text)
        return []
    except Exception as e:
        # Find other unwanted error
        print(f"An unexpected error occurred {str(e)}")
        return []

def process_product_data(products):
    """Process and flatten product data for CSV export"""
    processed_data = []
    if not products:
        return processed_data # Return empty list

    print(f'Processing {len(products)} products...')
    for product in products:
        general = product.get('general', {})
        filterable = product.get('filterable', {})
        categories = general.get('categories', [])
        attributes = general.get('attributes', {})
        category_name = "|".join([cat.get('name', '') for cat in categories]) if categories else ''
        category_id =  "|". join([str(cat.get('categoryId', '')) for cat in categories]) if categories else ''
        # Change complex field in JSON
        filters = filterable.get('filter', [])
        prices_data = filterable.get('prices', {})
        prices = prices_data if isinstance(prices_data, dict) else {}
        filter_id = "|".join([str(cat.get('id', '')) for cat in filters]) if filters else ''
        filter_label = "|".join([cat.get('Label', '') for cat in filters]) if filters else ''

        product_record = {
            # general
            'product_id': general.get('product_id', ''),
            'name': general.get('name', ''),
            'additional_information': attributes.get('additional_information', ''),
            'ads_base_image': attributes.get('ads_base_image', ''),
            'bao_hanh_1_doi_1': attributes.get('bao_hanh_1_doi_', ''),
            'basic': attributes.get('basic', ''),
            'battery': attributes.get('battery', ''),
            'best_discount_price': attributes.get('best_discount_price', ''),
            'bluetooth': attributes.get('bluetooth', ''),
            'change_layout_preorder': attributes.get('change_layout_preorder', ''),
            'coupon_value': attributes.get('coupon_value', ''),
            'cpu': html.unescape(attributes.get('cpu', '')),
            'dimensions': attributes.get('dimensions', ''),
            'discount_price': attributes.get('discount_price', ''),
            'display_resolution': attributes.get('display_resolution', ''),
            'display_size': attributes.get('display_size', ''),
            'display_type': html.unescape(attributes.get('display_type', '')),
            'fe_minimum_down_payment': attributes.get('fe_minimum_down_payment', ''),
            'final_sale_price': attributes.get('final_sale_price', ''),
            'flash_sale_from': attributes.get('flash_sale_from', ''),
            'flash_sale_price': attributes.get('flash_sale_price', ''),
            'full_by_group': attributes.get('full_by_group', []),
            'hc_maximum_down_payment': attributes.get('hc_maximum_down_payment', ''),
            'hc_minimum_down_payment': attributes.get('hc_minimum_down_payment', ''),
            'hdd_sdd': attributes.get('hdd_sdd', ''),
            'image': attributes.get('image', ''),
            'image_label': attributes.get('image_label', ''),
            'included_accessories': html.unescape(attributes.get('included_accessories', '')),
            'is_imported': attributes.get('is_imported', ''),
            'key_selling_points': html.unescape(attributes.get('key_selling_points', '')),
            'laptop_cam_ung': attributes.get('laptop_cam_ung', ''),
            'laptop_camera_webcam': attributes.get('laptop_camera_webcam', ''),
            'laptop_chat_lieu': html.unescape(attributes.get('laptop_chat_lieu', '')),
            'laptop_cong_nghe_am_thanh': html.unescape(attributes.get('laptop_cong_nghe_am_thanh', '')),
            'laptop_cpu': attributes.get('laptop_cpu', ''),
            'laptop_khe_doc_the_nho':attributes.get('laptop_khe_doc_the_nho', ''),
            'laptop_loai_ram': attributes.get('laptop_loai_ram', ''),
            'laptop_nganh_hoc': html.unescape(attributes.get('laptop_nganh_hoc', '')),
            'laptop_ram': attributes.get('laptop_ram', ''),
            'laptop_resolution_filter': attributes.get('laptop_resolution_filter', ''),
            'laptop_screen_size_filter': html.unescape(attributes.get('laptop_screen_size_filter', '')),
            'laptop_so_khe_ram': html.unescape(attributes.get('laptop_so_khe_ram', '')),
            'laptop_special_feature': attributes.get('laptop_special_feature', ''),
            'laptop_tam_nen_man_hinh': html.unescape(attributes.get('laptop_tam_nen_man_hinh', '')),
            'laptop_tan_so_quet': attributes.get('laptop_tan_so_quet', ''),
            'laptop_vga_filter': attributes.get('laptop_vga_filter', ''),
            'loaisp': html.unescape(attributes.get('loaisp', '')),
            'macbook_anh_bao_mat': attributes.get('macbook_anh_bao_mat', ''),
            'macbook_anh_dong_chip': attributes.get('macbook_anh_dong_chip', ''),
            'manufacturer': attributes.get('manufacturer', ''),
            'meta_image': attributes.get('meta_image', ''),
            'meta_title': html.unescape(attributes.get('meta_title', '')),
            'mobile_accessory_type': attributes.get('mobile_accessory_type', ''),
            'msrp': attributes.get('msrp', ''),
            'msrp_display_actual_price_type': attributes.get('msrp_display_actual_price_type', ''),
            'msrp_enabled': attributes.get('msrp_enabled', ''),
            'nhu_cau_su_dung': html.unescape(attributes.get('nhu_cau_su_dung', '')),
            'o_cung_laptop': attributes.get('o_cung_laptop', ''),
            'options_container': attributes.get('options_container', ''),
            'os_version': attributes.get('os_version', ''),
            'ports_slots': html.unescape(attributes.get('ports_slots', '')),
            'product_condition': html.unescape(attributes.get('product_condition', '')),
            'product_feed_type': attributes.get('product_feed_type', ''),
            'product_state': html.unescape(attributes.get('product_state', '')),
            'product_weight': attributes.get('product_weight', ''),
            'related_name': attributes.get('related_name', ''),
            'short_description_hidden_time': attributes.get('short_description_hidden_time', ''),
            'short_description_show_time': attributes.get('short_description_show_time', ''),
            'sim_special_group': attributes.get('sim_special_group', ''),
            'small_image': attributes.get('small_image', ''),
            'small_image_label': attributes.get('small_image_label', ''),
            'smember_sms': attributes.get('smember_sms', ''),
            'status': attributes.get('status', ''),
            'tag_sforum': attributes.get('tag_sforum', ''),
            'tax_vat': attributes.get('tax_vat', ''),
            'thumbnail_label': attributes.get('thumbnail_label', ''),
            'tien_coc': attributes.get('tien_coc', ''),
            'title_price': html.unescape(attributes.get('title_price', '')),
            'use_smd_colorswatch': attributes.get('use_smd_colorswatch', ''),
            'vga': attributes.get('vga', ''),
            'warranty_information': html.unescape(attributes.get('warranty_information', '')),
            'weight': attributes.get('weight', ''),
            'wlan': attributes.get('wlan', ''),


            'sku': general.get('sku', ''),
            'url_key': general.get('url_key',''),
            'url_path': general.get('url_path', ''),
            'doc_quyen': general.get('doc_quyen', ''),
            'average_rating': general.get('review', {}).get('average_rating', ''),
            'total_count': general.get('review', {}).get('total_count', ''),
            'category_id': category_id,
            'category_name': category_name,


            # filterable
            'is_installment': filterable.get('is_installment', ''),
            'price': filterable.get('price', ''),
            'special_price': filterable.get('special_price', ''),
            'thumbnail': filterable.get('thumbnail', ''),
            'is_parent': filterable.get('is_parent', ''),
            'stock_available_id': str(filterable.get('stock_available_id', '')),
            'company_stock_id': str(filterable.get('company_stock_id', '')),
            'filter_id': filter_id,
            'filter_label': filter_label,
            # Convert price dictionaries to JSON strings to store in CSV
            'root_price': json.dumps(prices.get('root', {})),
            'smem_price': json.dumps(prices.get('smem', {})),
            'smem_student_price': json.dumps(prices.get('smem_student', {})),
            'smem_teacher_price': json.dumps(prices.get('smem_teacher', {})),
            'snew_student_price': json.dumps(prices.get('snew_student', {})),
            'snew_teacher_price': json.dumps(prices.get('snew_teacher', {})),
            'snull_student': json.dumps(prices.get('snull_student', {})),
            'snull_teacher': json.dumps(prices.get('snull_teacher', {})),
            'special_prices': json.dumps(prices.get('special', {})),
            'svip': json.dumps(prices.get('svip', {})),
            'svip_student': json.dumps(prices.get('svip_student', {})),
            'svip_teacher': json.dumps(prices.get('svip_teacher', {})),

            'promotion_information': html.unescape(filterable.get('promotion_information', '')),
            # do not take promotion_pack/ sticker/ flash_sale_types here
        }
        processed_data.append(product_record)
    print('Processing complete')
    return processed_data

def save_to_csv(data, filename):
    """Save processed data to CSV file"""
    if not data:
        print('No data to save to CSV file')
        return False
    fieldnames = data[0].keys() # column name as first record
    print(f'Save data to {filename}')
    try:
        with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile: # utf-8-sig for exact Vietnamese text
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader() # Headers
            writer.writerows(data) # Rows of data
        print(f'Successfully saved {len(data)} records to {filename}')
        return True

    except IOError as e:
        print(f'Error saving to CSV (I/O Error): {str(e)}')
        return False

    except Exception as e:
        print(f'Error in CSV saving: {str(e)}')
        return False

def main():
    """Main fuction to collect laptop products and save to CSV"""
    # Get data from API
    raw_laptop_products = fetch_laptop_products()

    # Check if data exist
    if raw_laptop_products:
        processed_laptop_data = process_product_data(raw_laptop_products)

        # Debug
        #if processed_laptop_data:  # Chỉ kiểm tra nếu list không rỗng
        #   print(f"DEBUG: Type of processed_laptop_data: {type(processed_laptop_data)}")
        #   print(f"DEBUG: Type of first element: {type(processed_laptop_data[0])}")
        #   print(f"DEBUG: First element content: {processed_laptop_data[0]}")

        # Save data to CSV file
        if processed_laptop_data:
            csv_filename = 'cellphones_laptops_category_380.csv'
            save_to_csv(processed_laptop_data, csv_filename)
        else:
            print('No products were processed')

    else:
        print('Fail to fetch product data from API')


if __name__ == '__main__':
    start_time = time.time()
    main()
    end_time = time.time()
    print(f'Script finished in {end_time - start_time:.2f} seconds')
