import json
import logging
from config import INTENT_DEFINITIONS
from call_gemini_api import call_gemini_api

logger = logging.getLogger(__name__)

def built_prompt(original_quest:str) -> str:
    """
    Builds a detailed prompt for the LLM to classify intent, correct grammar, and decide if the question should be kept.

    Args:
        original_quest (str)

    Returns:
        str
    """
    intent_list_str = ""
    for intent_key, details in INTENT_DEFINITIONS.items():
        if intent_key != 'other':
            intent_list_str += f"-Intent Name: {intent_key}, ID: {details['id']}, Description: {details['description_vi']}"
            intent_list_str += f"Typical Keywords: {','.join(details['keywords_vi'])}"
    prompt = f"""
    You are an expert AI assistant tasked with analyzing Vietnamese questions related to laptops.
    Your GOAL is to:
    - Determin if the question is a "What", "Which" or "Yes/No" type question.
    - If it is one of these types. correct any grammartical errors or typos and simplify it by removing unnecessary salutations or filter words, while preserving the core meaning
    - Assign one of the predefined intents to the corrected questions
    - Decide if the question should be kept for further processing based on its type and relevance to the defined intents
    
    ### PREDIFINED INTENTS:
    {intent_list_str}
    - Intent Name: 'other', ID: {INTENT_DEFINITIONS['other']['id']}, Description: {INTENT_DEFINITIONS['other']['description_vi']} (Use this if the question is not a  What/Which/Yes/No type, or of it clearly does not fit anyother defined intent, even if corrected)
    - Note:
        * recommend_budget: is used when the customer asks for recommendations based on their budget
        * recommend_usage: is used when the customer wants a laptop recommendation based on their specific usage needs
        * tech_detail is used when the customer asks about the technical specifications of a laptop
        
        
    
    ### INPUT QUESTION: "{original_quest}"
    
    ### INSTRUCTIONS 
    #### FOR OUPUT
    You MUST return your analysis as a single, valid JSON with the following structure:
    
    ```json
    {{
        "original_question": "string",  // The original input question
        "keep_question": "integer",     // 1 if the question is a What/Which/Yes/No type AND relevant to the defined intents (recommend_budget, recommend_usage, tech_detail). 0 otherwise.
        "corrected_question": "string | null", // The grammatically corrected and simplified question if keep_question is 1. Null if keep_question is 0.
        "assigned_intent_id": "ARRAY_OF_INTEGERS | null" // A list of IDs of the assigned intents (e.g., [0, 2], [1], [0, 1, 2]) if keep_question is 1. If keep_question is 0, this should be [{INTENT_DEFINITIONS['other']['id']}] or null. If no specific intent from 0, 1, 2 fits a kept question, return an empty null.
    }}    
    
    
    #### CHAIN OF THOUGHT:
       STEP 01. ANALYZE QUESTION TYPE:
        - First, determine if the input question is primarily a "What" question (e.g., "Laptop nào...", "Thông số gì..."), a "Which" question (e.g., "Chọn cái nào..."), or a "Yes/No" question (e.g., "Có hỗ trợ... không?", "Máy này có card rời không?").
        - If it is NOT a "What", "Which", or "Yes/No" question, set keep_question to 0, corrected_question to null, and assigned_intent_id to {INTENT_DEFINITIONS['other']['id']}.
       
       STEP 02. IF IS A "WHAT", "WHICH", OR "YES/NO" QUESTION: 
        a. Correct and Simplify:
        -  Correct any spelling mistakes or grammatical errors in the Vietnamese question.
        - Remove polite filler words, salutations (e.g., "ad ơi", "shop ơi", "bạn ơi"), or unnecessary pronouns/phrases that don't change the core query (e.g., "cho mình hỏi", "tư vấn giúp mình").
        - The corrected_question should be PRECISE, CONCISE and focused on the technical query
        
        b. Assign Intent:
        - Based on the corrected_question, identify ALL relevant intents from the list:
            * {INTENT_DEFINITIONS['recommend_budget']['id']} (recommend_budget)
            * {INTENT_DEFINITIONS['recommend_usage']['id']} (recommend_usage)
            * {INTENT_DEFINITIONS['tech_detail']['id']} (tech_detail)
            * The assigned_intent_id fild should be a list containing the ids of ALL applicable intents. 
        - If the corrected question, despite being a What/Which/Yes/No type, does not clearly fit into intents 0, 1, 2 ; OR asks about store availability at a specific location (e.g., “Is this available in Hanoi?”, “Still in stock in HCMC?”), OR asks about promotions, discounts, or bundled gifts (e.g., “Is a mouse included?”, “Any discounts now?”, “Any free accessories?”)...:
            * Set keep_question to 0
            * Set corrected_question to the corrected version 
            * Set assigned_intent_ids to [{INTENT_DEFINITIONS['other']['id']}] 
        - If it fits AT LEAST one of the intents 0 OR 1 OR 2:
            * Set keep_question to 1
            * Set "assigned_intent_ids" to a list of all matching intent IDs (e.g., [0], [1, 2], etc.)
        - If the corrected question is still relevant and technical, but does not clearly match any specific intent (0, 1, or 2):
            * Set keep_question to 0
            * Set corrected_question to the corrected version 
            * Set assigned_intent_ids to [{INTENT_DEFINITIONS['other']['id']}]
            
        Step 03: Format and return the completed information as a valid JSON object, following all formatting instructions precisely

    ### EXAMPLE: 
    Example 01: 
        Input Question: "ad ơi cho mình hỏi lap top nào tầm giá 15tr sài chơi game ổn định ạ?"
        Expected JSON Output:
        Generated json
        {{
        "original_question": "ad ơi cho mình hỏi lap top nào tầm giá 15tr sài chơi game ổn định ạ?",
        "keep_question": 1,
        "corrected_question": "laptop nào tầm giá 15 triệu sử dụng để chơi game ổn định?",
        "assigned_intent_id": [{INTENT_DEFINITIONS['recommend_budget']['id']}, {INTENT_DEFINITIONS['recommend_usage']['id']}]
        }}
        
    Example 02: 
        Input Question: "máy này có card đồ hoạ rời k shop, ram bao nhiêu gb vậy?"
        Expected JSON Output:
        Generated json
        {{
        "original_question": "máy này có card đồ hoạ rời k shop, ram bao nhiêu gb vậy?",
        "keep_question": 1,
        "corrected_question": "máy này có card đồ họa rời không và RAM bao nhiêu GB?",
        "assigned_intent_ids": [{INTENT_DEFINITIONS['tech_detail']['id']}]
        }}
        
    """
    return prompt

def process_single_question(original_question:str):
    """Process a single question: build prompt, calls LLM, parse JSON

    Args:
        original_question (str): _description_

    Returns:
        dict | None: _description_
    """
    if not isinstance(original_question, str) or not original_question.strip():
        logger.warning("Recieved an empty or non-string question")
        return {
            "original question": original_question,
            "keep_question": 0,
            "corrected_question": None,
            "assigned_intent_id": INTENT_DEFINITIONS['other']['id']
        }
    prompt = built_prompt(original_question)
    logger.debug(f"Generated prompt for question: {original_question[:100]}...")
    response_json_str = call_gemini_api(original_question, prompt)
    if response_json_str:
        try:
            parsed_response = json.loads(response_json_str)
            # Validate structure
            required_keys = ['original_question', "keep_question", "corrected_question", "assigned_intent_id"]
            if not all(key in parsed_response for key in required_keys):
                logger.error(f"LLM response missing required keys for quest: {original_question}. Response: {parsed_response}")
                return {
                    "original_question": original_question,
                    "keep_question": 0,
                    "corrected_question": "ERROR_LLM_RESPONSE_MALFORMED",
                    "assigned_intent_ids": [INTENT_DEFINITIONS['other']['id']]
                }
                
            # Make sure assigned_intent_id is a list or null
            intent_id = parsed_response.get("assigned_intent_id")
            if intent_id is not None and not isinstance(intent_id, list):
                logger.warning(f"LLM return non-list for assigned_intent_id: {intent_id}. Force into list")
                if isinstance(intent_id, int): # if it is an int --> list
                    parsed_response['assigned_intent_id'] = [intent_id]
                else:
                    parsed_response['assigned_intent_id'] = [INTENT_DEFINITIONS['other']['id']] if parsed_response.get('keep_question') == 0 else []
            
            # Make sure original_question fit with input
            if parsed_response.get("original_question") != original_question:
                logger.warning(f"Mismatch in original quest form LLM for input: {original_question}. LLM return: {parsed_response.get('original_question')}")
                parsed_response['original_question'] = original_question
            
            logger.info(f"Successfully processed question: {original_question[:50]}... -> Intent ID: {parsed_response.get('assigned_intent_id')}, Keep: {parsed_response.get('keep_question')}")
            return parsed_response
        
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON response for question: \"{original_question[:50]}...\". Error: {e}. Response: {response_json_str[:500]}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error parsing LLM response for question: \"{original_question[:50]}...\". Error: {e}", exc_info=True)
            return None
    else:
        logger.error(f"No reponse from LLM for question: {original_question[:50]}...")
        return None
    
    