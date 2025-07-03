import google.generativeai as genai
import logging
import time
from config import GOOGLE_API_KEY, GEMINI_MODEL_NAME, GENERATION_CONFIG_JSON, SAFETY_SETTINGS, MAX_RETRIES_API_CALL, API_CALL_DELAY_SECONDS


# logger
logger = logging.getLogger(__name__)
logger.info('This is Gemini 2.5 Flash model')

genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel(
    model_name=GEMINI_MODEL_NAME,
    generation_config=GENERATION_CONFIG_JSON,
    safety_settings=SAFETY_SETTINGS
)


def call_gemini_api(question_text: str, prompt:str):
    """Calls the Gemini API with a specific prompt for intent classification and text correction"""
    for attempt in range(MAX_RETRIES_API_CALL):
        try:
            logger.debug(f"Attempt {attempt + 1}/{MAX_RETRIES_API_CALL} to call Gemini for question: \"{question_text[:100]}...\"")
            response = model.generate_content(prompt)
            if response.parts:
                response_text = response.text.strip()
                logger.debug(f"Gemini raw response: {response_text[:200]}...")
                return response_text
            else:
                block_reason_msg = ""
                if response.prompt_feedback and hasattr(response.prompt_feedback, 'block_reason'):
                    block_reason_msg = f"Block reason: {response.prompt_feedback.block_reason_message or response.prompt_feedback.block_reason}"
                logger.warning(
                    f"Gemini API returned no parts for question: \"{question_text[:50]}...\" (attempt {attempt + 1}). "
                    f"{block_reason_msg} Full feedback: {response.prompt_feedback}"
                )
                if attempt < MAX_RETRIES_API_CALL - 1:
                    time.sleep(API_CALL_DELAY_SECONDS * (attempt + 1)) # Exponential backoff
                else:
                    logger.error(f"Max retries reached. Failed to get response for question: \"{question_text[:50]}...\"")
            
        except Exception as e:
            logger.error(f"Error calling Gemini API for question \"{question_text[:50]}...\" (attempt {attempt + 1}): {e}", exc_info=True)
            if "429" or "rate limit" in str(e).lower():
                wait_time = API_CALL_DELAY_SECONDS* (attempt + 2)
                logger.warning(f"Rate limit hit. Waiting for {wait_time} seconds before retrying")
                time.sleep(wait_time)
            elif attempt < MAX_RETRIES_API_CALL - 1:
                time.sleep(API_CALL_DELAY_SECONDS)
            else:
                logger.error(f'Max retried reached. Failed to process question "{question_text[:50]}...')
                return None
    return None