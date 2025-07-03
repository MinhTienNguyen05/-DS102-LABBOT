from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.forms.models import model_to_dict
from django.conf import settings # Import settings
from chat.models import LaptopInfo
import json
import re
import requests
import markdown
from .predictor_service import predictor # Import instance đã được tải sẵn trong apps
from .intent_classifier import classifier
from .llms_service import llms
from .form_predict import LaptopPredictionFeaturesForm
from .prompts import SYSTEM_CONTENT_USER_MESS_EXTRACT_AND_GEN_GROUP, SYSTEM_CONTENT_EXTRACT_BUDGET, SYSTEM_CONTENT_EXTRACT_RECOMMEND_USAGE
from urllib.parse import urljoin

# API
# Lấy base URL từ settings
api_base_url = settings.INTERNAL_API_BASE_URL

# Markdown
md = markdown.Markdown(extensions=["fenced_code"])

def extract_json_from_string(text: str) -> str | None:
    """
    Trích xuất chuỗi JSON từ bên trong một khối mã Markdown.
    """
    # Regex tương tự, nhưng không có dấu / ở đầu và cuối
    # re.DOTALL cho phép `.` khớp với cả ký tự xuống dòng, tương đương [\s\S]
    pattern = r"```(?:json)?\s*(.*?)\s*```"
    
    match = re.search(pattern, text, re.DOTALL)
    
    if match:
        # group(1) là capturing group đầu tiên
        return match.group(1).strip()
    
    # Nếu không tìm thấy, trả về chuỗi gốc để thử parse
    return text.strip()

def change_usage_alias(suggested_laptops):
    usage_keys = [
        'laptop_sang_tao_noi_dung', 'do_hoa_ky_thuat', 'cao_cap_sang_trong', 
        'hoc_tap_van_phong', 'mong_nhe', 'gaming'
    ]

    usage_keys_alias = {
        'laptop_sang_tao_noi_dung': 'Sáng tạo nội dung',
        'do_hoa_ky_thuat': 'Đồ họa - Kỹ thuật',
        'cao_cap_sang_trong': 'Cao cấp - Sang trọng',
        'hoc_tap_van_phong': 'Học tập - Văn phòng',
        'mong_nhe': 'Mỏng nhẹ',
        'gaming': 'Gaming'
    }

    for idx, laptop in enumerate(suggested_laptops):
        suggested_laptops[idx]['usage_needs'] = [usage_keys_alias[key] for key in usage_keys if laptop.get(key, 0) == 1]

        # (Tùy chọn) Xóa các key cũ để làm sạch output
        for key_to_remove in usage_keys:
            suggested_laptops[idx].pop(key_to_remove, None) # .pop(key, None) sẽ không báo lỗi nếu key không tồn tại
    
    return suggested_laptops

# VIEW 
@csrf_exempt
def index(request):
    """
    Hiển thị trang chat chính.
    """ 
    # Khởi tạo nếu chưa có
    chat_history = request.session.get('chat_history', [])

    return render(request, 'chat/index.html', {
        'chat_history': chat_history
    })

@csrf_exempt
def intent_detect(request):
    """
    Model trả về intent message của người dùng để phân cách trả lời
    """
    # intent_type = {
    #     0: 'intent_recommend_budget',
    #     1: 'intent_recommend_usage',
    #     2: 'intent_tech_detail'
    # }
    intent_type = {
        0: 'Ngân sách',
        1: 'Nhu cầu sử dụng',
        2: 'Thông số kỹ thuật'
    }

    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            user_message = data.get('user_message', '')

            # intent = int(llms.invoke(SYSTEM_CONTENT_INTENT_DETECT, user_message))

            # return JsonResponse({
            #     'data_intent': {
            #         'intent_code': intent,
            #         'intent_meaning': intent_type[intent]
            #     }
            # })

            intent = classifier.classifier(user_message) # trả về dạng [0 0 0]
            print(intent)

            data_intent = []
            for idx in range(len(intent)):
                if intent[idx] == 1:
                    data_intent.append({
                        'intent_code': idx,
                        'intent_meaning': intent_type[idx]
                    })
            
            print('INTENT: ', data_intent)
                
            return JsonResponse({
                'data': data_intent
            })

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON format'}, status=400)
        except Exception as e:
            print(f"Error processing message: {e}")
            return JsonResponse({'error': 'An internal server error occurred'}, status=500)

    else:
        return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)

@csrf_exempt
def send_message(request):
    """
    Xử lý tin nhắn từ người dùng (gửi qua AJAX POST request).
    Lấy phản hồi từ bot và trả về dưới dạng JSON.

    Câu trả lời theo từng intent :
    - Với 1 intent duy nhất :
        + budget : 
        + usage : 
        + detail : 
    - Với 2 intent :
        + budget + usage : 
        + budget + detail :
        + usage + detail :
    - Với 3 intent : 
        + budget + usage + detail : 
    """
    if request.method == 'POST':
        try:
            # Lấy dữ liệu JSON từ body của request
            # Cần đảm bảo client gửi Content-Type: application/json
            data = json.loads(request.body.decode('utf-8'))
            user_message = data.get('user_message', '')

            if not user_message:
                return JsonResponse({
                    'status': 400,
                    'error': 'Message cannot be empty!'
                }, status=400)

            intent_detect_url = urljoin(api_base_url, '/chat/intent_detect/')
            try:
                resp = requests.post(intent_detect_url, json=data)
                resp.raise_for_status() 
                data = resp.json()  
                intent = data.get('data')  # list intent
                print(intent)
            except Exception as e:
                print(f"Error calling send_message API: {e}")   
                raise e
            # intent = [{
            #             'intent_code': 1,
            #             'intent_meaning': '.....'
            #         },
            #         {
            #             'intent_code': 2,
            #             'intent_meaning': '.....'
            #         }]
            intent_codes = [one_intent['intent_code'] for one_intent in intent]
            # intent_codes = [1, 2]
            match len(intent_codes):
                case 1: # Trường hợp có duy nhất 1
                    if intent_codes[0] == 0: 
                        response = llms.invoke(SYSTEM_CONTENT_EXTRACT_BUDGET, user_message)
                        response = extract_json_from_string(response)
                        response = json.loads(response) 

                        min_price = response['budget_min']
                        max_price = response['budget_max']
                        
                        filters = {
                            'discounted_price__gte': min_price,
                            'discounted_price__lte': max_price
                        }

                        if min_price == max_price:
                            filters['discounted_price__gte'] = min_price - 2000000 # 2tr
                            filters['discounted_price__lte'] = max_price + 2000000 # 2tr
                        if not min_price:
                            filters['discounted_price__gte'] = max_price - 10000000 # range 10tr
                        if not max_price:
                            filters['discounted_price__lte'] = min_price + 10000000 # range 10tr

                        try:
                            laptop_filters = LaptopInfo.objects.filter(**filters)\
                                                                    .values('url_path', 'image', 'root_price', 'discounted_price', 'name', 
                                                                            'laptop_sang_tao_noi_dung', 'do_hoa_ky_thuat', 'cao_cap_sang_trong', 
                                                                            'hoc_tap_van_phong', 'mong_nhe', 'gaming')\
                                                                    .order_by('discounted_price')
                            suggested_laptops = list(laptop_filters)
                            suggested_laptops = change_usage_alias(suggested_laptops) # Thay đổi lại tên từ vd mong_nhe sang Mỏng nhẹ
                        except Exception as e: 
                            # Bắt các lỗi có thể xảy ra do filter không hợp lệ
                            print(f"Lỗi khi thực thi filter cho persona '{persona}': {e}")
                            suggested_laptops = []

                        data_result = {
                            'min_price': filters['discounted_price__gte'],
                            'max_price': filters['discounted_price__lte'],
                            'suggested_laptops': suggested_laptops
                        }

                        return JsonResponse({
                            'data': {
                                'intent_codes': [one_intent['intent_code'] for one_intent in intent],
                                'intent_meanings': [one_intent['intent_meaning'] for one_intent in intent],
                                'user_message': user_message,
                                'ai_response': data_result
                            }
                        }, status=200)
                    
                    if intent_codes[0] == 1:
                        response = llms.invoke(SYSTEM_CONTENT_EXTRACT_RECOMMEND_USAGE, user_message)
                        response = extract_json_from_string(response)
                        response = json.loads(response) 
                        print(response)

                        # raise ValueError('STOP FOR TESTING')
                        data_result = {}

                        persona = response.get("persona", None)
                        filters = response.get("filters", {})

                        if (not persona) or (not filters):
                            raise ValueError('Không tìm được persona, hoặc không có giá trị filters.')
                        
                        try:
                            # Dùng **filters để "giải nén" dictionary thành các tham số cho .filter()
                            laptop_filters = LaptopInfo.objects.filter(**filters)\
                                                                    .values('url_path', 'image', 'root_price', 'discounted_price', 'name', 
                                                                            'laptop_sang_tao_noi_dung', 'do_hoa_ky_thuat', 'cao_cap_sang_trong', 
                                                                            'hoc_tap_van_phong', 'mong_nhe', 'gaming')\
                                                                    .order_by('discounted_price')
                            suggested_laptops = list(laptop_filters)
                            suggested_laptops = change_usage_alias(suggested_laptops) # Thay đổi lại tên từ vd mong_nhe sang Mỏng nhẹ
                            
                        except Exception as e:
                            # Bắt các lỗi có thể xảy ra do filter không hợp lệ
                            print(f"Lỗi khi thực thi filter cho persona '{persona}': {e}")
                            suggested_laptops = []
                        
                        data_result['persona'] = persona
                        data_result['suggested_laptops'] = suggested_laptops

                        return JsonResponse({
                            'data': {
                                'intent_codes': [one_intent['intent_code'] for one_intent in intent],
                                'intent_meanings': [one_intent['intent_meaning'] for one_intent in intent],
                                'user_message': user_message,
                                'ai_response': data_result
                            }
                        }, status=200)
                    
                    if intent_codes[0] == 2:
                        response = llms.invoke(SYSTEM_CONTENT_USER_MESS_EXTRACT_AND_GEN_GROUP, user_message)
                        print(response)
                        response = extract_json_from_string(response)
                        response = json.loads(response) # Chuyển về dict
                        data_result = []

                        predict_price_url = urljoin(api_base_url, '/chat/predict_price/')

                        for item in response:
                            recommendation = {}

                            persona = item.get("persona", None)
                            filters = item.get("filters", {})

                            if (not persona) or (not filters):
                                continue

                            try:
                                resp = requests.post(predict_price_url, json={
                                    'data': item['prediction_profile']
                                })
                                resp.raise_for_status() 
                                data = resp.json()  
                                predict_price = data.get('predict_price')  # dict chứa intent_code, intent_meaning
                            except Exception as e:
                                print(f"Error calling predict price API: {e}")   
                                raise e
                            
                            # Nếu có giá dự đoán hợp lệ, thêm điều kiện lọc theo giá
                            if predict_price is not None:
                                price_range = 5000000  # 5 triệu đồng
                                
                                # Thêm điều kiện giá vào dictionary `filters`
                                filters['discounted_price__gte'] = predict_price - price_range
                                filters['discounted_price__lte'] = predict_price + price_range
                                
                                # Đảm bảo giá không bị âm
                                if filters['discounted_price__gte'] < 0:
                                    filters['discounted_price__gte'] = 0
                            print('FILTER: ', filters)
                            try:
                                # Dùng **filters để "giải nén" dictionary thành các tham số cho .filter()
                                laptop_filters = LaptopInfo.objects.filter(**filters)\
                                                                        .values('url_path', 'image', 'root_price', 'discounted_price', 'name', 
                                                                                'laptop_sang_tao_noi_dung', 'do_hoa_ky_thuat', 'cao_cap_sang_trong', 
                                                                                'hoc_tap_van_phong', 'mong_nhe', 'gaming')\
                                                                        .order_by('discounted_price')
                                suggested_laptops = list(laptop_filters)
                                suggested_laptops = change_usage_alias(suggested_laptops) # Thay đổi lại tên từ vd mong_nhe sang Mỏng nhẹ
                                
                            except Exception as e:
                                # Bắt các lỗi có thể xảy ra do filter không hợp lệ
                                print(f"Lỗi khi thực thi filter cho persona '{persona}': {e}")
                                suggested_laptops = []
                            
                            recommendation['persona'] = persona
                            recommendation['general_price'] = predict_price
                            recommendation['suggested_laptops'] = suggested_laptops

                            data_result.append(recommendation)

                        return JsonResponse({
                            'data': {
                                'intent_codes': [one_intent['intent_code'] for one_intent in intent],
                                'intent_meanings': [one_intent['intent_meaning'] for one_intent in intent],
                                'user_message': user_message,
                                'ai_response': data_result
                            }
                        }, status=200)

                case 2 | 3:
                    response = llms.invoke(SYSTEM_CONTENT_USER_MESS_EXTRACT_AND_GEN_GROUP, user_message)
                    print(response)
                    response = extract_json_from_string(response)
                    response = json.loads(response) # Chuyển về dict
                    data_result = []
                    print('COME HERE???')

                    predict_price_url = urljoin(api_base_url, '/chat/predict_price/')

                    for item in response:
                        recommendation = {}

                        persona = item.get("persona", None)
                        filters = item.get("filters", {})

                        if (not persona) or (not filters):
                            continue

                        try:
                            resp = requests.post(predict_price_url, json={
                                'data': item['prediction_profile']
                            })
                            resp.raise_for_status() 
                            data = resp.json()  
                            predict_price = data.get('predict_price')  # dict chứa intent_code, intent_meaning
                        except Exception as e:
                            print(f"Error calling predict price API: {e}")   
                            raise e
                        
                        # Nếu có giá dự đoán hợp lệ, thêm điều kiện lọc theo giá
                        if predict_price is not None:
                            price_range = 5000000  # 5 triệu đồng
                            
                            # Thêm điều kiện giá vào dictionary `filters`
                            filters['discounted_price__gte'] = predict_price - price_range
                            filters['discounted_price__lte'] = predict_price + price_range
                            
                            # Đảm bảo giá không bị âm
                            if filters['discounted_price__gte'] < 0:
                                filters['discounted_price__gte'] = 0
                        
                        try:
                            # Dùng **filters để "giải nén" dictionary thành các tham số cho .filter()
                            laptop_filters = LaptopInfo.objects.filter(**filters)\
                                                                    .values('url_path', 'image', 'root_price', 'discounted_price', 'name', 
                                                                            'laptop_sang_tao_noi_dung', 'do_hoa_ky_thuat', 'cao_cap_sang_trong', 
                                                                            'hoc_tap_van_phong', 'mong_nhe', 'gaming')\
                                                                    .order_by('discounted_price')
                            suggested_laptops = list(laptop_filters)
                            suggested_laptops = change_usage_alias(suggested_laptops) # Thay đổi lại tên từ vd mong_nhe sang Mỏng nhẹ
                            
                        except Exception as e:
                            # Bắt các lỗi có thể xảy ra do filter không hợp lệ
                            print(f"Lỗi khi thực thi filter cho persona '{persona}': {e}")
                            suggested_laptops = []
                        
                        recommendation['persona'] = persona
                        recommendation['general_price'] = predict_price
                        recommendation['suggested_laptops'] = suggested_laptops

                        data_result.append(recommendation)

                    return JsonResponse({
                        'data': {
                            'intent_codes': [one_intent['intent_code'] for one_intent in intent],
                            'intent_meanings': [one_intent['intent_meaning'] for one_intent in intent],
                            'user_message': user_message,
                            'ai_response': data_result
                        }
                    }, status=200)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON format'}, status=400)
        
        except Exception as e:
            print(f"Error processing message: {e}")
            return JsonResponse({'error': 'An internal server error occurred'}, status=500)
        
    else:
        return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)
    

@csrf_exempt
def user_message_html(request):
    if request.method == 'POST':
        try:
            # Lấy dữ liệu JSON từ body của request
            # Cần đảm bảo client gửi Content-Type: application/json
            data = json.loads(request.body.decode('utf-8'))
            data = data.get('data', '')
            user_message = data.get('user_message', '')

            if not user_message:
                return JsonResponse({
                    'status': 400,
                    'error': 'Message cannot be empty!'
                }, status=400)
            
            data_md_converted = {
                "user_message": md.convert(user_message)
            }

            chat_block_html = render_to_string('components/message/user_message.html', {
                "data": data_md_converted
            })

            return JsonResponse({"html": chat_block_html})
        
        except Exception as e:
            print(f"Error processing message: {e}")
            return JsonResponse({'error': 'An internal server error occurred'}, status=500)
    else:
        return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)
    

@csrf_exempt
def ai_message_html(request):
    if request.method == 'POST':
        chat_history = request.session.get('chat_history', [])

        try:
            # Lấy dữ liệu JSON từ body của request
            # Cần đảm bảo client gửi Content-Type: application/json
            data = json.loads(request.body.decode('utf-8'))
            data = data.get('data', '')
            user_message = data.get('user_message', '')

            if not user_message:
                return JsonResponse({
                    'status': 400,
                    'error': 'Message cannot be empty!'
                }, status=400)
            
            send_mess_url = urljoin(api_base_url, '/chat/send_message/')
            try:
                resp = requests.post(send_mess_url, json={
                    'user_message': user_message
                })
                resp.raise_for_status()  # Kiểm tra lỗi HTTP
                data = resp.json()       # Lấy dict JSON từ response
                response = data.get('data')  # Lấy phần data, thay đổi tùy response server
            except Exception as e:
                print(f"Error calling send_message API: {e}")   
                raise e
            
            # data_md_converted = {
            #     'intent_code': response['intent_code'],
            #     'intent_meaning': response['intent_meaning'],
            #     'user_message': md.convert(response['user_message']),
            #     'ai_response': response['ai_response'] if response['intent_code'] == 0 else md.convert(response['ai_response'])
            # }

            data_md_converted = {
                'intent_codes': response['intent_codes'],
                'intent_meanings': response['intent_meanings'],
                'user_message': md.convert(response['user_message']),
                'ai_response': response['ai_response']
            }

            chat_block_html = render_to_string('components/message/ai_message.html', {
                'data': data_md_converted
            })

            chat_history.append(data_md_converted)
            request.session['chat_history'] = chat_history
            request.session.modified = True 

            return JsonResponse({"html": chat_block_html})
        
        except Exception as e:
            print(f"Error processing message: {e}")
            return JsonResponse({'error': 'An internal server error occurred'}, status=500)
    else:
        return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)

@csrf_exempt
def delete_all_message(request):
    if request.method == 'POST':
        try:
            if 'chat_history' in request.session:
                del request.session['chat_history']  # Xóa session
                request.session.modified = True

            return JsonResponse({'status': 'Deleted all messages sucessfully!'}, status=200)
        
        except Exception as e:
            print(f"Error processing message: {e}")
            return JsonResponse({'error': 'An internal server error occurred'}, status=500)
    else:
        return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)

@csrf_exempt
def predict_price(request):
    if request.method == 'POST':

        try:
            data = json.loads(request.body.decode('utf-8'))
            data = data.get('data', '')

            if not data:
                return JsonResponse({
                    'status': 400,
                    'error': 'Data cannot be empty!'
                }, status=400)
            
            form = LaptopPredictionFeaturesForm(data)  

            if form.is_valid():
                print('PASS FORM VALID')
                cleaned_data = form.cleaned_data
                predict_result = predictor.predict(cleaned_data)
                print('COMPLETE PREDICT')
                # Kiểm tra xem service có trả về lỗi không
                if isinstance(predict_result, str) and ("Error" in predict_result):
                    return JsonResponse({'error': predict_result}, status=500)
                
                return JsonResponse({
                    'data': cleaned_data,
                    'predict_price': float(predict_result['predict_price'])
                }, status=200)
            else:
                return JsonResponse({'error': form.errors}, status=400)
            
        except Exception as e:
            print(f"Error processing message: {e}")
            return JsonResponse({'error': 'An internal server error occurred'}, status=500)
    else:
        return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)