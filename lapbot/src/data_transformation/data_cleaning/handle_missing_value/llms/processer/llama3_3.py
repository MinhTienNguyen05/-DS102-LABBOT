from together import Together
from dotenv import load_dotenv
import logging
import os
import requests
import json

load_dotenv()
# logger()
logger = logging.getLogger(__name__)
logger.info("This is Llama 3.3 Free model")

try: 
    TOGERT_API_KEY = os.environ.get('TOGETHER_API_KEY')
except KeyError as e:
    logger.error('Error with API key')
    exit()
    
client = Together(api_key=TOGERT_API_KEY)
TOGETHER_API_URL = "https://api.together.xyz/v1/chat/completions"

def call_togetherai_api(prompt_text, expect_json=False):
    """ Call API of Together Ai with meta-llama/Llama-3.3-70B-Instruct-Turbo-Free

    Args:
        prompt_text : string of prompt
        expect_json (bool, optional): expect returned result format is JSON
    """
    headers = {
        "Authorization": f'Bearer {TOGERT_API_KEY}',
        "Content-Type": "application/json"
    }
    payload = {
        "model" : "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
        "max_tokens": 1024,
        "temperature": 0.2,
        "message": [{
            "role": "user",
            "content": prompt_text
            }]
    }
    try:
        response = requests.post(TOGETHER_API_URL, headers=headers, data=json.dumps(payload))
        if response.status_code == 200:
            result = response.json()
            if "choices" in result and result["choices"]:
                content = result["choices"][0]["message"]["content"].strip()
                if expect_json:
                    try:
                        return json.loads(content)
                    except json.JSONDecodeError:
                        logger. warning("Could not parse content into JSON. Return text only")
                        return content
                return content
            else:
                logger.warning(f"No valid response from Together AI")
                return None
        else:
            logger.error(f"Error with API Together: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error when calling Together API: {e}")
        return None

 