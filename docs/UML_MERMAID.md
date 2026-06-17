# AdPulseAI — Mermaid UML-style diagrams

Paste any block into [mermaid.live](https://mermaid.live) or a Markdown preview that supports Mermaid.

---

## 1. Project overview (system context)

High-level actors and external systems.

```mermaid
flowchart LR
    subgraph Users
        SA[Super Admin]
        MA[Merchant Admin]
        EM[Employee]
    end

    subgraph AdPulseAI["AdPulseAI (FastAPI + static UI)"]
        API[REST API<br/>api/main.py]
        UI[Browser UI<br/>ui/static]
    end

    subgraph Data["Persistence"]
        DB[(JSON store<br/>db_service / schemas)]
    end

    subgraph AI["Generation"]
        LLM[Gemini / Ollama<br/>llm_service]
    end

    subgraph Cloud["Messaging"]
        SNS[AWS SNS SMS<br/>sns_service]
    end

    SA --> UI
    MA --> UI
    EM --> UI
    UI --> API
    API --> DB
    API --> LLM
    API --> SNS
```

---

## 2. End-to-end application flow

Typical journey from login through campaigns.

```mermaid
flowchart TD
    A[Open UI] --> B[POST /token<br/>login]
    B --> C{Valid user?}
    C -->|No| B
    C -->|Yes| D[Store JWT + role<br/>in browser]
    D --> E[Dashboard by RBAC]

    E --> F[Social PMI ad]
    E --> G[SMS tools]
    E --> H[Admin / merchant CRUD]

    F --> F1[POST /api/generate]
    F1 --> F2[Merchant + customer context]
    F2 --> F3[LLM generates copy]
    F3 --> F4[Log generation history]

    G --> G1{Which SMS path?}
    G1 --> G2[POST /api/sms/send<br/>single transactional]
    G1 --> G3[POST /api/sms/bulk<br/>client bodies]
    G1 --> G4[POST /api/sms/campaign<br/>LLM per customer]

    G4 --> G5{Cache hit?}
    G5 -->|Yes| G6[Reuse messages]
    G5 -->|No| G7[LLM per selected customer]
    G6 --> G8{send_immediately?}
    G7 --> G8
    G8 -->|Yes| G9[SNS bulk publish]
    G8 -->|No| G10[Preview only]
    G9 --> G11[Log campaign + history]

    G2 --> SNS[(SNS / mock)]
    G3 --> SNS
```

---

## 3. Component diagram (backend layers)

Logical modules inside the API package.

```mermaid
flowchart TB
    subgraph FastAPI["FastAPI app (main.py)"]
        Routes[HTTP routes<br/>token, generate, SMS, admin, merchant]
    end

    subgraph Services["api/services"]
        Auth[auth_service<br/>JWT, bcrypt]
        DB[db_service<br/>JSON CRUD + logs]
        LLM[llm_service<br/>Gemini / Ollama]
        Prompt[prompt_service<br/>PMI + SMS prompts]
        SNS[sns_service<br/>Publish PhoneNumber]
        Settings[settings_service<br/>admin LLM prefs]
        Cache[sms_campaign_cache<br/>optional file cache]
    end

    subgraph Schemas["api/schemas"]
        AD[ad_schemas]
        SMS[sms_schemas]
    end

    Routes --> Auth
    Routes --> DB
    Routes --> LLM
    Routes --> Prompt
    Routes --> SNS
    Routes --> Settings
    Routes --> Cache
    Routes --> AD
    Routes --> SMS
    Prompt --> LLM
    LLM --> Settings
    Cache -.-> LLM
```

---

## 4. Domain model (simplified class diagram)

Mirrors main collections in the JSON store and request/response shapes (not every field).

```mermaid
classDiagram
    direction TB

    class User {
        +int id
        +string username
        +string password_hash
        +string role
        +string merchant_id
        +string name
        +string email
    }

    class Merchant {
        +string id
        +string business_name
        +string company_website
        +string phone
        +string industry
    }

    class Customer {
        +int id
        +string merchant_id
        +string name
        +string phone
        +string gender
        +int age
        +string city
    }

    class GenerationLog {
        +user sub
        +merchant_id
        +product_info
        +content
    }

    class SMSCampaign {
        +campaign_id
        +merchant scope
        +customer_ids
    }

    Merchant "1" --> "*" Customer : owns
    Merchant "1" --> "*" User : merchant_admin / employee
    User "*" --> "0..1" Merchant : scoped by merchant_id
```

---

## 5. RBAC vs API surface (overview)

Which roles typically reach which areas (approximate; some endpoints enforce extra checks in code).

```mermaid
flowchart LR
    subgraph Roles
        R1[super_admin]
        R2[merchant_admin]
        R3[employee]
    end

    subgraph Areas
        A1[Platform dashboard<br/>telemetry / settings / all merchants]
        A2[Merchant workspace<br/>ads, SMS, customers, employees]
        A3[Employee workspace<br/>narrower merchant features]
    end

    R1 --> A1
    R1 --> A2
    R2 --> A2
    R3 --> A3
```

---

## 6. Sequence — authenticated PMI generation (summary)

```mermaid
sequenceDiagram
    participant UI as Browser
    participant API as FastAPI
    participant Auth as AuthService
    participant DB as DBService
    participant P as PromptService
    participant L as LLMService

    UI->>API: POST /api/generate + Bearer JWT
    API->>Auth: decode token
    Auth-->>API: sub, role, merchant_id
    API->>DB: merchant + customers
    DB-->>API: context
    API->>P: build_social_media_ad_context
    P-->>API: prompt
    API->>L: generate_response
    L-->>API: ad text
    API->>DB: log_generation
    API-->>UI: AdResponse
```

---

## 7. Sequence — SMS campaign (summary)

```mermaid
sequenceDiagram
    participant UI as Browser
    participant API as FastAPI
    participant DB as DBService
    participant C as SMS campaign cache
    participant P as PromptService
    participant L as LLMService
    participant S as SNSService

    UI->>API: POST /api/sms/campaign
    API->>DB: customers by IDs + merchant
    API->>C: get cache key
    alt cache miss
        loop customers
            API->>P: SMS context
            API->>L: generate SMS body
        end
        API->>C: set cache
    end
    opt send_immediately
        API->>S: send_bulk_sms
    end
    API->>DB: log campaign + generation summary
    API-->>UI: CampaignSMSResponse
```

---

More granular sequence diagrams (including `/token` and raw SMS) live in [`SEQUENCE_DIAGRAM.md`](./SEQUENCE_DIAGRAM.md).
