from llama3_3 import call_togetherai_api
from gemini_2_5_pro import call_gemini_api
import time

global_llm = {'model': None}

def set_llm_model(model_name):
    if model_name == 'gemini':
        global_llm['model'] = call_gemini_api
    elif model_name == 'llama':
        global_llm['model'] = call_togetherai_api
    else:
        raise ValueError("Model not supported")
    
def call_llm(prompt):
    if global_llm['model'] is None:
        raise RuntimeError("LLM nodel is not set")
    response = global_llm['model'](prompt)
    time.sleep(4.5)
    return response