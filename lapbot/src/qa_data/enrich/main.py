import pandas as pd
import time
import os
import logging
import logging.config
from tqdm import tqdm
import concurrent.futures
import threading
import argparse

from config import (
    INPUT_CSV_FILE, OUTPUT_DIR , OUTPUT_CSV_FILE, QUESTION_COLUMN_NAME, API_CALL_DELAY_SECONDS, LOGGING_CONFIG, INTENT_DEFINITIONS, PROCESSED_QUESTIONS_TRACKING_FILE, NUM_QUESTIONS_TO_GENERATE, LAPTOP_INFO_FILT_PATH, GENERATED_QA_OUTPUT_FILE
)

from label_processor import process_single_question
from question_generator import generate_quest_in_batches

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)

MAX_CONCURRENT_WORKERS = 2


MAX_REQUESTS_PER_MIN = 15
SECONDS_BETWEEN_REQUESTS = 60 / MAX_REQUESTS_PER_MIN
rate_limiter = threading.Semaphore(MAX_REQUESTS_PER_MIN)

def load_processed_questions(tracking_file_path:str, original_question_col: str) -> set:
    """Load list of processed questions from tracking file 

    Args:
        tracking_file_path (str): _description_
        original_question_col (str): _description_

    Returns:
        set: return a set of original, processed questions
    """
    processed_set = set()
    if os.path.exists(tracking_file_path):
        try:
            # Only read original question col
            df_processed = pd.read_csv(tracking_file_path, usecols=[original_question_col])
            processed_set = set(df_processed[original_question_col]. astype(str).tolist())
            logger.info(f"Loaded {len(processed_set)} already processed questions from {tracking_file_path}")
        except FileNotFoundError:
            logger.error(f"Could not find tracking file: {tracking_file_path}")
        except ValueError as e:
            logger.error(f"Column {original_question_col} is not found in tracking file {tracking_file_path}")
        except Exception as e:
            logger.error(f"Error loading processed questions from {tracking_file_path}: {e}")
    return processed_set



def append_results_to_csv(results_list: list, output_file_path: str, is_first_batch: bool, is_generation_mode = False):
    """
    Concat result into final csv file. If is_first_batch, write header
    is_generation_mode: True nếu đang ghi dữ liệu câu hỏi được sinh ra.
    
    """
    df_to_append = pd.DataFrame(results_list)
    
    if is_generation_mode:
        cols_to_save = ['question'] + [k for k in INTENT_DEFINITIONS.keys() if k != 'other']
        df_to_append = df_to_append[[col for col in cols_to_save if col in df_to_append.columns]]
    else:
        if not df_to_append.empty:
            intent_id_to_name = {v['id']: k for k, v in INTENT_DEFINITIONS.items()}
            def get_intent_names(ids_list):
                if isinstance(ids_list, list):
                    return [intent_id_to_name.get(id_val, "") for id_val in ids_list]
                return []
            df_to_append['assigned_intent_name'] = df_to_append['assigned_intent_id'].apply(get_intent_names)
            try:
                if is_first_batch or not os.path.exists(output_file_path):
                    df_to_append.to_csv(output_file_path, index=False, encoding='utf-8-sig', mode='w', header=True)
                    logger.info(f"Written initial batch of {len(df_to_append)} results to {output_file_path}")
                else:
                    df_to_append.to_csv(output_file_path, index=False, encoding='utf-8-sig', mode='a', header=False)
                    logger.info(f"Appended {len(df_to_append)} results to {output_file_path}")
            except Exception as e:
                logger.error(f"Error appending/writing results to CSV {output_file_path}: {e}", exc_info=True)
            
def process_single_question_with_limit(question):
    with rate_limiter:
        result = process_single_question(question)
        time.sleep(SECONDS_BETWEEN_REQUESTS)  # để tránh vượt RPM
        return result

def run_to_process():
    logger.info(f"Start processing!")
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        logger.info(f"Created {OUTPUT_DIR}")
        
    # Load data
    try:
        df = pd.read_csv(INPUT_CSV_FILE)
        logger.info(f"Sucecessfully loaded {len(df)} questions from {INPUT_CSV_FILE} ")
    except FileNotFoundError as e:
        logger.error(f"Could not find {INPUT_CSV_FILE}")
        return
    except Exception as e:
        logger.error(f"Error loading input file: {e}")
        return
    
    if QUESTION_COLUMN_NAME not in df.columns:
        logger.error(f"Could not find {QUESTION_COLUMN_NAME} in {INPUT_CSV_FILE}")
        return 
    
    already_processed_questions = load_processed_questions(PROCESSED_QUESTIONS_TRACKING_FILE, 'original_question')
    
    all_input_questions = df[QUESTION_COLUMN_NAME].fillna('').astype(str).tolist()
    
    questions_to_process = [] # list of unprocessed question
    for q_orig in all_input_questions:
        if q_orig.strip() and q_orig not in already_processed_questions:
            questions_to_process.append(q_orig)
        elif not q_orig.strip():
            pass # donnot submit empty quest but still kept in output
    if not questions_to_process:
        logger.info("All questions from input file have already been processed according to the tracking file. Exiting.")
        return
    
    logger.info(f"Found {len(questions_to_process)} new questions to process out of {len(all_input_questions)}")
   
    error_count = 0
    processed_count = 0
    future_result_map = {}
    is_first = not os.path.exists(PROCESSED_QUESTIONS_TRACKING_FILE)
    
    
    # Concurrent
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_CONCURRENT_WORKERS) as executor:
        future_to_question_map = {
            executor.submit(process_single_question_with_limit, question): question 
            for question in questions_to_process if question.strip()
        }
        # sequence is not important so appending result after future is finished
        logger.info(f"Submitting {len(future_to_question_map)} non-wmpty questions to {MAX_CONCURRENT_WORKERS} workers")
        
        temp_batch_results = [] # Save with batches
        BATCH_SIZE_TO_WRITE = 20
        
        # Use tqdm to see the process of future
        # as_completed will yield futures when they are finished (not in order)
        for future in tqdm(concurrent.futures.as_completed(future_to_question_map), total=len(future_to_question_map), desc = 'Processing questions'):
            original_question = future_to_question_map[future]
            error_data= ({
                        "original_question": original_question,
                        "keep_question": 0,
                        "corrected_question": "ERROR_PROCESSING_RETURNED_NONE",
                        "assigned_intent_id": [INTENT_DEFINITIONS['other']['id']]
                    })
            try:
                processed_data = future.result()
                if processed_data:
                    future_result_map[original_question] = processed_data
                    temp_batch_results.append(processed_data)
                
                else:
                    logger.warning(f"Processing return None for: {original_question[:50]}... Append default value")
                    future_result_map[original_question] = error_data
                    temp_batch_results.append(error_data)
                    error_count += 1
            except Exception as e:
                logger.error(f"Question: {original_question[:50]}... generated exception during future.result(): {e}", exc_info=True)
                future_result_map[original_question]= error_data
                temp_batch_results.append(error_data)
                error_count += 1
                
            finally: 
                processed_count += 1
            
            if len(temp_batch_results) >= BATCH_SIZE_TO_WRITE:
                append_results_to_csv(temp_batch_results, PROCESSED_QUESTIONS_TRACKING_FILE, is_first, is_generation_mode=False)
                temp_batch_results = [] # Reset batch
                if is_first:
                    is_first=False
        if temp_batch_results: # append the rest
            append_results_to_csv(temp_batch_results, PROCESSED_QUESTIONS_TRACKING_FILE, is_first)
                
    
    logger.info(f"Processing for current run complete.")
    logger.info(f"New questions processed in this run: {processed_count}. Errors in this run: {error_count}")
    logger.info(f"All results (new and previously processed) are in {PROCESSED_QUESTIONS_TRACKING_FILE}")
    logger.info("Process completed")

def run_question_generation():
    logger.info(f"Running in BATCH QUESTION GENERATION mode. Target: {NUM_QUESTIONS_TO_GENERATE} questions.")
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        try:
            df = pd.read_csv(LAPTOP_INFO_FILT_PATH)
            if df.empty:
                logger.error(f"Laptop specs file {LAPTOP_INFO_FILT_PATH} is empty. Cannot generate."); return
            logger.info(f"Loaded {len(df)} laptop specs for question generation.")
        except Exception as e:
            logger.error(f"Error loading laptop info csv {LAPTOP_INFO_FILT_PATH}: {e}")
            return
        num_already_generated = 0
        if os.path.exists(GENERATED_QA_OUTPUT_FILE):
            try:
                df_generated = pd.read_csv(GENERATED_QA_OUTPUT_FILE)
                num_already_generated = len(df_generated)
                logger.info(f"Found {num_already_generated} questions in existing file: {GENERATED_QA_OUTPUT_FILE}")
            except Exception as e:
                logger.warning(f"Could not read existing generated questions file, will start fresh or append: {e}")

        num_remain = NUM_QUESTIONS_TO_GENERATE - num_already_generated
        if num_remain <= 0:
            logger.info(f"Target of {NUM_QUESTIONS_TO_GENERATE} questions already met. Exiting generation.")
            return
        logger.info(f'Will generate {num_remain} quests more')
        
        BATCH_SIZE_PER_API_CALL = 10
        generated_data = generate_quest_in_batches(
            total_quest_need=num_remain,
            df=df,
            batch_size=BATCH_SIZE_PER_API_CALL
        )
        if generated_data:
            is_first = (num_already_generated==0)
            append_results_to_csv(generated_data, GENERATED_QA_OUTPUT_FILE, is_first, is_generation_mode = True)
            logger.info(f"Finished generating. Total questions in file now (approx): {num_already_generated + len(generated_data)}")
        else:
            logger.info("No new questions were successfully generated in this run.")
        
def main_controller():
    parser = argparse.ArgumentParser(description="Process or Generation foor Intent Classification")
    parser.add_argument(
        "--mode",
        type=str,
        choices=['process', 'generate'],
        required=True,
        help="'process' for classify intents for existing questions, 'generate' to create new questions"
    )
    args = parser.parse_args()
    if args.mode == 'process':
        run_to_process()
    elif args.mode == 'generate':
        run_question_generation()
    else:
        logger.error(f"Invalid mode: {args.mode}. Choose 'process' or 'generate'.")
                
if __name__ =="__main__":
    main_controller()
    
    
    
    
    
# # Handle for len of output == len of input regardless of empty questions
    # ordered_final_results = []
    # for q_orig in questions_to_process:
    #     if not q_orig.strip():
    #         ordered_final_results. append({
    #             "original_question": q_orig,
    #             "keep_question": 0,
    #             "corrected_question": None,
    #             "assigned_intent_id": [INTENT_DEFINITIONS['other']['id']]
    #         })
    #     elif q_orig in future_result_map:
    #         ordered_final_results.append(future_result_map[q_orig])
    #     else:
    #         # This should not happen
    #         logger.error(f"Question {q_orig} is not processed or found in results map")
    #         ordered_final_results.append({
    #             "original_question": q_orig,
    #             "keep_question": 0,
    #             "corrected_question": "ERROR_NOT_PROCESSED",
    #             "assigned_intent_id": [INTENT_DEFINITIONS['other']['id']]
    #         })
    #         error_count += 1
            
    # output_df = pd.DataFrame(ordered_final_results) # used ordered list
    # # Add intent name
    # intent_id_to_name = {v['id']: k for k, v in INTENT_DEFINITIONS.items()}
    
    # def get_intent_name(id_list):
    #     if isinstance(id_list, list):
    #         return [intent_id_to_name.get(id_val, []) for id_val in id_list]
    #     return []
    
    # output_df['assigned_intent_name'] = output_df['assigned_intent_id'].apply(get_intent_name)
    
    
    # # save to csv
    # try:
    #     output_df.to_csv(OUTPUT_CSV_FILE, index=False, encoding='utf-8-sig')
    #     logger.info(f"Successfully saved processed data to {OUTPUT_CSV_FILE}")
    #     logger.info(f"Total questions from input: {all_input_questions}. Non-empty questions processed: {processed_count}. Errors count: {error_count}")
    # except Exception as e:
    #     logger.error(f"Error saving output CSV file: {e}", exc_info=True)
