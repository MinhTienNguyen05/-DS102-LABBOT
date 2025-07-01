import joblib
import pandas as pd
from django.db.models import Avg, Count
from .models import LaptopInfo

def calculate_default_values():
    categorical_features = ['manufacturer', 'cpu_brand', 'material', 'os_version', 'laptop_color', 'vga_brand',
            'laptop_camera', 'ram_type', 'laptop_sang_tao_noi_dung', 'do_hoa_ky_thuat', 'cao_cap_sang_trong']
    numeric_features = ['storage_max_support', 'storage_gb', 'display_width', 'cpu_threads', 'cpu_cores', 
                    'ram_speed', 'cpu_speed', 'ram_storage', 'ram_slots', 'battery_capacity', 'display_height']
    
    """
    Sử dụng Django ORM để tính toán giá trị mặc định (mean/mode)
    cho tất cả các feature từ database.
    """
    default = {}
    print("Calculating default imputation values from database...")

    # 1. Xử lý các trường số (Numeric Features) - Tính Mean (Trung bình)
    for feature in numeric_features:
        # Sử dụng aggregation của Django để tính trung bình, bỏ qua giá trị NULL
        # Coalesce(Avg(feature), 0.0) sẽ trả về 0.0 nếu tất cả giá trị đều là NULL
        result = LaptopInfo.objects.aggregate(avg_value=Avg(feature))
        mean_value = result.get('avg_value')
        # Làm tròn để giá trị đẹp hơn và gán giá trị mặc định nếu là None
        default[feature] = round(mean_value, 2) if mean_value is not None else 0
        print(f"  - Calculated mean for '{feature}': {default[feature]}")
    
    # 2. Xử lý các trường phân loại (Categorical Features) - Tính Mode (Giá trị phổ biến nhất)
    for feature in categorical_features:
        if feature in ['laptop_sang_tao_noi_dung', 'do_hoa_ky_thuat', 'cao_cap_sang_trong']:
            default[feature] = 0
        else:
            mode_result = LaptopInfo.objects.values(feature)\
                                            .annotate(count=Count(feature))\
                                            .order_by('-count')\
                                            .first() # Lấy phần tử đầu tiên (phổ biến nhất)
            
            if mode_result:
                default[feature] = mode_result[feature]

        print(f"  - Calculated mode for '{feature}': {default[feature]}")
        
    print("Default values calculation complete.")
    return default


# Lớp này sẽ quản lý việc tải và sử dụng model (Singleton pattern)
class PricePredictor:
    def __init__(self, default_imputation_values):
        self.model = None
        self.load_model()
        self.default_imputation_values = default_imputation_values
        
    def load_model(self):
        """Tải model từ file .joblib vào bộ nhớ."""
        model_path = 'chat/model/best_model_xgb.joblib'
        try:
            self.model = joblib.load(model_path)
            print("ML Model loaded successfully!")
        except FileNotFoundError:
            print(f"Error: Model file not found at {model_path}")
            self.model = None

    def predict(self, input_data):
        """
        Thực hiện dự đoán dựa trên dữ liệu đầu vào.
        `input_data` nên là một dictionary.
        """
        if self.model is None:
            return "Model is not loaded."
        if not input_data:
            return "No data to predict"
        
        try:
            data = self.default_imputation_values.copy()
            data.update(input_data)

            # ----- QUAN TRỌNG NHẤT ------
            # Dữ liệu đầu vào phải được chuyển đổi thành định dạng mà model mong đợi.
            # Thường là một Pandas DataFrame với các cột và thứ tự chính xác.
            fields = ['storage_max_support', 'storage_gb', 'display_width', 'cpu_threads', 'cpu_cores', 
                    'ram_speed', 'cpu_speed', 'ram_storage', 'ram_slots', 'battery_capacity', 
                    'display_height', 'laptop_sang_tao_noi_dung', 'do_hoa_ky_thuat', 'cao_cap_sang_trong', 
                    'material', 'manufacturer', 'ram_type', 'os_version', 'laptop_color', 'vga_brand', 'laptop_camera', 'cpu_brand']
            
            input_df = pd.DataFrame([data], columns=fields)

            prediction = self.model.predict(input_df)
            return {
                'data': data,
                'predict_price': prediction[0]
            }

        except Exception as e:
            return f"Error: {e}"