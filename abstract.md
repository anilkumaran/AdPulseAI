# AdPulseAI - Generative AI for Autonomous Ad Synthesis and Business Intelligence

## Table of Contents
1. [Abstract](#abstract)
2. [System Specification](#system-specification)
   - [Hardware Requirements](#hardware-requirements-aws-ec2)
   - [Software Requirements](#software-requirements)
3. [System Modules](#system-modules)
   - [Admin Module](#1-admin-module-ownermanager)
   - [User Module](#2-user-module-employeesales-staff)
4. [Proposed System](#proposed-system-cloud-implementation-with-admin-control)
5. [Project Guide](#project-guide)
6. [Developed By](#developed-by)
---

## Abstract
The AdPulseAI is an innovative, cloud-based framework designed to democratize professional digital marketing and business intelligence for Enterprises by leveraging the transformative power of Generative Artificial Intelligence. Developed as a response to the resource constraints that often hinder small businesses—such as limited marketing budgets and lack of specialized data expertise—the system provides an automated platform for synthesizing multi-channel ad copy, optimizing SEO metadata, and identifying target audience segments. Hosted on Amazon Web Services (AWS) using a scalable EC2 infrastructure, the application utilizes the Google Gemini API to transform unstructured product data into high-converting promotional content with unprecedented speed and precision. By integrating a robust Admin Module for centralized governance and an intuitive user interface for streamlined task execution, AdPulseAI empowers SMEs to enhance their operational efficiency, reduce overhead costs by up to 30%, and maintain a competitive edge in an increasingly digital marketplace.

---

## System Specification

### Hardware Requirements (AWS EC2)
| Component | Specification |
| :--- | :--- |
| **Instance Type** | t2.micro (AWS Free Tier eligible) |
| **Processor** | 1 vCPU |
| **Memory (RAM)** | 1 GB |
| **Storage** | 8 GB Elastic Block Store (EBS) |
| **Network** | Public IP with Security Group configured for Port 80 (HTTP) and Port 5000 (Flask) |

### Software Requirements
| Layer | Technology / Tool |
| :--- | :--- |
| **Front End** | HTML5, CSS3, JavaScript (Vanilla) |
| **Back End** | Python 3.10+, Flask Framework |
| **Cloud Platform** | Amazon Web Services (AWS) |
| **AI Engine** | Google Gemini API |
| **Web Server** | Gunicorn (for production-grade deployment on AWS) |

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

## Project Guide
**Dr. B. Rama**

---

## Developed By
* **V. Surya Prakash**
* **Ch. Sagar**
* **K. Anil**






---
## Architecture 

```
🏗️ 3-Tier Role Structure:
┌─────────────────────────────────────────────────────────┐
│ SUPER ADMIN (AdPulseAI Owner)                           │
│ - Manage entire platform                                │
│ - View Gemini API usage across all merchants            │
│ - Change AI settings (system-wide)                      │
│ - Add/remove merchants                                  │
│ - View all merchants' data                              │
│ - Platform analytics                                    │
└─────────────────────────────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        ▼                 ▼                 ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ MERCHANT 1   │  │ MERCHANT 2   │  │ MERCHANT 3   │
│ (Business A) │  │ (Business B) │  │ (Business C) │
└──────────────┘  └──────────────┘  └──────────────┘
        │
        ├─ Merchant Admin (Business Owner)
        │  - Create employee accounts
        │  - Generate ads & SMS campaigns
        │  - View all employees' activity
        │  - Manage customers
        │  - View merchant-level analytics
        │
        └─ Employees (Staff 1, Staff 2, Staff 3...)
           - Generate ads only
           - Send SMS campaigns only
           - View their own history only

```