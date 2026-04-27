"""Quick test to verify the generate endpoint works"""

# Test the mock service directly
from api.services.llm_service import MockLlmService

service = MockLlmService()

# Test 1: Simple product info
print("Test 1: Simple product input")
print("="*60)
result = service.generate_response("Wireless Earbuds - ₹2,999", "Professional")
print(result[:200] + "...")
print("\n")

# Test 2: PMI-style prompt (like the API uses)
print("Test 2: PMI-style prompt")
print("="*60)
pmi_prompt = """
PRODUCT: Wireless Earbuds Pro - Noise-cancelling. TONE: Professional.
USER: Male, 28, Hyderabad, HISTORY: Bought a smartphone last year.

PMI CONSTRAINTS:
- Reason for purchase based on history.
- Personalize with user name: Rahul.
- Human-like persona (Don't reveal AI).

FORMAT HEADERS:
FACEBOOK:
INSTAGRAM:
TWITTER:
WHATSAPP:
TEXTMESSAGE:
"""
result = service.generate_response(pmi_prompt, "Professional")
print(result[:200] + "...")
print("\n")

# Check if it has all platforms
platforms = ['FACEBOOK:', 'INSTAGRAM:', 'TWITTER:', 'WHATSAPP:', 'TEXTMESSAGE:']
missing = [p for p in platforms if p not in result]

if missing:
    print(f"❌ Missing platforms: {missing}")
else:
    print("✅ All platforms present!")
