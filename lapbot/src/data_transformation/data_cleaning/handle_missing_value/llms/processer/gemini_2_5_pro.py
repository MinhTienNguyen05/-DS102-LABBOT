from dotenv import load_dotenv
import google.generativeai as genai
import logging
import os

load_dotenv()

# logger
logger = logging.getLogger(__name__)
logger.info("This is Gemini 2.5 Pro model")

try:
    GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')
except KeyError:
    logger.error('Error with API key')
    exit()
    

def call_gemini_api(prompt_text, except_json=False):
    """Function to call api of gemini 2.5 Pro"""
    genai.configure(api_key=GOOGLE_API_KEY)
    llm_model = genai.GenerativeModel('gemini-2.5-flash-preview-05-20')
    try: 
        if except_json:
            response = llm_model.generate_content(prompt_text, generation_config=genai.types.GenerationConfig(max_output_tokens=1024,
                                                                                                               temperature=0.1,
                                                                                                               response_mime_type='application/json'))
            response.resolve()
            if response.parts:
                return response.text.strip()
            else:
                logger.warnign(f"Warning: Gamini API returned no parts for JSON. Fallback or error {response.prompt_feedback}")
                return None
        else:
            response = llm_model.generate_content(prompt_text,generation_config=genai.types.GenerationConfig(temperature=0.2))
            response.resolve()
            if response.parts:
                return response.text.strip()
            else:
                logger.warnign(f"Warning: Gamini API returned no parts for JSON. Fallback or error {response.prompt_feedback}")
                return None
    except Exception as e:
        logger.error(f"Error with calling Gemini API: {e}")
        if hasattr(e, 'response') and e.response:
            logger.error(f"API Response Error: {str(e)}")
        return None
