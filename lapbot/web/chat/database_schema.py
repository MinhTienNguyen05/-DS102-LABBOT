import json
from django.db import OperationalError
from django.db.models import Min, Max, Avg, Count
from .models import LaptopInfo

# Phân chia categorical và numeric với toàn bộ columns
ALL_CATEGORICAL_FEATURES = ['manufacturer', 'cpu_brand', 'material', 'os_version', 'laptop_color', 'vga_brand', 
                        'cpu_model', 'vga_type', 'cpu_series', 'laptop_camera', 'ram_type']
ALL_CATEGORICAL_LABEL_FEATURES = ['cam_ung', 'laptop_sang_tao_noi_dung', 'do_hoa_ky_thuat', 'cao_cap_sang_trong', 
                                  'hoc_tap_van_phong', 'mong_nhe', 'gaming']
ALL_NUMERIC_FEATURES = ['storage_max_support', 'storage_gb', 'display_width', 'cpu_threads', 'cpu_cores', 
                    'ram_speed', 'cpu_speed', 'ram_storage', 'ram_slots', 'battery_capacity', 'display_height',
                    'height_mm', 'cpu_max_speed', 'root_price', 'product_weight', 'refresh_rate', 'depth_mm', 
                    'vga_vram', 'display_size']
ALL_BOTH_CATE_NUMERIC = [*ALL_CATEGORICAL_FEATURES, *ALL_CATEGORICAL_LABEL_FEATURES, *ALL_NUMERIC_FEATURES]

# Phân chia categorical và numeric với các columns cần dùng để predict
PREDICT_CATEGORICAL_FEATURES = ['manufacturer', 'cpu_brand', 'material', 'os_version', 'laptop_color', 'vga_brand',
                                'laptop_camera', 'ram_type']
PREDICT_CATEGORICAL_LABEL_FEATURES = ['laptop_sang_tao_noi_dung', 'do_hoa_ky_thuat', 'cao_cap_sang_trong']
PREDICT_NUMERIC_FEATURES = ['storage_max_support', 'storage_gb', 'display_width', 'cpu_threads', 'cpu_cores', 
                            'ram_speed', 'cpu_speed', 'ram_storage', 'ram_slots', 'battery_capacity', 'display_height']
PREDICT_BOTH_CATE_NUMERIC = [*PREDICT_CATEGORICAL_FEATURES, *PREDICT_CATEGORICAL_LABEL_FEATURES, *PREDICT_NUMERIC_FEATURES]

DATABASE_SCHEMA_CONTEXT = ""

def get_database_schema_and_choices():
    global DATABASE_SCHEMA_CONTEXT, ALL_CATEGORICAL_FEATURES, ALL_CATEGORICAL_LABEL_FEATURES, ALL_NUMERIC_FEATURES

    # --- Categorical Features ---
    # Các choices bây giờ được cung cấp bởi hàm get_distinct_choices

    schema_data = {"categorical": {}, "numerical": {}}

    try:
        # --- 1. Xử lý Categorical Features ---
        print("Generating schema for CATEGORICAL features...")
        for feature in ALL_CATEGORICAL_FEATURES:
            if feature in ALL_CATEGORICAL_LABEL_FEATURES:
                values = [0, 1]
            else:
                values = list(
                    LaptopInfo.objects.values_list(feature, flat=True)
                    .distinct()
                    .exclude(**{f'{feature}__isnull': True})
                    .exclude(**{f'{feature}__exact': ''})
                )

            schema_data['categorical'][feature] = values
        
        # --- 2. Xử lý Numerical Features (Hiệu quả hơn) ---
        print("Generating schema for NUMERICAL features...")
        # Xây dựng một dictionary các phép tính tổng hợp để chạy trong MỘT query duy nhất
        aggregations = {}
        for feature in ALL_NUMERIC_FEATURES:
            aggregations[f'{feature}__min'] = Min(feature)
            aggregations[f'{feature}__max'] = Max(feature)

        # Thực thi một query duy nhất để lấy tất cả min/max
        results = LaptopInfo.objects.aggregate(**aggregations)

        for feature in ALL_NUMERIC_FEATURES:
            min_val = results.get(f'{feature}__min')
            max_val = results.get(f'{feature}__max')
            schema_data['numerical'][feature] = {
                'min': float(min_val) if min_val is not None else None,
                'max': float(max_val) if max_val is not None else None
            }
    
        # --- 3. Định dạng Schema thành một chuỗi dễ đọc cho LLM ---
        schema_string_parts = []
        
        schema_string_parts.append("## Các trường Phân loại (Categorical):")
        for feature, values in schema_data['categorical'].items():
            schema_string_parts.append(f"- {feature}: {values}")

        schema_string_parts.append("\n## Các trường Số (Numerical):")
        for feature, ranges in schema_data['numerical'].items():
            schema_string_parts.append(f"- {feature}: (Phạm vi từ {ranges['min']} đến {ranges['max']})")
        
        # Gán kết quả vào biến toàn cục
        DATABASE_SCHEMA_CONTEXT = "\n".join(schema_string_parts)
        print("Database schema context for LLM has been generated and cached.")
        
    except OperationalError:
        print("Warning: Could not connect to DB to generate schema. This is normal during first migration.")
        DATABASE_SCHEMA_CONTEXT = "Lỗi: Không thể tải schema từ cơ sở dữ liệu."