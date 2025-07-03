import pandas as pd
import random 
import json
import logging
import time
from tqdm import tqdm
from typing import List, Dict, Any, Tuple
from call_gemini_api_for_qa import call_gemini_api_for_quest_generation


logger = logging.getLogger(__name__)
from config import(
    LAPTOP_INFO_FILT_PATH, INTENT_DEFINITIONS, GEMINI_MODEL_NAME, GENERATION_CONFIG_FOR_QA, SAFETY_SETTINGS, API_CALL_DELAY_SECONDS
)

def select_random_specs_for_context(df_laptops: pd.DataFrame, num_laptops: int = 3) -> List[Dict[str, Any]]:
    """Chọn thông tin từ một vài laptop ngẫu nhiên để làm ngữ cảnh phong phú."""
    if df_laptops.empty or len(df_laptops) < num_laptops:
        return []
    
    context_specs = []
    sampled_rows = df_laptops.sample(num_laptops)
    
    for _, row in sampled_rows.iterrows():
        # Lấy các cột thông số thú vị
        priority_cols = [
            'name', 'manufacturer', 'cpu_model', 'ram_storage', 'storage_gb', 'vga_type',
            'display_size', 'refresh_rate', 'root_price', 'nhu_cau_su_dung', 'product_weight'
        ]
        specs = row[priority_cols].dropna().to_dict()
        context_specs.append(specs)
    return context_specs

# def select_random_specs (df, num_specs = 3):
#     """Pick up some random from a row of laptop info
#     """
#     if df.empty:
#         return {}
    
#     laptop_row = df.sample(1).iloc[0]
#     all_specs = laptop_row.dropna().to_dict()
    
#     priority_cols = [
#         'name', 'manufacturer', 'cpu_model', 'cpu_cores', 'cpu_threads', 'cpu_brand', 'cpu_series',
#         'ram_storage', 'ram_type', 'ram_speed', 'storage_gb', 'vga_type', 'vga_brand', 'vga_vram',
#         'display_size', 'refresh_rate', 'display_width', 'display_height', 'root_price', 
#         'nhu_cau_su_dung', 'laptop_color', 'product_weight', 'battery_capacity'
#     ]
#     available_priority_specs = {k: v for k, v in all_specs.items() if k in priority_cols}
#     if len(available_priority_specs) >= num_specs:
#         selected_keys = random.sample(list(available_priority_specs.keys()), k=min(num_specs, len(available_priority_specs)))
#     else:
#         remaining_keys = [k for k in all_specs.keys() if k not in available_priority_specs and k not in ['urrl_path', 'image', 'product_id']]
#         needed_more = num_specs - len(available_priority_specs)
#         selected_keys = list(available_priority_specs.keys())
#         if remaining_keys and needed_more > 0:
#             selected_keys.extend(random.sample(remaining_keys, k=min(needed_more, len(remaining_keys))))
#     return {key: all_specs[key] for key in selected_keys if key in all_specs}


def build_question_generation_prompt(num_questions_in_batch, specs_context):
    """
        Builds a prompt to generate a BATCH of questions in one API call.
    """
    # intent_names_str = ", ".join(target_intents)
    # intent_details_str = ""
    # for intent_name in target_intents:
    #     if intent_name in INTENT_DEFINITIONS:
    #         details = INTENT_DEFINITIONS[intent_name]
    #         intent_details_str += f"{intent_name} (ID: {details['id']}): {details['description_vi']}. Key words {', '.join(details['keywords_vi'][:5])}..."
    
    # # Create a whole descriptive text with intents and laptop specifications as the input for llm
    # specs_str = "No specific product in mind for this question"
    # product_name_hint = "a generic laptop"
    # if laptop_specs:
    #     specs_list = []
    #     if 'name' in laptop_specs:
    #         product_name_hint = f"the laptop '{laptop_specs['name']}'"
    #         for key, value in laptop_specs.items():
    #             if pd.notna(value) and str(value).strip != "":
    #                 if isinstance(value, float): # Make it round
    #                     value_str=f"{value:.1f}" if value % 1 != 0 else f"{int(value)}"
    #                 else:
    #                     value_str = str(value)
    #                 specs_list.append(f"{key}: {value}")
    #         if specs_list:
    #             specs_str = f"Consider the following product information as context (you can pick some details or the product name or generate a more general question): \n " + "\n".join(specs_list)
                
    context_str = "No specific product context provided. Generate general questions."
    if specs_context:
        context_str = "Here is some context about available laptops. Use these details to inspire your questions. You can mix and match features, prices, and usage purposes. Some questions can mention a product name, others can be more general.\n\n"
        for i, specs in enumerate(specs_context, 1):
            context_str += f"--- Product Context {i} ---\n"
            for key, value in specs.items():
                if pd.notna(value):
                    context_str += f"- {key}: {value}\n"
            context_str += "\n"

    prompt = f"""
    You are a highly efficient AI Data Generator. Your task is to create a batch of high-quality, clean, and diverse Vietnamese questions about laptops for training a multi-label classification model
    
    ### CONTEXT:
    You need to generate **{num_questions_in_batch}** unique questions.
    Each question must be classifiable into one or more of the following intents:
    - `recommend_budget` (ID: 0): Questions about price, budget, cost.
    - `recommend_usage` (ID: 1): Questions about usage needs (e.g., gaming, graphic design, office work).
    - `tech_detail` (ID: 2): Questions about specific technical specifications (e.g., CPU, RAM, screen).
    You are provided with the following product context to make your questions realistic and grounded in real data.
    {context_str}

    ### INSTRUCTION:
    1.  **Generate a total of {num_questions_in_batch} questions.**
    2.  **Question Style:** 
        - All question MUST be clean, grammatically correct, and professional
        - They must have a clear subject and predicate
        - **DO NOT** include any conversational filler, salutations, or pleasantries like "shop ơi", "ad ơi", "cho mình hỏi", "ạ", "nhỉ", etc. The questions should be direct and to the point.
        - All questions should be of the "What", "Which" oor "yes/No" type
    
    3. **Intent Distribution**
        - Create a diverse mix of questions
        -  **Prioritize generating questions that combine multiple intents.** For example, a question asking for a "gaming laptop under 20 million" combines `recommend_usage` (gaming) and `recommend_budget` (under 20 million)
        - Also include single-intent questions for variety
        - Example combinations: [1, 0], [1, 2], [0, 2], [0, 1, 2]
        
    4. **Output Format**
        - You must return a single, valid JSON object
        - This object must contain one key: "generated_data"
        - The value of "generated_data" must be a JSON ARRAY containing exactly {num_questions_in_batch} objects
        - Each object in the array represents one question and MUST have the following four keys:
            - "question": The generated, clean Vietnamese question string
            - "recommend_budget": "1" if the question relates to this intent, '0' otherrwise
            - `"recommend_usage"`: `1` if the question relates to this intent, `0` otherwise.
            - `"tech_detail"`: `1` if the question relates to this intent, `0` otherwise
        - At least oone of the intent keys must have a value of '1' for each generated question
        
        ### EXAMPLE OF EXPECTED JSON OUTPUT:
        ```json
        {{
        "generated_data": [
            {{
            "question": "Laptop nào phù hợp cho lập trình viên với ngân sách dưới 25 triệu đồng?",
            "recommend_budget": 1,
            "recommend_usage": 1,
            "tech_detail": 0
            }},
            {{
            "question": "Cấu hình CPU và RAM của máy Asus TUF Gaming A15 là gì?",
            "recommend_budget": 0,
            "recommend_usage": 0,
            "tech_detail": 1
            }},
            {{
            "question": "Máy Dell XPS có card đồ họa rời và giá bao nhiêu?",
            "recommend_budget": 1,
            "recommend_usage": 0,
            "tech_detail": 1
            }},
            {{
            "question": "Tìm laptop gaming chip Core i7, RAM 16GB, giá khoảng 30 triệu.",
            "recommend_budget": 1,
            "recommend_usage": 1,
            "tech_detail": 1
            }}
        ]
        }}
 
    ### TASK:
    Generated the JSON object containing a list od {num_questions_in_batch} questions as specificed
    """
    return prompt

def generate_quest_in_batches(total_quest_need, df, batch_size=20):
    """
    Generates a specified number of questions by calling the LLM in batches.
    """
    all_generated_data = []
    if df.empty:
        logger.warning("Laptop dataframe is empty")
        return []
    pbar = tqdm(total=total_quest_need, desc = "Generating quests in batches")
    while len(all_generated_data) < total_quest_need:
        num_to_gen_this_batch = min(batch_size, total_quest_need - len(all_generated_data))
        if num_to_gen_this_batch <=0:
            break
        
        # 1. Get frwsh context for each batch
        specs_context = select_random_specs_for_context(df, num_laptops=random.randint(3, 5))
        
        # 2. Built prompt
        prompt = build_question_generation_prompt(num_to_gen_this_batch, specs_context)
        
        # 3. Call LLM
        response_json_str = call_gemini_api_for_quest_generation(prompt)
        if response_json_str:
            try:
                parse_response = json.loads(response_json_str)
                batch_data = parse_response.get("generated_data")
                
                if batch_data and isinstance(batch_data, list):
                    # Validate each item in  batch
                    valid_items = []
                    required_key ={'question', 'recommend_budget', 'recommend_usage', 'tech_detail'}
                    for item in batch_data:
                        if isinstance(item, dict) and required_key.issubset(item.keys()):
                            valid_items.append(item)
                        else:
                            logger.warning(f"Skipping malformed item in batch: {item}")
                    all_generated_data.extend(valid_items)
                    pbar.update(len(valid_items))
                    logger.info(f"Successfully generated and parsed a batch of {len(valid_items)} questions.")
                else:
                    logger.warning(f"LLM did not return a valid 'generated_data' list in the JSON response.")
            except (json.JSONDecodeError, TypeError) as e:
                logger.error(f"Failed to decode or parse JSON batch from LLM. Error: {e}. Response: {response_json_str[:300]}")
        else:
            logger.error("LLM call for batch question generation returned None. Skipping this batch.")
        time.sleep(API_CALL_DELAY_SECONDS * 2)
    pbar.close()
    return all_generated_data


    