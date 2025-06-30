#!/usr/bin/env python3
import time

import requests
import csv
import json
from tqdm import tqdm


""" Script to collect questions and answers from CellphoneS API and save to CSV"""

# API endpoint
API_URL = 'https://api.cellphones.com.vn/graphql-customer/graphql/query'

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
# GraphQL query template for getting comment with category ID (laptop) = 380
# This API is PAGINATION
QUERY_TEMPLATE = """
    query COMMENTS($currentPage: Int!){
          comment(
              type: "page", 
              pageUrl: "https://cellphones.com.vn/laptop.html"
              productId: 0, 
              currentPage: $currentPage
                             
          ) {
            total
            matches {
              id
              content
              page_name
              is_shown
              is_admin
              is_pinned
              sent_from
              created_at
              children
              product_id
              page_url
              customer {
                id
                fullname
              }
            }
          }
        }
"""

def fetch_all_comments():
    """Fetch all comments using pagination"""
    all_comments = []
    current_page = 1
    previous_matches_data = None
    print('Fetching comments from https://cellphones.com.vn/laptop.html')
    while True: # run until matches return None
        print(f'Fetching page {current_page}')

        payload = {
            'query': QUERY_TEMPLATE,
            'variables': {'currentPage': current_page}
        }

        try:
            response = requests.post(API_URL, headers=HEADERS, json=payload, timeout=30)
            response.raise_for_status() # Check HTTP errors
            data = response.json()
            # Check error in returned response
            if 'errors' in data:
                print(f'GraphQL API returned errors on page {current_page}: {data["errors"]}')
                break
            response_data = data.get('data') # Fetch data firstly

            if response_data: # Secondly fetch comment in data
                comment_data = response_data.get('comment')
            else:
                print(f'Response from page {current_page} does not contain data')
                comment_data = None

            if not comment_data:
                print(f'No "comment" data found in response on page {current_page}. Stop!!!')
                break

            matches = comment_data.get('matches')

            if not matches: # Check if there are any comment
                print(f'Page {current_page} returned no comment. Reached the end.')
                break # Exit while loop

            if previous_matches_data is not None and matches == previous_matches_data:
                print(f'Data on page {current_page} is identical to the previous page ({current_page - 1}). Stop !!!')
                break

            print(f'Page {current_page}: Found {len(matches)} comments')
            all_comments.extend(matches)
            current_page += 1
            previous_matches_data = matches
            time.sleep(0.5)

        # Error during request process
        except requests.exceptions.Timeout: # Timeout
            print(f'Request timed out on page {current_page}')
            # Do not increase current_page if timeout occur
            continue

        except requests.exceptions.HTTPError as http_err: # Error with HTTP
            print(f'HTTP error occurred on page {current_page}: {http_err}')
            print(f'Response status code: {response.status_code}')
            print(f'Response text: {response.text[:500]}')
            break

        except requests.exceptions.RequestException as req_err: # Request error
            print(f'Network or request error on page {current_page}: {req_err}')
            break

        except json.JSONDecodeError: # invalid JSON
            print(f'Failed to decode JSON response from page {current_page}')
            print(f'Response text: {response.text[:500]}')
            break

        except Exception as e: # Other unexpected errors
            print(f'Other errors occur on page {current_page}: {e}')
            import traceback
            traceback.print_exc()
            break

    print(f'Finished fetching. Collected {len(all_comments)} comments')
    return all_comments

def process_comment_data(comments):
    """Process and flatten comment data for CSV export"""
    processed_data = []
    if not comments:
        return processed_data

    print(f'Processing {len(comments)} comments')
    delimiter = " ||| "
    # tqdm for large amount element in loop
    for comment in tqdm(comments, desc='Processing comments'):
        customer_info = comment.get('customer') if comment.get('customer') else {}
        # Just take some features in columns
        # answer_list = comment.get('children', '') children is a list of dictionary -> cannot have get() functiom
        children_list = comment.get('children', [])
        child_contents = []
        child_created_ats = []
        child_answerer_names = []
        child_answerer_ids = []
        child_is_admin_flags = []

        if isinstance(children_list, list): # Make sure children_list is a list
            for child in children_list:
                if isinstance(child, dict): # Make sure child of children is a dictionary
                    child_contents.append(child.get('content', ''))
                    child_created_ats.append(child.get('created_at', ''))
                    child_is_admin_flags.append(str(child.get('is_admin', '0')))
                    child_answerer_info = child.get('customer', {})
                    if isinstance(child_answerer_info, dict):
                        child_answerer_names.append(child_answerer_info.get('fullname', 'N/A'))
                        child_answerer_ids.append(str(child_answerer_info.get('id', '')))
                    else: # if children_info is not a dict
                        child_answerer_names.append('N/A')
                        child_answerer_ids.append('')
                else: # if child in children is not a dict
                    print(f"Warning: Found non-dict item in children list for comment ID {comment.get('id')}")
        joined_child_contents = delimiter.join(child_contents)
        joined_child_created_ats = delimiter.join(child_created_ats)
        joined_child_answerer_names = delimiter.join(child_answerer_names)
        joined_child_answerer_ids = delimiter.join(child_answerer_ids)
        joined_child_is_admin_flags = delimiter.join(child_is_admin_flags)

        comment_record = {
            'comment_id': comment.get('id', ''),
            # Comment id might be the same as customer_id : I don't know how to figure out this
            'question': comment.get('content', ''),
            'page_name': comment.get('page_name', ''),
            'question_sent_from': comment.get('sent_from', ''),
            'question_created_at': comment.get('created_at', ''),
            'product_id': comment.get('product_id', ''),
            # product_id here gonna be = 0 because customer are confused which laptop to buy
            'page_url': comment.get('page_url', ''),
            'customer_id': customer_info.get('id', ''),
            'customer_fullname': customer_info.get('fullname', ''),
            'answer_contents': joined_child_contents,

            'answer_created_at': joined_child_created_ats,
            'answerer_names': joined_child_answerer_names,
            'answerer_ids': joined_child_answerer_ids,
            'is_admin': joined_child_is_admin_flags

        }
        processed_data.append(comment_record)

    print('Processing complete')
    return processed_data

def save_to_csv(data, filename):
    """Save processed data to CSV file"""
    if not data:
        print('No data to save to CSV')
        return False

    if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
        fieldnames = list(data[0].keys())

    else:
        print('Data format is incorrect for CSV saving')
        return False
    print(f'Saving {len(data)} records to {filename}')
    try:
        with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
        print(f'Successfully saved data to {filename}')
        return True

    except IOError as e:
        print(f'Error saving to CSV (I/O Error): {str(e)}')
        return False
    except Exception as e:
        print(f'Unwanted error: {str(e)}')
        return False

def main():
    """Main function to collect comments and save too CSV"""

    start_time = time.time()

    # Step 01: Fetch all the comments
    raw_comments = fetch_all_comments()

    # Step 02: Process data
    if raw_comments:
        processed_comments =  process_comment_data(raw_comments)
        if processed_comments:
            csv_filename = 'cellphones_laptops_category_380_question.csv'
            save_to_csv(processed_comments, csv_filename)
        else:
            print('Error in processing comment procedure')
    else:
        print('Error in fetching comments from category page')

    end_time = time.time()
    print(f'Script finished in {end_time - start_time:.2f} seconds')

if __name__ == '__main__':
    main()

