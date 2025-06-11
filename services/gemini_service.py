import google.generativeai as genai
import logging
from dotenv import load_dotenv

class GeminiService:
    def __init__(self, api_key):
        self.model = None
        self.chat = None
        self.logger = logging.getLogger(__name__)
        load_dotenv()
        self._initialize(api_key)

    def _initialize(self, api_key):
        try:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('models/gemini-1.5-flash')
            self.chat = self.model.start_chat(history=[])
            self.logger.info("Gemini service initialized successfully with Gemini 1.5 Flash")
        except Exception as e:
            self.logger.error(f"Error initializing Gemini service: {str(e)}")
            self.model = None
            self.chat = None

    def send_message(self, message):
        if not self.model or not self.chat:
            self.logger.error("Gemini model or chat not initialized")
            return "AI service is not properly initialized. Please check the configuration."
        try:
            response = self.chat.send_message(message)
            return response.text
        except Exception as e:
            self.logger.error(f"Error in chat: {str(e)}")
            return "I apologize, but I'm having trouble processing your request right now. Please try again later." 