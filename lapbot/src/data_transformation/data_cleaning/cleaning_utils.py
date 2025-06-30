import pandas as pd
import numpy as np
import re
import unidecode
import seaborn as sns
import matplotlib.pyplot as plt

def detect_missing(df, custom_missing_values=None):
    """
    Phát hiện missing values, bao gồm cả:
    - NaN mặc định
    - Chuỗi thể hiện giá trị thiếu
    - List rỗng hoặc list chỉ chứa giá trị thiếu

    Parameters:
    - df: DataFrame đầu vào
    - custom_missing_values: list các chuỗi biểu diễn missing (mặc định có sẵn)

    Returns:
    - DataFrame gồm số lượng và % giá trị missing theo từng cột
    """
    import numpy as np
    import pandas as pd

    if custom_missing_values is None:
        custom_missing_values = ['null', 'na', 'n/a', 'nan', 'none', '-', '--', '', 'nat']

    # Đếm missing mặc định (NaN)
    missing = df.isnull().sum()

    # Kiểm tra từng cột
    for col in df.columns:
        series = df[col]

        # Với cột object hoặc chứa list
        if series.apply(lambda x: isinstance(x, (str, list, object))).any():
            def is_custom_missing(val):
                # None hoặc NaN thì đã tính ở bước đầu
                if pd.isna(val):
                    return False
                # Chuỗi
                if isinstance(val, str):
                    return val.strip().lower() in custom_missing_values
                # List
                if isinstance(val, list):
                    if len(val) == 0:
                        return True
                    # Kiểm tra nếu tất cả phần tử trong list là chuỗi thiếu
                    normalized = [str(v).strip().lower() for v in val if isinstance(v, str)]
                    return all(v in custom_missing_values for v in normalized)
                return False

            missing[col] += series.apply(is_custom_missing).sum()

    # Tính phần trăm
    missing_percent = 100 * missing / len(df)

    # Trả về DataFrame
    missing_df = pd.DataFrame({
        'Missing Values': missing,
        'Missing %': missing_percent
    })

    # Chỉ giữ cột có missing
    missing_df = missing_df[missing_df['Missing Values'] > 0].sort_values('Missing %', ascending=False)

    return missing_df


