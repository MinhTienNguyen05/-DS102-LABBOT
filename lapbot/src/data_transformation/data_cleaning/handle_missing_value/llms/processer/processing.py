from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import time
import traceback
import tqdm
import logging
import pandas as pd
import argparse
from llm_model_sellector import call_llm



def build_prompt(row_data, null_columns_list):
    """Constructs a detailed prompt for LLM, focusing on standarrdised output

    Args:
        row_data: each row in null-fetched datafram
        null_columns_list: a list of null columns in the given row above
    """
    laptop_name = row_data.get('name', 'N/A')
    manufacturer = row_data.get('manufacturer', 'N/A')

    existing_specs_parts = []
    for col, val in row_data.items():
        if pd.notna(val) and col not in null_columns_list:
            existing_specs_parts.append(f"- {col}: {val}")
    if existing_specs_parts:
        existing_specs_str = '\n'.join(existing_specs_parts)
    else:
        existing_specs_str = 'No other specifications are known for this data row'

    prompt = f"""
    You are a highly proficient AI assistant specialiized in accurately retrieving and standardizing laptop technical specifications from web sources
    Your task is to find missing technical specifications for a given laptop and return these specifications in a structured JSON format, adhearing to strict data type and unit conversion rules

    ### CONTEXT:
    You are procided with data for a laptop entry that has some missing (NULL) specifications
    Known information about this laptop included:
	○  Laptop name: {laptop_name}
	○  Manufacturer: {manufacturer}
	○  Other known specifications: {existing_specs_str}
    The following columns have missing information and require your lookup: {', '.join(null_columns_list)}

    ### INSTRUCTIONS:
	1.  Web search: Base on the 'Laptop name', the 'Manufacturer' and any 'Other known specifications' (if needed), perform a targeted web search to find the values for the mising columns: {', '.join(null_columns_list)}

	2.  JSON output requirement:
	○  You MUST return the results as a single, valid JSON object
	○  The 'key' in the JSON object must be exactly match the column names provided in the missing columns list '{null_columns_list[0]}'
	○  If, after a thorough search, you cannot find reliable information for a specifiic column, use the JSON value 'null' (NOT the string "null") for that key

	3.  Data formating and unit conversion (CRITICAL)
	○  For all numerical specification, you MUST return ONLY THE NUMERICAL VALUE (as a float or integer). DO NOT include units (like "GB", "Hz", "mm", "GHz", "VND", "Wh") in the JSON value itself
	○  Adhere to the following specific instructions for each column type if it appears in the 'null_columns_list':
    + 'laptop_height_mm': report height in milimeters(mm). Return ONLY the numerical value as a float( for 23.5 cm , convert and turn '235.0')
    + 'laptop_width_mm': report width in milimeters(mm). Return ONLY the numerical value as a float( for 39.5 cm , convert and turn '395.0')
    + 'laptop_depth_mm': report depth/thickness in milimeters(mm). Return ONLY the numerical value as a float( for 1.75 cm , convert and turn '17.5')
    + 'cpu_boost_clock_ghz': Report CPU boost clock speed in Gigahertz (GHz). Return ONLY the numerical value as a float (e.g., for 4.9 GHz, return 4.9; for 5000 MHz, return 5.0)
    + 'root_price_vnd': Report original price in Vietnamese Dong (VND). Find the original price in USD, then you MUST convert into VND using the fixed conversion rate: 1 USD = 26000 VND. Return ONLY the numerical value as a float or integer, without commas or currency symbols (e.g., for $750 USD, return 19500000.0). Do not include any units or text.
    + 'cpu_threads': Report the number of CPU threads. Return ONLY the numerical value as an integer (e.g., 16)
    + 'cpu_cores': Report the number of CPU cores. Return ONLY the numerical value as an integer (e.g., 10)
    + 'ram_speed': Report RAM speed in Megahertz (MHz). Return ONLY the numerical value as a float or integer (for 4800 MHz, return 4800.0)
    + 'ram_type': (e.g., "ddr4", "lpddr5", "ddr5") Return as a lowercase string without spaces
    + 'refresh_rate_hz': Report display refresh rate in Hertz (Hz). Return ONLY the numerical value as an integer or float (e.g., for 60Hz, return 60.0; for 144Hz, return 144.0)
    + 'cpu_base_clock_ghz': Report CPU base clock speed in Gigahertz (GHz). Return ONLY the numerical value as a float (e.g., for 2.4 GHz, return 2.4; for 3200 MHz, return 3.2).
    + 'ram_slots': Report the number of RAM slots. Return ONLY the numerical value as an integer (e.g., 0, 1, 2). If RAM is soldered and no slots, return 0.
    + 'battery_capacity_wh': Report battery capacity in Watt-hours (Wh). Return ONLY the numerical value as a float (e.g., for 47Wh, return 47.0)
    + 'cpu_model': (e.g., "13620h", "i7-12700h", "ryzen 7 5800u") Return as a string, preferably lowercase and normalized (e.g., remove "Intel Core", "AMD Ryzen" prefixes if the manufacturer column already specifies this, focus on the model number/name). 
    + 'vga_type' This field MUST be one of two specific string values:
		■  If the laptop uses integrated graphics (e.g., Intel Iris Xe, AMD Radeon Graphics), return "card tích hợp"
		■  If the laptop has a dedicated/discrete graphics card (e.g., NVIDIA GeForce RTX 3050, AMD Radeon RX 6600M), return "card rời"
		■  Do not use any other values.
    + 'vga_vram_gb': Report dedicated Video RAM (VRAM) capacity in Gigabytes (GB). Return ONLY the numerical value as a float (e.g., for 4GB VRAM, return 4.0). If vga_type is "card tích hợp", this value should typically be 0.0 as integrated graphics share system memory. Clarify if "shared memory" should be reported here or if it should be strictly for dedicated VRAM. For now, assume dedicated VRAM; if none, return null
    + 'laptop_camera': This field MUST be one of two specific string values:
		■  If the camera is Full HD (typically 1080p), return "full hd".
		■  If the camera is HD (typically 720p), return "hd".
		■  If other (e.g., VGA, or specific resolution like 5MP), and no direct match to "hd" or "full hd", attempt to classify or return the specific resolution as a string if these two are not applicable. However, strongly prefer "hd" or "full hd". If uncertain between the two, or if it's a higher non-standard resolution, you may return the most descriptive common term.
	+ 'discounted_price_vnd': Report discounted price in Vietnamese Dong (VND). Find the discounted price in USD, then you MUST convert into VND using the fixed conversion rate: 1 USD = 26000 VND. Return ONLY the numerical value as a float or integer, without commas or currency symbols (e.g., for $750 USD, return 19500000.0). Do not include any units or text.

	4.  Chain of thought:
    Step 01: Understand the data requirements and the format rules for each missing field
    Step 02: Perform a web search (oor rely on your interrnal knowledge) using the provided laptop name, manufacturer, and known specification
    Step 03: Summerize and extract relevant technical specifications based on your findings
    Step 04: The price is found in USD, convert it into VND using the fixed conversion rate: 1 USD = 26000VND
    Step 04: Format and return the completed information as a valid JSON object, following all formatting and unit conversion instructions precisely

	5.  Data source priority: Proritize information form official manufacturer websites, reputable e-commerce listings (from the manufacturer or major retailers), or well-known tech reiview sites

    ### INPUT DATA EXAMPLE (Just illustrative, showing how information might be structured for a request):
    Laptop name: Lenovo Legion 5 Pro 16ACH6H
    Manufacturer: Lenovo
    Known Specs:
	○  cpu_model: i5-12500H
	○  ram_type: ddr5
    Null Columns to fill: ["ram_speed", "vga_type", "vga_vram_gb", "refresh_rate_hz", "laptop_camera", "battery_capacity_wh"]

    ### EXPECTED JSON OUTPUT FORMAT (This is the precise format you MUST return):
    `json
    {{
    "ram_speed": 4800.0,
    "vga_type": "card rời",
    "vga_vram_gb": 6.0,
    "refresh_rate_hz": 144.0,
    "laptop_camera": "hd",
    "battery_capacity_wh": 57.5
    }}

    """
    return prompt


def process_row(index, row, df_columns):
    null_columns = row[row.isnull()].index.tolist()
    if not null_columns:
        return index, {}

    prompt_text = build_prompt(row, null_columns)

    try:
        response_text = call_llm(prompt_text)
        if not response_text:
            return index, {}

        filled_data = response_text.strip().removeprefix("```json").removesuffix("```").strip()
        filled_data = json.loads(filled_data)

        cleaned_data = {}
        for col_name, value in filled_data.items():
            if col_name in df_columns and col_name in null_columns:
                if value is not None:
                    cleaned_data[col_name] = value
        return index, cleaned_data

    except Exception as e:
        logging.error(f"[ERROR] row {index}: {e}")
        traceback.print_exc()
        return index, {}


def process_laptop_data_parallel(df, max_workers=4):

    df_updated = df.copy()
    rows_to_process = df[df.isnull().any(axis=1)]

    row_tuples = [(index, row) for index, row in rows_to_process.iterrows()]
    df_columns = df.columns

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_index = {
            executor.submit(process_row, index, row, df_columns): index
            for index, row in row_tuples
        }

        for future in tqdm.tqdm(as_completed(future_to_index), total=len(row_tuples)):
            try:
                index, cleaned_data = future.result()
                for col_name, value in cleaned_data.items():
                    df_updated.at[index, col_name] = value
                time.sleep(2)
            except Exception as e:
                logging.error(f"[ERROR - future] {e}")
                traceback.print_exc()

    return df_updated

