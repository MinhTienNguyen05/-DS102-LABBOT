from django import forms
from .models import LaptopInfo
from django.db import OperationalError

# ==============================================================================
# BƯỚC 1: TẠO HÀM TIỆN ÍCH ĐỂ TRUY VẤN DATABASE
# ==============================================================================
def get_distinct_choices(field_name):
    """
    Truy vấn database để lấy các giá trị unique (duy nhất) cho một trường cụ thể,
    và định dạng chúng thành dạng `choices` cho Django Form.
    Hàm này được thiết kế để chỉ chạy một lần khi server khởi động.
    """
    try:
        # Lấy danh sách các giá trị unique, loại bỏ các giá trị None hoặc rỗng
        values = LaptopInfo.objects.values_list(field_name, flat=True)\
                            .distinct()\
                            .exclude(**{f'{field_name}__isnull': True})\
                            .exclude(**{f'{field_name}__exact': ''})\
                            .order_by(field_name)
        
        # Chuyển danh sách thành định dạng choices: [(value, label), ...]
        choices = [(value, str(value)) for value in values]
        
    except OperationalError:
        # Xảy ra nếu database chưa sẵn sàng khi Django khởi động (ví dụ: lần đầu chạy migrate)
        # Trả về một list trống để tránh crash server.
        print(f"Warning: Could not connect to DB to get choices for '{field_name}'.")
        choices = []
    
    # Luôn thêm một lựa chọn trống ở đầu cho các trường không bắt buộc
    return [('', '---------')] + choices


# ==============================================================================
# BƯỚC 2: ĐỊNH NGHĨA FORM SỬ DỤNG HÀM TRUY VẤN
# Lưu ý: Các hàm get_distinct_choices() sẽ được gọi MỘT LẦN khi file này được import,
# tức là khi Django server khởi động.
# ==============================================================================
class LaptopPredictionFeaturesForm(forms.Form):
    """
    Form này dùng để xác thực (validate) dữ liệu đầu vào cho API dự đoán.
    Các lựa chọn (choices) được tải động từ database khi server khởi động.
    """
    categorical_features = ['manufacturer', 'cpu_brand', 'material', 'os_version', 'laptop_color', 'vga_brand',
                'laptop_camera', 'ram_type', 'laptop_sang_tao_noi_dung', 'do_hoa_ky_thuat', 'cao_cap_sang_trong']
    numeric_features = ['storage_max_support', 'storage_gb', 'display_width', 'cpu_threads', 'cpu_cores', 
                        'ram_speed', 'cpu_speed', 'ram_storage', 'ram_slots', 'battery_capacity', 'display_height']

    # --- Categorical Features ---
    # Các choices bây giờ được cung cấp bởi hàm get_distinct_choices
    manufacturer = forms.ChoiceField(choices=get_distinct_choices('manufacturer'), required=False, label="")
    cpu_brand = forms.ChoiceField(choices=get_distinct_choices('cpu_brand'), required=False, label="")
    material = forms.ChoiceField(choices=get_distinct_choices('material'), required=False, label="")
    os_version = forms.ChoiceField(choices=get_distinct_choices('os_version'), required=False, label="")
    laptop_color = forms.ChoiceField(choices=get_distinct_choices('laptop_color'), required=False, label="")
    vga_brand = forms.ChoiceField(choices=get_distinct_choices('vga_brand'), required=False, label="")
    laptop_camera = forms.ChoiceField(choices=get_distinct_choices('laptop_camera'), required=False, label="")
    ram_type = forms.ChoiceField(choices=get_distinct_choices('ram_type'), required=False, label="")
    
    # Các trường này có kiểu Integer trong DB, nên ta dùng IntegerField
    laptop_sang_tao_noi_dung = forms.ChoiceField(choices=[(0, 'Có'), (1, 'Không')], required=False, label="")
    do_hoa_ky_thuat = forms.ChoiceField(choices=[(0, 'Có'), (1, 'Không')], required=False, label="")
    cao_cap_sang_trong = forms.ChoiceField(choices=[(0, 'Có'), (1, 'Không')], required=False, label="")

    # --- Numeric Features ---
    storage_max_support = forms.FloatField(required=False, label="")
    storage_gb = forms.FloatField(required=False, label="")
    display_width = forms.FloatField(required=False, label="")
    cpu_threads = forms.FloatField(required=False, label="")
    cpu_cores = forms.FloatField(required=False, label="")
    cpu_speed = forms.FloatField(required=False, label="")
    ram_slots = forms.FloatField(required=False, label="")
    ram_speed = forms.FloatField(required=False, label="")
    ram_storage = forms.FloatField(required=False, label="")
    battery_capacity = forms.FloatField(required=False, label="")
    display_height = forms.FloatField(required=False, label="")

    