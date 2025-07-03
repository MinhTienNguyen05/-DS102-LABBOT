#!/usr/bin/env python3
import pandas as pd
from together import Together
import time
import os
import requests
import re
import concurrent.futures
from tqdm import tqdm
from dotenv import load_dotenv
import logging


# load_dotenv()
from dotenv import load_dotenv
from pathlib import Path
import os

env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path=env_path)

print("DEBUG - TOGETHER_API_KEY:", os.environ.get("TOGETHER_API_KEY"))


TOGETHER_API_KEY = os.environ.get("TOGETHER_API_KEY")
if not TOGETHER_API_KEY:
    import logging
    logging.basicConfig(level=logging.INFO, 
                        format='%(asctime)s - %(levelname)s - %(threadName)s - %(message)s',
                        handlers=[logging.FileHandler('processing_log.txt'), logging.StreamHandler()])
    logging.error("Could not find TOGETHER_API_KEY")
    exit()

# Kiểm tra thử xem có lấy được chưa (có thể xóa sau)
print("TOGETHER_API_KEY:", TOGETHER_API_KEY[:6] + "..." + TOGETHER_API_KEY[-4:])


# ---LOGGING
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(threadName)s - %(message)s',
                    handlers=[logging.FileHandler('processing_log.txt'),logging.StreamHandler()])



TOGETHER_API_KEY = os.environ.get("TOGETHER_API_KEY")
if not TOGETHER_API_KEY:
    logging.error("Could not find TOGETHER_API_KEY")
    exit()
    
client = Together(api_key=TOGETHER_API_KEY)
MODEL_NAME = "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free"
INPUT_CSV_PATH = "cellphones_laptops_category_380_question.csv"
OUTPUT_CSV_PATH = "processed_questions.csv"
QUESTION_COLUMN_NAME = "question"

MAX_WORKERS = 10 # Number of worker for ThreadPoolExecutor
API_RETRY_DELAY = 5 # Time between retry if API error
API_RATELIMIT_DELAY_BASE = 20 # Time foe RateLimitError

INTENT_DEFINITION_TEXT = """
Mã intent: 0
Tên: recommend_budget
Mô tả/Từ khóa: Gợi ý theo ngân sách, tầm giá, ngân sách, bao nhiêu tiền, dưới, khoảng, triệu, giá bao nhiêu, tài chính
---
Mã intent: 1
Tên: recommend_use_case
Mô tả/Từ khóa: Gợi ý theo nhu cầu sử dụng, học tập, đồ họa, chơi game, lập trình, thiết kế, chỉnh sửa video, công nghệ thông tin, marketing, kế toán, kỹ thuật, dựng phim, autocad, solidworks, photoshop, adobe, canva, truyền thông, văn phòng, cơ bản, giải trí
---
Mã intent: 2
Tên: product_status
Mô tả/Từ khóa: Tình trạng hàng, còn hàng, chi nhánh, cửa hàng, khu vực, địa chỉ, Hà Nội, TPHCM, Đà Nẵng, Cần Thơ, Bình Dương, màu sắc, màu xám, màu bạc, màu đen, màu vàng, sẵn hàng, trưng bày
---
Mã intent: 3
Tên: promotion_discount_gift
Mô tả/Từ khóa: Khuyến mãi, giảm giá, quà tặng, tặng kèm, balo, chuột, bàn phím, RAM, office bản quyền, voucher, ưu đãi, sinh viên, S-student, thanh toán VNPay, flash sale, hot sale, SVIP, phiếu mua hàng
---
Mã intent: 4
Tên: finance_installment
Mô tả/Từ khóa: Trả góp, góp, trả trước, lãi suất, 0%, tháng, công ty tài chính, Shinhan Finance, HomeCredit, Fundin, thẻ tín dụng, Visa, Mastercard, thanh toán thẻ, điều kiện trả góp, giấy tờ, phụ huynh, xác nhận
---
Mã intent: 5
Tên: hardware_upgrade
Mô tả/Từ khóa: Nâng cấp, RAM, SSD, ổ cứng, HDD, dung lượng, 16GB, 32GB, 1TB, khe cắm, thay RAM, lắp thêm, giá nâng cấp, tản nhiệt, quạt
---
Mã intent: 6
Tên: tech_detail
Mô tả/Từ khóa: Thông số kỹ thuật, chip, CPU, GPU, card rời, card tích hợp, RAM, SSD, màn hình, tần số quét, Hz, sRGB, độ sáng, nit, bàn phím, đèn bàn phím, RGB, độ sáng bàn phím, đổi màu, tùy chỉnh đèn, đèn RGB, cổng, USB, Type-C, Thunderbolt, DisplayPort, độ phân giải, 2K, 4K, pin, cell, vỏ nhựa, vỏ kim loại, trọng lượng, M1, M2, M3, M4
---
Mã intent: 7
Tên: warranty_exchange_policy
Mô tả/Từ khóa: Bảo hành, đổi trả, lỗi, 1 đổi 1, sửa chữa, bản lề, màn hình, loa, pin, thẩm định, bảo hành quốc tế, mất giấy bảo hành, vệ sinh máy, quyền lợi bảo hành
---
Mã intent: 8
Tên: trade_in_estimate
Mô tả/Từ khóa: Thu cũ, đổi mới, lên đời, bù bao nhiêu, giá thu, ngoại hình, tình trạng, pin, sạc lần, vết xước, trợ giá, MacBook, Dell, Asus, MSI, Lenovo
---
Mã intent: 9
Tên: compare_models
Mô tả/Từ khóa: So sánh, máy nào tốt hơn, khác nhau, MacBook, Dell, Asus, Lenovo, MSI, Acer, VivoBook, ThinkPad, TUF, Nitro, hiệu năng, cấu hình
---
Mã intent: 10
Tên: performance
Mô tả/Từ khóa: Hiệu năng thực tế, mượt, lag, FPS, setting, max setting, Valorant, Liên Minh, Genshin, FO4, GTA V, Elden Ring, dựng phim, chỉnh ảnh, Photoshop, Premiere, After Effects, AutoCAD, SolidWorks, tản nhiệt, quạt kêu, pin tụt, hiệu suất, xử lý, đa nhiệm
---
Mã intent: 11
Tên: product_info
Mô tả/Từ khóa: Thông tin sản phẩm, sản xuất, ra mắt, năm nào, xuất xứ, hàng mới, nguyên seal, nội địa, xách tay, bản quyền, Windows, Office, Microsoft, hệ điều hành, macOS, Linux, Windows 10, Windows 11, cài đặt, cập nhật, phiên bản
---
Mã intent: 12
Tên: other_general
Mô tả/Từ khóa: Câu hỏi khác, tư vấn, nên mua, hiện tại, đặt hàng, hủy đơn, giao hàng, ship, giữ hàng, trải nghiệm, liên hệ, nhân viên, dịch vụ, khiếu nại, hệ thống, cửa hàng gần nhất
"""
INTENT_MAP = {
    "0": "recommend_budget", 
    "1": "recommend_use_case", 
    "2": "product_status",
    "3": "promotion_discount_gift", 
    "4": "finance_installment", 
    "5": "hardware_upgrade",
    "6": "tech_detail", 
    "7": "warranty_exchange_policy", 
    "8": "trade_in_estimate",
    "9": "compare_models", 
    "10": "performance", 
    "11": "product_info",
    "12": "other_general"
}

def call_api(prompt_text, task_name="API Call", max_retries=3):
    """Function for calling API with retry and rate limit handling"""
    current_delay = API_RETRY_DELAY
    for attempt in range(max_retries):
        try:
            logging.info(f'{task_name} - Attempt: {attempt + 1}/{max_retries} for {prompt_text[:100]}')
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[{"role": "user", "content": prompt_text}],
                temperature=0.2,
                timeout=60,
            )

            if response.choices and len(response.choices) > 0:
                content = response.choices[0].message.content.strip()
                logging.info(f"{task_name}: - succeeded. Response: {content[:100]}")
                return content
            else:
                logging.warning(f"{task_name} - Response with no choices or empty choices. Response: {response}")
                raise ValueError("Invalid response from API")

        except requests.exceptions.HTTPError as e:
            if e.response is not None and e.response.status_code == 429:
                wait_time = API_RATELIMIT_DELAY_BASE * (2 ** attempt)
                logging.warning(f"{task_name}: Rate limit error. Waiting {wait_time}s (Attempt {attempt+1}/{max_retries})")
                time.sleep(wait_time)
            else:
                raise  # unknown HTTP error, re-raise

        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as conn_err:
            logging.warning(f"{task_name}: Connection/timeout error: {conn_err}. Wait {current_delay}s (Attempt {attempt+1}/{max_retries})")
            time.sleep(current_delay)
            current_delay *= 1.5

        except Exception as e:
            logging.warning(f"{task_name}: General error: {e}. Retry after {current_delay}s. (Attempt {attempt+1}/{max_retries})")
            time.sleep(current_delay)

    logging.error(f'{task_name}: Failed after {max_retries} attempts. Prompt: {prompt_text[:70]}')
    return None


def correct_question_and_extract_errors(question_text):
    """Correct the spelling error in user questions and extract errors"""
    prompt = f"""Phân tích câu tiếng Việt sau: "{question_text}
    Hãy thực hiện các yêu cầu sau:
    1. Liệt kê các lỗi chính tả hoặc lỗi ngữ pháp tìm thấy. Nếu không có lỗi, ghi "None"
    2. Cung cấp câu đã được sửa hoàn chỉnh
    
    Định dạng output mong muốn:
    Lỗi: [danh sách lỗi hoặc "None"]
    Câu sửa: "câu đã được sửa hoàn chỉnh" (theo kiểu string bình thường)
    """
    
    response_text = call_api(prompt, task_name="Correct")
    errors_found = "Lỗi API khi sửa câu"
    corrected_q = question_text # default
    
    if response_text:
        logging.debug(f'Response sửa lỗi raw:')
        error_match = re.search(r"Lỗi:\s*(.+?)(?=\nCâu sửa:|\Z)", response_text, re.DOTALL | re.IGNORECASE)
        corrected_match = re.search(r"Câu sửa:\s*(.*)", response_text, re.DOTALL | re.IGNORECASE)
        
        if error_match:
            errors_found = error_match.group(1).strip()
            if not error_match: 
                errors_found = "None"
        if corrected_match:
            corrected_q = corrected_match.group(1).strip()
        else: 
            # Nếu không tìm thấy "Câu sửa:", có thể LLM chỉ trả về câu đã sửa
            # hoặc định dạng không đúng
            if "Lỗi:" not in response_text and "Câu sửa:" not in response_text and len(response_text) > 0:
                corrected_q = response_text
                errors_found = "Không có thông tin (model chỉ trả về câu sửa)"
            else:
                corrected_q = response_text # Giữ câu gốc nếu không parse được
                if errors_found == "Không parse được lỗi": # Chỉ ghi đè nếu chưa có lỗi cụ thể hơn
                    errors_found = "Không parse được câu sửa"
        logging.info(f'Original question: "{question_text}" -> Errors: "{errors_found}, Corrected: "{corrected_q}""')
        return errors_found, corrected_q
    
    logging.warning(f'Do not recieve response when correcting error forr "{question_text}"')
    return errors_found, corrected_q
    
def classify_intent(question_text):
    """ Classify the intent of user questions"""
    prompt = f"""Dựa vào danh sách các intent sau đây, hãy xác định MÃ INTENT phù hợp nhất cho câu hỏi của người dùng.
    Chỉ trả về MÃ INTENT (ví dụ: 0, 1, 2, 3, ....). Nếu không chắc chắn hoặc trong câu không có các từ khoá đã được xác định thì hãy chọn 12 (other_general)
    
    Danh sách các Intent:
    {INTENT_DEFINITION_TEXT}
    
    Câu hỏi của người dùng: {question_text}
    Mã Intent: 
    """
    response_text = call_api(prompt)
    if response_text:
        logging.debug(f"Response gán intent raw: {response_text}")
        # Try to extract froom LLMs response due to extra unwanted text
        match = re.search(r'\b(\d+)\b', response_text)
        if match:
            intent_code = match.group(1)
            if intent_code in INTENT_MAP: # Cheack if intent_code is valid
                intent_name = INTENT_MAP.get(intent_code, "unknown_intent_name")
                logging.info(f"'{question_text[:50]}...' -> Intent: {intent_code} ({intent_name})")
                return intent_code, intent_name
            else:
                logging.warning(f"Intent code '{intent_code}' is not valid from response: '{response_text}'. Label as '12'.")
        
        else:
            logging.warning(f"Could not extract intent code from :'{response_text}'. Label as '12'")
            return "12", INTENT_MAP["12"]
    logging.warning(f"Could not recieve response for:'{response_text}'. Label as '12'")    
    return "12", INTENT_MAP["12"] #Default and API error

def process_single_row(args):
    """
    Handling a row (a user question)
    args is a tuple: (index, original_question, pbar_instance_optional)
    """
    index, original_question = args
    logging.info(f'Process {index}: {original_question[:70]}')
    #1. Correct and extarct errosrs
    errors, corrected_q = correct_question_and_extract_errors(original_question)
    
    #2. Label intent
    intent_code, intent_name = classify_intent(corrected_q)
    logging.info(f'Successfully processed {index}. Errors: {errors}, Correct: {corrected_q}, Intent: {intent_code} ({intent_name})')
    return index, errors, corrected_q, intent_code, intent_name
    
def main():
    print("Main function is running")
    logging.info('Start: ')
    if not os.environ.get("TOGETHER_API_KEY"):
        logging.error("Error: envirronment variable")
        return
    try:
        df = pd.read_csv(INPUT_CSV_PATH)    
        logging.info(f"Read {len(df)} rows from {INPUT_CSV_PATH}")
    except FileNotFoundError:
        logging.error(f"Error: Could not find {INPUT_CSV_PATH}")
        return
    
    if QUESTION_COLUMN_NAME not in df.columns:
        logging.error(f"Error: {QUESTION_COLUMN_NAME} is not in {INPUT_CSV_PATH}")
        return
    
    df["errors_found"] = ""
    df["corrected_question"] = ""
    df["intent_code"] = ""
    df["intent_name"] = ""
    
    tasks = []
    
    #Testing
    df_subset = df.head(10).copy()
    for index, row in df_subset.iterrows():
        original_question = str(row[QUESTION_COLUMN_NAME])
        if pd.isna(original_question) or original_question.strip() == "":
            # Handling empty question
            logging.warning(f"Dòng {index}: Câu hỏi gốc rỗng hoặc chỉ chứa khoảng trắng. Bỏ qua.")
            df.loc[index, "errors_found"] = "Câu hỏi gốc rỗng"
            df.loc[index, "corrected_question"] = ""
            df.loc[index, "intent_code"] = "N/A"
            df.loc[index, "intent_name"] = "N/A"
            continue
        tasks.append((index, original_question))
    if not tasks:
        logging.info('No valid question for processing')
        df_subset.to_csv(OUTPUT_CSV_PATH, index=False, encoding='utf-8-sig')
        return
    
    logging.info(f'Ready to process {len(tasks)} qith {MAX_WORKERS} concurrently')
    processed_count = 0
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_index = {executor.submit(process_single_row, task):task[0] for task in tasks}
        for future in tqdm(concurrent.futures.as_completed(future_to_index), total=len(tasks), desc="Processing question"):
            original_index = future_to_index[future]
            try:
                idx, errors, corrected_q, intent_code, intent_name = future.result()
                # 1. Correct and extract errors 
                df_subset.loc[idx,"errors_found"] = errors
                df_subset.loc[idx, "corrected_question"] = corrected_q
                # 2. Label intent (using corrected sentences)
                df_subset.loc[idx, "intent_code"] = intent_code
                df_subset.loc[idx, "intent_name"] = intent_name
                processed_count += 1

            except Exception as exc:
                logging.error(f'Error in processing row {original_index}: {exc}', exc_info=True)
                df_subset.loc[original_index, "errors_found"] = f'Error processing thread: {exc}'
                df_subset.loc[original_index, "corrected_question"] = df.loc[original_index, QUESTION_COLUMN_NAME] # Take the original
                df_subset.loc[original_index, "intent_code"] = "ERROR"
                df_subset.loc[original_index, "intent_name"] = "ERROR_THREAD"
            processed_count += 1
            if processed_count > 0 and processed_count % (MAX_WORKERS * 5) == 0: #Save after 50 rows
                logging.info(f"Processed {len(df_subset[df_subset['intent_code'] != ''])}rows. Saved")
                #df.update(df_subset) #update original df if using df_subset
                #df.loc[df_subset.index] = df_subset
                df.to_csv(OUTPUT_CSV_PATH, index = False, encoding='utf-8-sig')
                logging.info(f'Save to {OUTPUT_CSV_PATH}')
            
    df.update(df_subset)#update original df if using df_subset
    df.to_csv(OUTPUT_CSV_PATH, index=False, encoding='utf-8-sig')
    print(f'Completed saving to {OUTPUT_CSV_PATH}')
 
if __name__ == "__main__":
    print("here")
    main()