# AdPulseAI Project PPT (self-contained)

Generate an **8-slide** project presentation in **16:9**.

## Visual style (match the provided sample deck look)

Recreate the look of a modern “GenAI | Project Presentation” deck:

- Clean, professional **business + AI** aesthetic
- Consistent typography hierarchy (bold headings, lighter body)
- Subtle gradients / tinted section backgrounds (blue/green/orange accents)
- Rounded cards, light shadows, generous whitespace
- Minimal, consistent icon style (flat / simple)
- Keep slides uncluttered: **max 4–5 bullets** per slide

If you cannot reference the sample deck directly, approximate it using:

- Primary accent: **AI blue** (#0d6efd-ish)
- Secondary accent: **Calm green** (#198754-ish)
- Third accent: **Soft orange** (#ffc107-ish)
- Background: very light gray/white with subtle gradient

## Important constraints

- AdPulseAI is a **multi-tenant** marketing automation platform with roles: **Super Admin / Merchant Admin / Employee**
- Cloud-first LLM routing: default is **Gemini →  fallback Ollama (Llama2)** (llama2 is optional/conditional)
- SMS sending uses **AWS SNS** (mock mode may exist for testing)
- Avoid fake performance claims. Use “pilot targets” / “estimated” language unless numbers are provided.

## Title slide

- **Title:** AdPulseAI — GenAI‑Powered Multi‑Channel Ad Synthesis + PMI Messaging
- **Subtitle:** Generate platform-ready ads (Facebook, Instagram, Twitter, WhatsApp, SMS) and run personalized SMS campaigns using customer context
- **Prepared By:**
  - V. Surya Prakash
  - Ch. Sagar
  - K. Anil
- **Project Guide:** Dr. B. Rama

## Slides (generate all content) — match these exact section titles

### 1) Title (cover)

Use a strong hero layout with a subtle AI/marketing background pattern and the title/subtitle/meta.

### 2) Abstract

Bullets (keep tight, like the sample):

- SMEs struggle with limited budgets and lack of marketing expertise
- AdPulseAI automates multi-platform ad creation using Generative AI
- Extends **PMI** from SMS-only to omnichannel content + messaging
- Includes role-based governance + usage telemetry for safer platform operations

Add a “Core Components” row with 4 labeled icons:

**Prompt Templates** • **LLM Router (Ollama→Gemini)** • **AWS SNS SMS** • **Campaign History**

Quote at bottom:

“Turning raw product notes into ready-to-publish campaigns.”

### 3) Introduction

Bullets:

- Digital marketing requires consistent content across channels and formats
- Manual copywriting + segmentation is time-consuming for small teams
- AdPulseAI provides a unified workflow: input product details → generate content → reuse & iterate
- Adds customer-targeted personalization for SMS campaigns (PMI-inspired)

Add a small callout line (like sample):

**One input → Five platforms** — consistent voice, faster execution.

### 4) Literature Review

Two-column layout, matching the sample:

**📚 Existing Landscape**

- Generative AI used for ad copy and brand messaging
- Personalization frameworks exist but are often single-channel
- Many tools lack admin governance and multi-tenant isolation
- SMS delivery often relies on external gateways with limited scalability

**✨ Proposed Innovation (AdPulseAI)**

- Production-ready PMI evolution: SMS + social platforms in one tool
- Role-based system: Super Admin governance + merchant isolation
- LLM routing: cloud-first (Gemini) with with local fallback (Ollama) 
- Integrated campaign history + telemetry for monitoring and iteration

Quote:

“From siloed tools to an integrated omnichannel system.”

### 5) Methodology

Three blocks (like sample): **🧩 Ad Synthesis**, **📩 PMI SMS Campaigns**, **🖥 Interface & Roles**

**🧩 Ad Synthesis**

- Structured prompt templates produce platform-specific blocks (FB/IG/Twitter/WhatsApp/SMS)
- Voice + persona settings ensure consistent brand tone
- Output is copy-ready and can be edited/copy-pasted per platform

**📩 PMI SMS Campaigns**

- Select customers; use demographics/context to generate personalized SMS
- Optional send via AWS SNS; preview mode for safety
- Cost estimation for planning campaign budgets

**🖥 Interface & Roles**

- Single-page web UI with role-based menus and workflows
- Super Admin: telemetry, system settings, merchant management
- Merchant Admin: customers, employees, campaigns, history

Include a UI visual: a clean “app screenshot-style” mock showing:

1) Login + role-based sidebar
2) Ad generator input + platform tabs output
3) SMS campaign customer selector + preview list + send toggle

### 6) Experimental Study

Present as a small evaluation plan/pilot (do NOT fabricate real numbers if not provided):

**📋 Evaluation Setup**

- Dataset: sample product briefs + de-identified customer profiles (demo data)
- Metrics: content usefulness, clarity, brand consistency, time-to-first-draft, usability (SUS-style)
- Compare: manual copywriting vs AdPulseAI generation + edits

**🔬 Methodology**

- Blind review by mixed group (students + small business users)
- Check format correctness per platform (length/style constraints)
- Validate campaign flow: selection → preview → (optional) send + logging

Tech stack line (small): FastAPI • Ollama • Gemini (optional) • AWS SNS • JSON DB • Vanilla JS UI

### 7) Key Results

If you have real numbers, include them; otherwise show **Pilot targets** (clearly labeled).

Suggested layout:

- 3 KPI cards (Draft quality / Format correctness / Avg response time)
- 1 line of user feedback bullets (e.g., “faster drafting”, “easy to reuse”, “clear SMS previews”)

Important: label numbers as **Pilot targets** if not measured.

### 8) Conclusion & Future Work

**✅ Impact**

- Reduces time to create multi-platform campaigns from a single product brief
- Brings PMI-style personalization into a practical tool with governance
- Supports cloud-first operation with optional local fallback

**🚀 Future Roadmap**

- Add more local models & dynamic model priority configuration
- More channels (email/SEO landing copy) and richer analytics
- Per-merchant brand kits (style rules, forbidden claims, compliance checks)
- A/B testing support and campaign performance feedback loops

Footer (small):

Prepared By: V. Surya Prakash, Ch. Sagar, K. Anil

• Project Guide: Dr. B. Rama
