from together import Together
from google import genai
import dotenv
import os
import abc  # Abstract Base Classes

dotenv.load_dotenv()

# ==============================================================================
# 1. LỚP CƠ SỞ TRỪU TƯỢNG (BASE CLASS)
# ==============================================================================
class BaseLLMService(abc.ABC):
    """
    Lớp cơ sở trừu tượng định nghĩa giao diện chung cho tất cả các dịch vụ LLM.
    Mọi class LLM service khác phải kế thừa từ lớp này và triển khai
    phương thức `invoke`.
    """

    def __init__(self, model_name: str, temperature: float = 0.0, **kwargs):
        """
        Khởi tạo với các tham số chung.
        :param model_name: Tên của model cụ thể để sử dụng.
        :param temperature: Độ "sáng tạo" của model.
        :param kwargs: Các tham số khác dành riêng cho từng dịch vụ.
        """
        self.model_name = model_name
        self.temperature = temperature
        self.client = self._initialize_client(**kwargs)

    @abc.abstractmethod
    def _initialize_client(self, **kwargs):
        """
        Phương thức trừu tượng để khởi tạo client API của nhà cung cấp.
        Lớp con phải triển khai phương thức này.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def invoke(self, system_prompt: str, user_prompt: str) -> str:
        """
        Phương thức chính để gửi yêu cầu đến LLM và nhận lại phản hồi.
        Lớp con phải triển khai phương thức này.
        :param system_prompt: Chỉ dẫn hệ thống cho model.
        :param user_prompt: Câu hỏi hoặc yêu cầu từ người dùng.
        :return: Chuỗi văn bản phản hồi từ LLM.
        """
        raise NotImplementedError

    def _format_prompt(self, system_prompt: str, user_prompt: str) -> list:
        """
        Một hàm trợ giúp để định dạng prompt theo cấu trúc chung.
        Lớp con có thể ghi đè (override) nếu cần định dạng khác.
        """
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]



# ==============================================================================
# 2. CÁC LỚP CON TRIỂN KHAI (CONCRETE CLASSES)
# ==============================================================================

# --- Dịch vụ cho TogetherAI ---
class TogetherLLMService(BaseLLMService):
    """Triển khai LLM Service cho TogetherAI."""

    def _initialize_client(self, **kwargs):
        api_key = os.getenv("TOGETHER_API_KEY")

        if not api_key:
            raise ValueError("TOGETHER_API_KEY không được tìm thấy trong biến môi trường.")
        
        return Together(api_key=api_key)

    def invoke(self, system_prompt: str, user_prompt: str) -> str:
        messages = self._format_prompt(system_prompt, user_prompt)

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=self.temperature
            )

            return response.choices[0].message.content
        
        except Exception as e:
            print(f"Error calling TogetherAI API: {e}")
            return "Xin lỗi, đã có lỗi xảy ra khi kết nối đến dịch vụ AI. Vui lòng thử lại sau."


# --- Dịch vụ cho Google Gemini ---
class GeminiLLMService(BaseLLMService):
    """Triển khai LLM Service cho Google Gemini."""

    def _initialize_client(self, **kwargs):
        api_key = os.getenv("GOOGLE_API_KEY")

        if not api_key:
            raise ValueError("GOOGLE_API_KEY không được tìm thấy trong biến môi trường.")

        return genai.Client(api_key=api_key)

    def invoke(self, system_prompt: str, user_prompt: str) -> str:
        messages = self._format_prompt(system_prompt, user_prompt)

        try:
            response = self.client.models.generate_content(
                model=self.model_name, 
                contents=messages
            )

            return response.text
        
        except Exception as e: 
            print(f"Error calling Gemini API: {e}")
            return "Lỗi khi kết nối đến Gemini."

    def _format_prompt(self, system_prompt, user_prompt):
        return f'''
            System Prompt: \n{system_prompt}\n
            User Input: \n{user_prompt}
        '''
    

# ==============================================================================
# 3. HÀM NHÀ MÁY (FACTORY FUNCTION)
# ==============================================================================
_llm_services = {
    "together": TogetherLLMService,
    "gemini": GeminiLLMService,
    # Thêm các dịch vụ khác ở đây
    # "openai": OpenAILLMService,
}

_llm_models = {
    # Định nghĩa các model muốn sử dụng và chúng thuộc dịch vụ nào
    "llama3-70b-instruct": ("together", "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free"),
    "gemini-2.5-flash": ("gemini", "gemini-2.5-flash-preview-05-20"),
}

def get_llm_service(model_alias: str, **kwargs) -> BaseLLMService:
    f"""
    Lấy một instance của LLM service dựa trên một tên định danh (alias).
    :param model_alias: Tên định danh của model, ví dụ {_llm_models.keys()}.
    :return: Một instance của class con kế thừa từ BaseLLMService.
    """

    if model_alias not in _llm_models:
        raise ValueError(f"Model alias '{model_alias}' không được hỗ trợ. Các lựa chọn: {list(_llm_models.keys())}")
    
    service_name, model_name = _llm_models[model_alias]
    
    if service_name not in _llm_services:
        raise ValueError(f"Service '{service_name}' không được định nghĩa.")
    
    ServiceClass = _llm_services[service_name]

    # Khởi tạo và trả về instance
    return ServiceClass(model_name=model_name, **kwargs)