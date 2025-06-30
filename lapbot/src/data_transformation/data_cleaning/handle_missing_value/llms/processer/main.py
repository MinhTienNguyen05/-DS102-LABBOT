import pandas as pd
from processing import process_laptop_data_parallel
from dotenv import load_dotenv
import logging
import os
import argparse
from llm_model_sellector import set_llm_model


# logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    handlers= [
        logging.FileHandler("filling_null.log", mode="w", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

logger = logging .getLogger(__name__)

def load_configuration():
    load_dotenv()
    config = {}
    config['input_file'] = os.getenv('INPUT_FILE_PATH')
    config['output_file'] = os.getenv('OUTPUT_FILE_PATH')
    config['google_api_key'] = os.getenv('GOOGLE_API_KEY')
    config['together_api_key'] = os.getenv('TOGETHER_API_KEY')
    if not all([config['input_file'], config['output_file'], config['google_api_key'], config['together_api_key']]):
        logger.error("Error: Something is wrong with the environmental variants")
        return None
    logger.info('Configuration successed')
    return config

def load_data_from_file(filepath):
    try:
        df = pd.read_csv(filepath)
        df = df.replace('', pd.NA).fillna(pd.NA)
        logger.info(f"Loaded data from {filepath}. Columns: {len(df.columns)}. Rows: {len(df)}")
        return df
    except FileNotFoundError:
        logger.error(f"Could not find input file: {filepath}")
        return None
    except pd.errors.EmptyDataError:
        logger.error(f"Input file {filepath} is empty")
        return None
    except Exception as e:
        logger.error(f"Error with loading file {filepath}: {str(e)}")
        return None
    
def ensure_output_dir(filepath):
    output_dir = os.path.dirname(filepath)
    if output_dir and not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir)
            logger.info(f"Create output dir: {output_dir}")
        except OSError as e:
            logger.error(f"Error creating output dir {output_dir}: {e}")
            return False
    return True

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', choices=['gemini', 'llama'], default='gemini', help='LLM model to use')
    args = parser.parse_args()
  
    
    #Load config
    config = load_configuration()
    if not config: 
        return
    # Set LLM model based on CLI input
    set_llm_model(args.model)
    
    # Varify ouput file name
    if args.model == 'gemini':
        config['output_file'] = config['output_file'].replace('.csv', '_gemini.csv')
    else:
        config['output_file'] = config['output_file'].replace('.csv', '_llama.csv')
    # config['output_file'] = config['output_file'].replace('.csv', f"_{args.model}.csv")
    df_origin = load_data_from_file(config['input_file'])
    if df_origin is None:
        return
    
    
    df_filled = process_laptop_data_parallel(df_origin, max_workers=2)
    if ensure_output_dir(config['output_file']):
        try:
            df_filled.to_csv(config['output_file'], index=False)
            logger.info(f"Sucessfully saved to{config['output_file']}")
        except Exception as e:
            logger.error(f"Failed to save {config['output_file']}")
    else:
        logger.error('Cannot create output_dir')
    logger.info('Process completed')
    
if __name__ == "__main__":
    main()