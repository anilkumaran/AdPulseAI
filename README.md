# AdPulseAI - Generative AI for Autonomous Ad Synthesis and Business Intelligence

## Table of Contents
1. [Abstract](#abstract)
2. [PMI Evolution: From Research to Production](#pmi-evolution-from-research-to-production)
3. [Quick Start](#quick-start)
4. [System Specification](#system-specification)
   - [Hardware Requirements](#hardware-requirements-aws-ec2)
   - [Software Requirements](#software-requirements)
5. [System Modules](#system-modules)
   - [Admin Module](#1-admin-module-ownermanager)
   - [User Module](#2-user-module-employeesales-staff)
6. [Proposed System](#proposed-system-cloud-implementation-with-admin-control)
7. [Project Guide](#project-guide)
8. [Developed By](#developed-by)

---

## Abstract
The AdPulseAI is an innovative, cloud-based framework designed to democratize professional digital marketing and business intelligence for Enterprises by leveraging the transformative power of Generative Artificial Intelligence. Developed as a response to the resource constraints that often hinder small businesses—such as limited marketing budgets and lack of specialized data expertise—the system provides an automated platform for synthesizing multi-channel ad copy, optimizing SEO metadata, and identifying target audience segments. Hosted on Amazon Web Services (AWS) using a scalable EC2 infrastructure, the application utilizes the Google Gemini API to transform unstructured product data into high-converting promotional content with unprecedented speed and precision. By integrating a robust Admin Module for centralized governance and an intuitive user interface for streamlined task execution, AdPulseAI empowers SMEs to enhance their operational efficiency, reduce overhead costs by up to 30%, and maintain a competitive edge in an increasingly digital marketplace.

---

## PMI Evolution: From Research to Production

AdPulseAI extends the Persuasive Message Intelligence (PMI) framework introduced by Lee et al. (IEEE Access, 2024) from a research prototype to a production-ready, multi-channel marketing platform.

**Reference Paper:** [Developing Personalized Marketing Service Using Generative AI](https://ieeexplore.ieee.org/document/10419357) (DOI: 10.1109/ACCESS.2024.3361946)

| **Original Paper (PMI)** | **AdPulseAI System** |
| :--- | :--- |
| SMS-only delivery | Multi-platform (Facebook, Instagram, Twitter, WhatsApp, SMS) |
| GPT-4 API | Google Gemini API (more cost-effective) |
| Aligo SMS API | AWS SNS (scalable cloud messaging) |
| Single-channel personalization | Omnichannel personalized marketing |
| Research prototype | Production-ready cloud deployment (AWS) |

---

## Quick Start

Prerequisites: Python 3.10+.

1. Clone and enter the repo:
```bash
git clone <repository-url>
cd AdPulseAI
```

2. Copy env template and edit values (`GEMINI_API_KEY` when using Gemini, `OLLAMA` / `OLLAMA_MODEL` when using local Ollama, AWS keys for real SMS):
```bash
cp .env.example .env
```

3. Start the app from the repo root (`run.sh` creates `.venv` if needed, installs `api/requirements.txt` when the venv is new or requirements changed, loads `.env`, runs FastAPI with reload):
```bash
chmod +x run.sh
./run.sh
```

Optional: `HOST=0.0.0.0 ./run.sh` to listen on all interfaces; `INSTALL_DEPS=1 ./run.sh` to force reinstall dependencies after editing `api/requirements.txt`.

Manual equivalent after activating `.venv` and exporting variables from `.env`:
```bash
python -m uvicorn api.main:app --reload --host 127.0.0.1 --port 8000
```

4. Open the UI at `http://127.0.0.1:8000` (or `http://localhost:8000`).

### Default login

| Role | Username | Password |
|------|----------|----------|
| Admin | `admin` | `admin123` |
| Merchant | `merchant1` | `user123` |

### Test vs production

With `ENV_MODE=test` (also the default in `run.sh` when `.env` does not define `ENV_MODE`), the LLM and SNS layers use mocks—no Gemini key or AWS SMS required. Set `ENV_MODE=prod` in `.env` for real Gemini and/or Ollama per `.env.example`.

---

## System Specification

### Hardware Requirements (AWS EC2)
| Component | Specification |
| :--- | :--- |
| **Instance Type** | t2.micro (AWS Free Tier eligible) |
| **Processor** | 1 vCPU |
| **Memory (RAM)** | 1 GB |
| **Storage** | 8 GB Elastic Block Store (EBS) |
| **Network** | Public IP; security group allows HTTP (80) and app port (e.g. 8000 for uvicorn, or 443 behind a reverse proxy) |

### Software Requirements
| Layer | Technology / Tool |
| :--- | :--- |
| **Front End** | HTML5, CSS3, JavaScript (Vanilla) |
| **Back End** | Python 3.10+, FastAPI |
| **Cloud Platform** | Amazon Web Services (AWS) |
| **AI Engine** | Google Gemini API and/or local models via Ollama |
| **App server** | uvicorn (`api.main:app`); optional process manager / reverse proxy in production |

---

## System Modules

### 1. Admin Module (Owner/Manager)
* **Login:** Secure administrative authentication to access system-wide analytics.
* **Usage Dashboard:** Real-time monitoring of API requests, token consumption, and server health.
* **Brand Voice Settings:** Tools to define the permanent "personality" of the AI (e.g., Professional, Quirky, or Trustworthy).
* **User Management:** Overseeing staff access and managing permissions for various departments.

### 2. User Module (Employee/Sales Staff)
* **Login:** Secure user access for employees to utilize the generation tools.
* **Product Data Input:** A dedicated form to enter product specifications, features, and pricing.
* **Automated Ad Synthesis:** One-click generation of Facebook ads, Google SEO tags, and Amazon product descriptions.
* **Market Insight Engine:** AI identifies primary target audiences and high-performing keywords based on input data.
* **My Profile:** Users can manage their profiles and view the history of their generated marketing collateral.

---

## Proposed System (Cloud Implementation with Admin Control)
The "AdPulseAI System" introduces a modernized and efficient solution for business growth:
* **AWS Cloud Hosting:** The backend is deployed on an EC2 instance, providing a reliable and globally accessible infrastructure for small teams.
* **Autonomous Marketing Synthesis:** By using the Gemini API, the system performs high-level reasoning to expand raw notes into professional, high-converting ad copy.
* **Data-Driven Decision Making:** The app identifies sales trends and customer sentiment from unstructured text, helping owners make better stock and pricing choices.
* **Operational Cost Reduction:** Automates the work of a copywriter and marketing analyst, saving the SME significant monthly overhead costs.

---

## API Endpoints

### Authentication
- `POST /token` - Login and get access token

### Ad Generation
- `POST /api/generate` - Generate multi-platform ad content
- `GET /api/history` - Get generation history

### SMS Campaigns (PMI Implementation)
- `POST /api/sms/send` - Send single SMS
- `POST /api/sms/bulk` - Send bulk personalized SMS
- `POST /api/sms/campaign` - Generate & send AI-powered personalized campaign
- `GET /api/sms/cost-estimate` - Estimate SMS costs
- `GET /api/customers` - List customers for targeting

### Admin
- `GET /api/admin/telemetry` - System usage metrics
- `GET /api/admin/settings` - Get system settings
- `POST /api/admin/settings` - Update system settings

---

## Project Guide
**Dr. B. Rama**

---

## Developed By
* **V. Surya Prakash**
* **Ch. Sagar**
* **K. Anil**

