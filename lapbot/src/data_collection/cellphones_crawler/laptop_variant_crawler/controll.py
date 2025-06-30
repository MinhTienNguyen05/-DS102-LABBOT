import subprocess # Run shell
import threading  # Create parallel threads
import pandas as pd
import os
import logging # Write log information
from settings import INPUT_FILE, OUTPUT_DIR, OUTPUT_FILES, BATCH_SIZE, NUM_THREADS

# Create folder if not existing
os.makedirs(OUTPUT_DIR, exist_ok=True)

def load_remaining_batches():
    """Upload uncrawled urls by comparing with 3 output files"""
    df_input = pd.read_csv(INPUT_FILE, encoding='utf-8')

    # Check crawled list
    crawled_urls = set()
    for file in OUTPUT_FILES:
        if os.path.exists(file):
            df_output = pd.read_csv(file, encoding='utf-8')
            if 'url' in df_output.columns:
                crawled_urls.update(df_output['url'].dropna().astype(str).tolist())

    df_remaining = df_input[~df_input['url'].astype(str).isin(crawled_urls)]
    return [df_remaining[i:i + BATCH_SIZE] for i in range(0,len(df_remaining), BATCH_SIZE)]

def run_scrapy_job(df_batch, thread_id):
    """Run scrapy in each batch and store results output files"""
    logging.info(f'Thread {thread_id} is processing {len(df_batch)} URL...')

    urls = list(df_batch['url'])
    urls_frm = str(urls).replace("'", '"')

    # Run scrapy with current batch
    command = f"""
        cd cellphones 
        scrapy crawl laptop
    """
    subprocess.run(command, shell=True, check=True)

    # Select file to store
    output_file = OUTPUT_FILES(thread_id % NUM_THREADS)

    # Check if file has data before writing header
    write_header = not os.path.exists(output_file) or os.stat(output_file).st_size == 0
    df_batch.to_csv(output_file, mode='a', header=write_header, index=False, encoding='utf-8')
    logging.info(f'Thread {thread_id} is stored in {output_file}')

def start_threads():
    """Launch batches in parallel across multiple threads, resuming from where it left off"""
    batches = load_remaining_batches()

    threads = []
    for i in range(0, len(batches), NUM_THREADS):
        for j in range(NUM_THREADS):
            if i + j >= len(batches):
                break

            thread = threading.Thread(target=run_scrapy_job, args=(batches[i + j], j)) # run run_scapy_job() parallely
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join() # Wait for thread complete before running other batch

    print('All batches completed')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    start_threads()

























