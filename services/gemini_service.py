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
        
        # Prompt Dictionary
        self.prompts = {
            "sms_campaign": """
You are a {persona}. Create a personalized SMS text message.

{product_info}

REQUIREMENTS:
1. Create ONLY an SMS text message (160 characters max)
2. Personalize with customer name
3. Reference their purchase history naturally
4. Use conversational tone
5. Include company contact information
6. DO NOT include platform labels like FACEBOOK, INSTAGRAM
7. Output ONLY the SMS message text, nothing else
""",
            "ad_generator": """
You are a {persona}. Generate {voice} marketing ad copy for multiple platforms.

Product Information:
{product_info}

IMPORTANT RULES:
1. Clearly describe WHAT the product is and its key features
2. Use natural, conversational language (not robotic)
3. Include specific product details from the input
4. Format response EXACTLY with these platform headers:

FACEBOOK:
[1-2 short lines describing the product with emojis. End with: "Visit {company_website} or call {company_phone} | {company_name}" and 2-3 hashtags]

INSTAGRAM:
[1-2 short lines about the product with emojis. End with: "🔗 {company_website} | 📞 {company_phone} | {company_name}" and 2-3 hashtags]

TWITTER:
[Under 280 chars describing product. Include: {company_name} and 2-3 hashtags]

WHATSAPP:
[2-3 short lines friendly message about the product with emojis. End with: "Visit {company_website} or call {company_phone} - {company_name}"]

TEXTMESSAGE:
[Under 160 chars about product. Include: {company_website} {company_phone} - {company_name}]

Do NOT add any other text. Just the platform headers and content.
"""
        }

    def generate_response(self, product_info: str, voice: str = "Professional", prompt_type: str = "ad_generator") -> str:
        """
        Pure business logic function for ad synthesis.
        prompt_type: "ad_generator" or "sms_campaign"
        """
        current_settings = self.settings_svc.get_settings()
        persona = current_settings.get("system_persona")
        
        # Get prompt template from dictionary
        prompt_template = self.prompts.get(prompt_type, self.prompts["ad_generator"])
        
        if prompt_type == "sms_campaign":
            prompt = prompt_template.format(persona=persona, product_info=product_info)
        else:
            # Extract company info from product_info for multi-platform ads
            company_name = "Our Store"
            company_website = ""
            company_phone = ""
            if "COMPANY:" in product_info:
                company_line = product_info.split("COMPANY:")[1].split("\n")[0].strip()
                company_name = company_line
            if "WEBSITE:" in product_info:
                website_line = product_info.split("WEBSITE:")[1].split("\n")[0].strip()
                company_website = website_line
            if "PHONE:" in product_info:
                phone_line = product_info.split("PHONE:")[1].split("\n")[0].strip()
                company_phone = phone_line
            
            prompt = prompt_template.format(
                persona=persona, 
                voice=voice, 
                product_info=product_info,
                company_name=company_name,
                company_website=company_website,
                company_phone=company_phone
            )
        
        response = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        result = response.text.strip()
        print("\n=== GEMINI API RESPONSE ===")
        print(result)
        print("=== END RESPONSE ===\n")
        
        # Save to file for mock data
        try:
            import json
            from datetime import datetime
            log_file = "gemini_responses.jsonl"
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "input": product_info,
                "voice": voice,
                "output": result
            }
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"[Warning] Failed to log response: {e}")
        
        return result

# --- MOCK SERVICE ---
class MockGeminiService(BaseAdService):
    """Mock service for testing without actual Gemini API calls"""
    
    def generate_response(self, product_info: str, voice: str, prompt_type: str = "ad_generator") -> str:
        """Generate mock ad content based on prompt type"""
        
        try:
            product_name = "Product"
            if "PRODUCT:" in product_info:
                product_line = product_info.split("PRODUCT:")[1].split(".")[0].strip()
                product_name = product_line.split("-")[0].strip() if "-" in product_line else product_line[:30]
            else:
                product_name = product_info[:50].strip()
            
            if prompt_type == "sms_campaign":
                # SMS-only response
                customer_name = "Customer"
                if "CUSTOMER:" in product_info:
                    customer_line = product_info.split("CUSTOMER:")[1].split("\n")[0].strip()
                    customer_name = customer_line
                return f"Hi {customer_name}! 🎉 Check out our {product_name}! Special offer just for you. Reply YES for details!"
            else:
                # Multi-platform response
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

