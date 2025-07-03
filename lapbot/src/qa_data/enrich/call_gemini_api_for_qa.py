import google.generativeai as genai
import logging
import time
from config import GOOGLE_API_KEY, GEMINI_MODEL_NAME, GENERATION_CONFIG_FOR_QA, SAFETY_SETTINGS, MAX_RETRIES_API_CALL, API_CALL_DELAY_SECONDS


# logger
logger = logging.getLogger(__name__)
logger.info('This is Gemini 2.5 Flash model')

genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel(
    model_name=GEMINI_MODEL_NAME,
    generation_config=GENERATION_CONFIG_FOR_QA,
    safety_settings=SAFETY_SETTINGS
)


def call_gemini_api_for_quest_generation(prompt:str):
    """Calls the Gemini API with a specific prompt for intent classification and text correction"""
    for attempt in range(MAX_RETRIES_API_CALL):
        try:
            response = model.generate_content(prompt)
            print('Have responds')
            print(response)
            if response.parts:
                response_text = response.text.strip()
                logger.debug(f"Gemini raw response: {response_text[:200]}...")
                return response_text
            else:
                logger.warning(
                    f"Gemini API returned no parts\" (attempt {attempt + 1}). Full feedback: {response.prompt_feedback}"
                )
                if attempt < MAX_RETRIES_API_CALL - 1:
                    time.sleep(API_CALL_DELAY_SECONDS * (attempt + 1)) # Exponential backoff
                else:
                    logger.error(f"Max retries reached. Failed to get question")
            
        except Exception as e:
            logger.error(f"Error calling Gemini API for question (attempt {attempt + 1}): {e}", exc_info=True)
            if "429" or "rate limit" in str(e).lower():
                wait_time = API_CALL_DELAY_SECONDS* (attempt + 2)
                logger.warning(f"Rate limit hit. Waiting for {wait_time} seconds before retrying")
                time.sleep(wait_time)
            elif attempt < MAX_RETRIES_API_CALL - 1:
                time.sleep(API_CALL_DELAY_SECONDS)
            else:
                logger.error(f'Max retried reached. Failed to generate question')
                return None
    return None





