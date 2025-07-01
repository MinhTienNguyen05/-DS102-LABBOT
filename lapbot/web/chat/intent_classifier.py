import joblib

class IntentClassifier:
    def __init__(self):
        self.model = None
        self.load_model()
    
    def load_model(self):
        """Tải model từ file .joblib vào bộ nhớ."""
        model_path = 'chat/model/best_intent_classifier.joblib'
        try:
            self.model = joblib.load(model_path)
            print("ML Model loaded successfully!")
        except FileNotFoundError:
            print(f"Error: Model file not found at {model_path}")
            self.model = None
    
    def classifier(self, input_question):
        """Thực hiện phân loại intent câu hỏi"""

        if self.model is None:
            return "Model is not loaded."
        if not input_question:
            return "No data to predict"
        
        try:
            result = self.model.predict([input_question])
            return result[0]

        except Exception as e:
            return f"Error: {e}"
    
