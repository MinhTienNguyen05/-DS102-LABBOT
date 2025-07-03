import pandas as pd
import time
import os
import logging
import logging.config
from tqdm import tqdm
import concurrent.futures
import threading

from config import (
    INPUT_CSV_FILE,
    OUTPUT_DIR,
    OUTPUT_CSV_FILE,
    QUESTION_COLUMN_NAME,
    API_CALL_DELAY_SECONDS,
    LOGGING_CONFIG,
    INTENT_DEFINITIONS
)
from processer import process_single_question

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)

MAX_CONCURRENT_WORKERS = 1
MAX_REQUESTS_PER_MIN = 15
SECONDS_BETWEEN_REQUESTS = 60 / MAX_REQUESTS_PER_MIN
rate_limiter = threading.Semaphore(MAX_REQUESTS_PER_MIN)


def normalize_question(q):
    return str(q).strip().lower()


def append_to_output_file(result_dict):
    output_df_single = pd.DataFrame([result_dict])
    write_header = not os.path.exists(OUTPUT_CSV_FILE)
    output_df_single.to_csv(
        OUTPUT_CSV_FILE,
        mode='a',
        index=False,
        encoding='utf-8-sig',
        header=write_header
    )


def process_single_question_with_limit(question):
    with rate_limiter:
        result = process_single_question(question)
        time.sleep(SECONDS_BETWEEN_REQUESTS)
        return result


def get_intent_name(id_list):
    intent_id_to_name = {v['id']: k for k, v in INTENT_DEFINITIONS.items()}
    if isinstance(id_list, list):
        return [intent_id_to_name.get(id_val, []) for id_val in id_list]
    return []


def load_already_processed_questions():
    processed = {}
    if os.path.exists(OUTPUT_CSV_FILE):
        try:
            prev_df = pd.read_csv(OUTPUT_CSV_FILE)
            for _, row in prev_df.iterrows():
                q = normalize_question(row.get("original_question", ""))
                if q:
                    processed[q] = row.to_dict()
            logger.info(f"Loaded {len(processed)} already processed questions from {OUTPUT_CSV_FILE}")
        except Exception as e:
            logger.warning(f"Could not read existing output file: {e}")
    return processed


def main():
    logger.info("Start processing!")

    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        logger.info(f"Created {OUTPUT_DIR}")

    try:
        df = pd.read_csv(INPUT_CSV_FILE)
        logger.info(f"Loaded {len(df)} questions from {INPUT_CSV_FILE}")
    except FileNotFoundError:
        logger.error(f"Could not find {INPUT_CSV_FILE}")
        return
    except Exception as e:
        logger.error(f"Error loading input file: {e}")
        return

    if QUESTION_COLUMN_NAME not in df.columns:
        logger.error(f"Missing column: {QUESTION_COLUMN_NAME} in input file")
        return

    already_processed_map = load_already_processed_questions()

    all_questions = df[QUESTION_COLUMN_NAME].fillna('').astype(str).tolist()
    questions_to_process = [
        q for q in all_questions
        if normalize_question(q) not in already_processed_map and q.strip()
    ]

    logger.info(f"Total: {len(all_questions)} | To process: {len(questions_to_process)}")

    error_count = 0
    processed_count = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_CONCURRENT_WORKERS) as executor:
        future_to_question = {
            executor.submit(process_single_question_with_limit, question): question
            for question in questions_to_process
        }

        for future in tqdm(concurrent.futures.as_completed(future_to_question), total=len(future_to_question), desc='Processing questions'):
            original_question = future_to_question[future]
            try:
                processed_data = future.result()
                if processed_data:
                    processed_data['original_question'] = original_question
                    processed_data['assigned_intent_name'] = get_intent_name(processed_data.get('assigned_intent_id', []))
                    append_to_output_file(processed_data)
                else:
                    logger.warning(f"No result for: {original_question[:50]}... Appending fallback")
                    fallback = {
                        "original_question": original_question,
                        "keep_question": 0,
                        "corrected_question": "ERROR_PROCESSING_RETURNED_NONE",
                        "assigned_intent_id": [INTENT_DEFINITIONS['other']['id']],
                        "assigned_intent_name": ["other"]
                    }
                    append_to_output_file(fallback)
                    error_count += 1
            except Exception as e:
                logger.error(f"Error during future.result() for question '{original_question[:50]}...': {e}", exc_info=True)
                fallback = {
                    "original_question": original_question,
                    "keep_question": 0,
                    "corrected_question": "ERROR_PROCESSING_EXCEPTION",
                    "assigned_intent_id": [INTENT_DEFINITIONS['other']['id']],
                    "assigned_intent_name": ["other"]
                }
                append_to_output_file(fallback)
                error_count += 1
            finally:
                processed_count += 1

    logger.info(f"Done. Processed: {processed_count} | Errors: {error_count}")


if __name__ == "__main__":
    main()