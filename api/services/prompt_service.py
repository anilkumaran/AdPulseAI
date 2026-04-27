"""
All user-facing LLM prompt templates and builders for AdPulseAI.
Routes and services should import from here — do not duplicate prompt text elsewhere.
"""

PROMPT_TEMPLATES: dict[str, str] = {
    "sms_campaign": """
You are a {persona}. Write the exact SMS the customer will receive on their phone.

{product_info}

TONE (NOT email):
- Write like a quick, friendly text: punchy, warm, exciting — like a brand DM or flash-sale alert.
- NEVER use email style: no "Dear", "Subject", "Dear Sir/Madam", "Kind regards", "Best regards", formal sign-offs, or business-letter wording.
- Short hooks, 1–2 emojis if they fit, plain words people tap to read on a lock screen.

STRUCTURE (required order, use real values from COMPANY/WEBSITE/PHONE above):
1) One or two lines: hook + offer + name/history touch (keep tight; you may use 2 SMS segments if needed for length).
2) Then a new line with exactly: Contact information:
3) Then a new line with the website as a full clickable URL starting with https:// (copy from WEBSITE; if missing use https:// plus domain only).
4) Then a new line with the phone exactly as +91 followed by 10 digits (no spaces preferred), e.g. +919876543210.

SMS only — no FACEBOOK/INSTAGRAM labels.

YOUR REPLY — CRITICAL:
- Output only the SMS body (no "Here is…", no quotes around the whole thing).
- First character = first character the customer reads (greeting or emoji).
- The lines "Contact information:", the https:// URL line, and the +91 line must appear exactly as described so links and tap-to-call work.
""",
    "ad_generator": """
You are a {persona}. Generate {voice} marketing ad copy for multiple platforms.

Product Information:
{product_info}

TONE (NOT email):
- Social-first: scroll-stopping, energetic, human — like native posts people want to share.
- NEVER write like a formal email: no "Dear customer", no subject lines, no corporate memo tone, no "Yours faithfully", no long formal paragraphs.

IMPORTANT RULES:
1. Say clearly WHAT the product is and why it matters in a fun, specific way (not generic filler).
2. Each platform block = promo lines first, then contact details ONLY in the format below (so URLs and phones can be linked in the app).

CONTACT BLOCK (repeat under EVERY platform after the promo copy, same company details):
- New line, then exactly: Contact information:
- New line: full website URL starting with https:// (use {company_website} with https:// if it has no scheme)
- New line: phone as +91 and 10 digits, e.g. {company_phone}

Format response EXACTLY with these platform headers:

FACEBOOK:
[2-4 short lines + emojis + hashtags. Then blank line, then Contact information:, then URL line, then +91 line. Mention {company_name} naturally in the promo part.]

INSTAGRAM:
[2-4 short lines + emojis + hashtags. Then same Contact information: / https URL / +91 block.]

TWITTER:
[Under 280 chars promo; then newline Contact information: newline https URL newline +91]

WHATSAPP:
[Friendly 2-3 short lines, emojis. Then Contact information: / https URL / +91]

TEXTMESSAGE:
[Under ~160 chars promo if possible; then Contact information: / https / +91 — may run slightly over for the contact block]

YOUR REPLY — CRITICAL:
- Nothing before FACEBOOK: and nothing after TEXTMESSAGE content.
- Every https:// URL must be a complete copy-paste link (include path if any). Phone must include country code +91.
- Exactly five sections: FACEBOOK:, INSTAGRAM:, TWITTER:, WHATSAPP:, TEXTMESSAGE: — headers on their own lines.
""",
}


def _extract_company_fields(product_info: str) -> tuple[str, str, str]:
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
    return company_name, company_website, company_phone


def build_generation_prompt(
    product_info: str,
    voice: str,
    persona: str,
    prompt_type: str = "ad_generator",
) -> str:
    """
    Build the full user prompt string from shared templates for the LLM.
    Same output regardless of which provider (Ollama, Gemini) runs it.
    """
    template = PROMPT_TEMPLATES.get(prompt_type, PROMPT_TEMPLATES["ad_generator"])

    if prompt_type == "sms_campaign":
        return template.format(persona=persona, product_info=product_info)

    company_name, company_website, company_phone = _extract_company_fields(product_info)
    return template.format(
        persona=persona,
        voice=voice,
        product_info=product_info,
        company_name=company_name,
        company_website=company_website,
        company_phone=company_phone,
    )


def build_social_media_ad_context(
    company_name: str,
    company_website: str,
    company_phone: str,
    product_info: str,
    voice: str,
    demographics: str,
    purchase_context: str,
) -> str:
    """
    Product-info block for multi-platform social ad generation (PMI-style).
    Fed into build_generation_prompt via the ad_generator template.
    """
    return f"""
    COMPANY: {company_name}
    PRODUCT: {product_info}. TONE: {voice}.
    TARGET AUDIENCE: {demographics}, CONTEXT: {purchase_context}.

    PMI CONSTRAINTS:
    - Engaging social voice — NOT formal email; no "Dear" or letter-style closings.
    - Persuasive, human-like (don't reveal AI). No specific customer names (broad audience).
    - After promo lines for each platform, use this exact layout:
      Contact information:
      https://... (full URL from company website)
      +91XXXXXXXXXX (from company phone)

    FORMAT HEADERS:
    FACEBOOK:
    INSTAGRAM:
    TWITTER:
    WHATSAPP:
    TEXTMESSAGE:
    """


def build_sms_campaign_customer_context(
    company_name: str,
    company_website: str,
    company_phone: str,
    product_info: str,
    customer_name: str,
    gender: str,
    age: str,
    city: str,
) -> str:
    """Structured product/customer block for personalized SMS campaign generation."""
    return f"""
COMPANY: {company_name}
WEBSITE: {company_website}
PHONE: {company_phone}
PRODUCT: {product_info}
CUSTOMER: {customer_name}
GENDER: {gender}
AGE: {age}
CITY: {city}
"""
