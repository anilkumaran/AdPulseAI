# AdPulseAI — sequence diagrams

Render these blocks in any Mermaid-capable viewer (GitHub, Cursor preview, [mermaid.live](https://mermaid.live)).

## 1. Authentication (`POST /token`)

```mermaid
sequenceDiagram
    autonumber
    actor User as Browser / UI
    participant API as FastAPI<br/>main.py
    participant Auth as AuthService<br/>auth_service.py
    participant DB as DBService<br/>db_service.py (JSON)

    User->>API: POST /token (username, password)
    API->>DB: get_data() → scan users[]
    DB-->>API: user record + password_hash
    API->>Auth: verify_password(plain, hash)
    Auth-->>API: ok / fail
    alt invalid credentials
        API-->>User: 400 Invalid Credentials
    else valid
        API->>Auth: create_token(sub, role, merchant_id?)
        Auth-->>API: JWT access_token
        API-->>User: access_token, role, merchant_id, name, email
    end
```

## 2. Personalized social ad (`POST /api/generate`)

Authenticated requests send `Authorization: Bearer <JWT>` (OAuth2 bearer). `get_current_user` decodes the token on each call.

```mermaid
sequenceDiagram
    autonumber
    actor User as Browser / UI
    participant API as FastAPI<br/>main.py
    participant Auth as AuthService
    participant DB as DBService
    participant Prompt as prompt_service
    participant LLM as LLM service<br/>llm_service.py<br/>(Gemini / Ollama)

    User->>API: POST /api/generate (AdRequest + Bearer token)
    API->>Auth: get_current_user(token)
    Auth-->>API: merchant context (sub, role, merchant_id)
    API->>DB: get_data() → merchant + customers for merchant_id
    DB-->>API: business profile, first customer or defaults
    API->>Prompt: build_social_media_ad_context(...)
    Prompt-->>API: PMI prompt text
    API->>LLM: generate_response(prompt, voice)
    LLM-->>API: generated ad content
    API->>DB: log_generation(...)
    API-->>User: AdResponse (content)
```

## 3. SMS campaign (`POST /api/sms/campaign`)

Covers optional **file-backed generation cache**, per-customer LLM messages, optional **immediate SNS bulk send**, and logging.

```mermaid
sequenceDiagram
    autonumber
    actor User as Browser / UI
    participant API as FastAPI<br/>main.py
    participant Auth as AuthService
    participant DB as DBService
    participant Cache as sms_campaign_cache
    participant Prompt as prompt_service
    participant LLM as LLM service
    participant SNS as SNSService<br/>sns_service.py
    participant AWS as AWS SNS<br/>(or mock)

    User->>API: POST /api/sms/campaign (customer_ids, product_info, voice, send_immediately)
    API->>Auth: get_current_user(token)
    Auth-->>API: user + merchant_id
    API->>DB: get_data() → merchants, customers by IDs
    DB-->>API: merchant profile + customer rows

    API->>Cache: get(cache_key)
    alt full cache hit
        Cache-->>API: messages per customer_id
        Note over API: Skip LLM for all customers in request
    else miss or partial miss
        Cache-->>API: empty / incomplete
        loop each customer
            API->>Prompt: build_sms_campaign_customer_context(...)
            Prompt-->>API: SMS prompt
            API->>LLM: generate_response(..., prompt_type=sms_campaign)
            LLM-->>API: personalized SMS body
        end
        API->>Cache: set(cache_key, customer_id → message)
    end

    alt send_immediately = false
        API->>DB: log_sms_campaign, log_generation (summary)
        API-->>User: CampaignSMSResponse (preview, no SNS)
    else send_immediately = true
        API->>SNS: send_bulk_sms(recipients) [filtered phones]
        alt ENV_MODE=test or no AWS keys
            SNS-->>API: mocked results
        else live SNS
            SNS->>AWS: Publish(PhoneNumber=...) per recipient
            AWS-->>SNS: MessageId / errors
            SNS-->>API: sent / skipped / failed counts
        end
        API->>DB: log_sms_campaign, log_generation
        API-->>User: CampaignSMSResponse (+ sns_dispatch, delivery lines)
    end
```

## 4. Single / bulk SMS (no LLM)

```mermaid
sequenceDiagram
    autonumber
    actor User as Browser / UI
    participant API as FastAPI
    participant Auth as AuthService
    participant SNS as SNSService
    participant DB as DBService

    User->>API: POST /api/sms/send OR /api/sms/bulk (+ Bearer)
    API->>Auth: get_current_user
    API->>SNS: send_sms / send_bulk_sms (client-supplied body)
    SNS-->>API: status / per-recipient results
    API->>DB: log_sms_send / log_bulk_sms_send
    API-->>User: SMSResponse / BulkSMSResponse
```

---

**Legend:** JSON “database” is loaded via `db_service`; LLM backend is chosen by admin settings / environment (see `llm_service.py`). SNS uses direct `Publish` to phone numbers; optional `SNS_ALLOWED_PHONES` can restrict which numbers hit AWS in live mode.
