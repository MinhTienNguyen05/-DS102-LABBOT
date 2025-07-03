import os
from dotenv import load_dotenv

load_dotenv(dotenv_path='.env.local')

# API Configuration
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
if not GOOGLE_API_KEY:
    raise ValueError ('GOOGLE_API_KEY is not set')

# Model Configuration
GEMINI_MODEL_NAME = 'gemini-2.5-flash-lite-preview-06-17'
GENERATION_CONFIG_JSON = {
    "temperature": 0.1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 4096,
    "response_mime_type": "application/json",
}


GENERATION_CONFIG_FOR_QA = {
    'temperature': 0.7,
    'top_p': 0.95,
    'top_k': 40,
    'max_output_tokens': 4096,
    'response_mime_type': 'application/json'
}

SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
]


# File Paths
INPUT_CSV_FILE = 'fpt_laptop_qa_cleaned.csv'
OUTPUT_DIR = "output"
OUTPUT_CSV_FILE = os.path.join(OUTPUT_DIR, "processed_qa_with_intents.csv")
LOG_FILE = os.path.join(OUTPUT_DIR, "processing_log.log")
PROCESSED_QUESTIONS_TRACKING_FILE = OUTPUT_CSV_FILE # Can be others


# Laptop info for QA generator
LAPTOP_INFO_FILT_PATH = 'general_info_cleaned.csv'
NUM_QUESTIONS_TO_GENERATE = 2000
GENERATED_QA_OUTPUT_FILE = os.path.join(OUTPUT_DIR, 'generated_training_question.csv')



# Processing Setting
QUESTION_COLUMN_NAME = "content"
API_CALL_DELAY_SECONDS = 2
MAX_RETRIES_API_CALL = 3

# Intent Definition
# Define intents and keywords to provide additional context for the LLM
# The LLM will be instructed to classify on its own, but including this list in the prompt may be helpful
INTENT_DEFINITIONS = {
    "recommend_budget": {
        "id": 0,
        "description_vi": "Gợi ý theo ngân sách",
        "keywords_vi": ["tầm giá", "ngân sách", "bao nhiêu tiền", "dưới", "khoảng", "triệu", "giá bao nhiêu", "tài chính"]
    },
    "recommend_usage": {
        "id": 1,
        "description_vi": "Gợi ý theo nhu cầu sử dụng",
        "keywords_vi": ["học tập", "đồ họa", "chơi game", "lập trình", "thiết kế", "chỉnh sửa video", "công nghệ thông tin", "marketing", "kế toán", "kỹ thuật", "dựng phim", "autocad", "solidworks", "photoshop", "adobe", "canva", "truyền thông", "văn phòng", "cơ bản", "giải trí"]
    },
    "tech_detail": {
        "id": 2,
        "description_vi": "Thông số kỹ thuật",
        "keywords_vi": ["chip", "CPU", "GPU", "card rời", "card tích hợp", "RAM", "SSD", "màn hình", "tần số quét", "Hz", "sRGB", "độ sáng", "nit", "bàn phím", "đèn bàn phím", "RGB", "độ sáng bàn phím", "đổi màu", "tùy chỉnh đèn", "đèn RGB", "cổng", "USB", "Type-C", "Thunderbolt", "DisplayPort", "độ phân giải", "2K", "4K", "pin", "cell", "vỏ nhựa", "vỏ kim loại", "trọng lượng", "M1", "M2", "M3", "M4", "sản xuất", "ra mắt", "năm nào", "xuất xứ", "hàng mới", "nguyên seal", "nội địa", "xách tay", "bản quyền", "Windows", "Office", "Microsoft", "hệ điều hành", "macOS", "Linux", "Windows 10", "Windows 11", "cài đặt", "cập nhật", "phiên bản", "màu sắc", "màu xám", "màu bạc", "màu đen", "màu vàng", "sẵn hàng", "trưng bày", "nâng cấp", "RAM", "SSD", "ổ cứng", "HDD", "dung lượng", "16GB", "32GB", "1TB", "khe cắm", "thay RAM", "lắp thêm", "giá nâng cấp", "tản nhiệt", "quạt"]
    },
    'other': {
        "id": -1,
        "description_vi": "Câu hỏi không phù hợp hoặc loại khác"
    }
    
}

# Log Configuration
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'detailed': {
            'format': '%(asctime)s - %(levelname)s - %(name)s - %(module)s.%(funcName)s:%(lineno)d - %(message)s'
        },
        'simple': {
            'format': '%(asctime)s - %(levelname)s - %(message)s'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': 'simple',
            'stream': 'ext://sys.stdout',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'DEBUG', # Ghi log chi tiết hơn vào file
            'formatter': 'detailed',
            'filename': LOG_FILE,
            'maxBytes': 1024*1024*5, # 5 MB
            'backupCount': 3,
            'encoding': 'utf-8',
        }
    },
    'root': { # Cấu hình cho root logger
        'handlers': ['console', 'file'],
        'level': 'DEBUG', # Mức log thấp nhất cho root, các handler sẽ lọc theo level của riêng chúng
    },
     'loggers': { # Cấu hình cho các logger cụ thể nếu cần
        'my_app': { # Ví dụ: logger cho ứng dụng của bạn
            'handlers': ['console', 'file'],
            'level': 'INFO', # Chỉ ghi INFO và cao hơn cho logger này
            'propagate': False # Không truyền log lên root logger nữa nếu đã xử lý ở đây
        }
    }
}