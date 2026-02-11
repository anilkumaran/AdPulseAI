import os
from abc import ABC, abstractmethod
from dotenv import load_dotenv
import google.generativeai as genai
from services.settings_service import get_settings_service

load_dotenv()

class BaseAdService(ABC):
    @abstractmethod
    def generate_response(self, product_info: str, voice: str) -> str:
        pass

class GeminiService(BaseAdService):
    def __init__(self):
        print("🚀 [System] Initializing REAL Gemini Service...")
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not set in environment variables.")
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel("gemini-1.5-flash")
        self.settings_svc = get_settings_service()

    def generate_response(self, product_info: str, voice: str = "Professional") -> str:
        """
        Pure business logic function for ad synthesis.
        """
        # Get the latest persona from the JSON file
        current_settings = self.settings_svc.get_settings()
        persona = current_settings.get("system_persona")
        prompt = (
            f"System Instruction: Act as a {persona}. "
            f"Task: Generate a {voice} ad copy for: {product_info}"
        )
        response = self.model.generate_content(prompt)
        return response.text.strip()

# --- MOCK SERVICE ---
class MockGeminiService(BaseAdService):
    def generate_response(self, product_info: str, voice: str) -> str:
        return f"[MOCK MODE] Simulated {voice} ad for: {product_info}."


_instance = None
def get_gemini_service() -> BaseAdService:
    global _instance
    if _instance is None:
        return MockGeminiService() if os.getenv("ENV_MODE") == "test" else GeminiService()
    return _instance

