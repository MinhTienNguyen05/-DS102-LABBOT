import os
import random
from django import template
from django.conf import settings
from django.templatetags.static import static
from pathlib import Path

# Tạo một instance của Library để đăng ký các tag
register = template.Library()

# Biến toàn cục để cache danh sách ảnh, tránh đọc lại file hệ thống mỗi lần render
_demo_image_list = []

@register.simple_tag
def random_demo_laptop_image():
    """
    Trả về đường dẫn static tới một ảnh ngẫu nhiên trong thư mục demo_laptops.
    Cache danh sách file để tăng hiệu năng.
    """
    global _demo_image_list

    # Nếu cache chưa có, hãy đọc file hệ thống một lần
    if not _demo_image_list:
        try:
            image_dir_path = Path('./static/global/img/laptop_img')

            image_extensions = {'.png', '.jpg', '.jpeg', '.webp', '.gif'}
            image_files = [f for f in image_dir_path.iterdir() if f.is_file() and f.suffix.lower() in image_extensions]

            # Lưu vào cache
            _demo_image_list = image_files
            print(f"Cached {len(_demo_image_list)} demo images.")

        except FileNotFoundError:
            # Nếu thư mục không tồn tại, trả về một ảnh mặc định để không crash
            print("Warning: Thư mục demo_laptops không được tìm thấy.")
            return static('global/img/laptop_img/laptop_demo.jpg') # Trả về ảnh mặc định của bạn
        except Exception as e:
            print(f"Lỗi khi đọc file ảnh demo: {e}")
            return static('global/img/laptop_img/laptop_demo.jpg')
    
    # Nếu cache đã có nhưng không có file nào, xử lý
    if not _demo_image_list:
        return static('global/img/laptop_img/laptop_demo.jpg')
    
    # Chọn ngẫu nhiên một tên file từ cache
    random_filename = random.choice(_demo_image_list)

    relative_static_path = f'global/img/laptop_img/{random_filename.name}'

    # Dùng hàm `static` của Django để có được URL cuối cùng
    return static(relative_static_path)