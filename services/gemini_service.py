import os
from abc import ABC, abstractmethod
from dotenv import load_dotenv
from google import genai
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
        self.client = genai.Client(api_key=self.api_key)
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
        response = self.client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt
        )
        return response.text.strip()

# --- MOCK SERVICE ---
class MockGeminiService(BaseAdService):
    """Mock service for testing without actual Gemini API calls"""
    
    def generate_response(self, product_info: str, voice: str) -> str:
        """Generate mock multi-platform ad content"""
        
        try:
            # Extract product name from prompt
            product_name = "Product"
            if "PRODUCT:" in product_info:
                product_line = product_info.split("PRODUCT:")[1].split(".")[0].strip()
                product_name = product_line.split("-")[0].strip() if "-" in product_line else product_line[:30]
            else:
                # If no PRODUCT: marker, use the whole input
                product_name = product_info[:50].strip()
            
            # Check if it's a PMI personalized SMS-only prompt (for SMS campaigns)
            is_sms_only = "Generate ONLY the SMS text message" in product_info
            customer_name = "Customer"
            
            if "USER:" in product_info:
                try:
                    user_section = product_info.split("USER:")[1].split("PMI")[0]
                    if "Name=" in user_section:
                        customer_name = user_section.split("Name=")[1].split(",")[0].strip()
                    elif "," in user_section:
                        # Format: "Name, Demographics, History"
                        parts = user_section.split(",")
                        if len(parts) > 0:
                            customer_name = parts[0].strip()
                except Exception as e:
                    print(f"[MockGemini] Error parsing user info: {e}")
                    customer_name = "Customer"
            
            # Generate mock content based on type
            if is_sms_only:
                # PMI-style personalized SMS only (for SMS campaigns)
                return f"Hi {customer_name}! 🎉 Based on your interests, check out our {product_name}! Special offer just for you. Reply YES for details!"
            else:
                # Multi-platform ad content (for regular ad generation)
                return f"""FACEBOOK:
🎉 Introducing {product_name} - Your Perfect Choice!

Discover amazing features and unbeatable value. Limited time offer - don't miss out!

💰 Special Price Available
🚚 Free Delivery
⭐ Premium Quality

Shop now and experience the difference!

#NewArrival #SpecialOffer #ShopNow

INSTAGRAM:
✨ Say hello to {product_name}! ✨

Your lifestyle upgrade is here! 🎯

✅ Premium quality
✅ Best price guaranteed
✅ Fast delivery

Tag a friend who needs this! 👇

#Shopping #Lifestyle #MustHave #Trending

TWITTER:
🔥 {product_name} is here!

Premium quality + Great price = Perfect deal! 🎯

Limited stock available. Order now! 🛒

#Deals #Shopping #NewProduct

WHATSAPP:
Hi there! 👋

Excited to share our new {product_name} with you!

✅ Premium quality
✅ Special pricing
✅ FREE delivery

Interested? Let me know! 😊

TEXTMESSAGE:
New arrival: {product_name}! Premium quality, special price, FREE delivery. Order now! Reply YES for details."""
        
        except Exception as e:
            print(f"[MockGemini] Error generating response: {e}")
            # Fallback response
            return """FACEBOOK:
🎉 New Product Available!

Check out our latest offering with amazing features!

#NewArrival #ShopNow

INSTAGRAM:
✨ Something special just arrived! ✨

#Shopping #MustHave

TWITTER:
🔥 New product alert!

#Deals #Shopping

WHATSAPP:
Hi! Check out our new product!

TEXTMESSAGE:
New arrival! Order now!"""


_instance = None
def get_gemini_service() -> BaseAdService:
    global _instance
    if _instance is None:
        env_mode = os.getenv("ENV_MODE", "test")
        _instance = MockGeminiService() if env_mode == "test" else GeminiService()
    return _instance

