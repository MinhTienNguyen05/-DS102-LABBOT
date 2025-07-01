from django.apps import AppConfig
import os

class ChatConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'chat'

    def ready(self):
        # Import service ở đây để đảm bảo model được tải khi server khởi động
        from . import predictor_service
        predictor_service.default_imputation_values = predictor_service.calculate_default_values()
        predictor_service.predictor = predictor_service.PricePredictor(predictor_service.default_imputation_values)
        print("Importing predictor service to load ML model...")

        from . import intent_classifier
        intent_classifier.classifier = intent_classifier.IntentClassifier()

        from . import llms_service
        llms_service.llms = llms_service.get_llm_service('gemini-2.5-flash')
        print("Connect to LLMs...")

        from . import database_schema
        database_schema.get_database_schema_and_choices()