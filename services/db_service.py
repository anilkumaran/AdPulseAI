import json
import os
from datetime import datetime

class DBService:
    def __init__(self, file_path=None):
        if file_path is None:
            # Get the project root directory (parent of services)
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(current_dir)
            file_path = os.path.join(project_root, "schemas", "db.json")
        self.file_path = file_path
        self._init_db()

    def _init_db(self):
        needs_init = not os.path.exists(self.file_path) or os.stat(self.file_path).st_size == 0
        if needs_init:
            from services.auth_service import auth_svc
            schema = {
                "users": [
                    {"id": 1, "username": "admin", "password_hash": auth_svc.hash_password("admin123"), 
                     "role": "super_admin", "merchant_id": None, "name": "Platform Admin", 
                     "email": "admin@adpulseai.com", "is_active": True, 
                     "created_at": datetime.now().isoformat(), "updated_at": datetime.now().isoformat()}
                ],
                "merchants": [],
                "customers": [],
                "ad_generation_history": [],
                "sms_history": [],
                "sms_campaigns": [],
                "system_settings": {
                    "id": 1, "system_persona": "Professional Marketing Expert", 
                    "default_voice": "Professional", "updated_at": datetime.now().isoformat()
                },
                "telemetry": {
                    "total_api_calls": 0, "total_sms_sent": 0, "total_campaigns": 0,
                    "total_merchants": 0, "total_customers": 0, "total_users": 1,
                    "last_api_call_timestamp": None, "last_updated": datetime.now().isoformat()
                }
            }
            self._write_db(schema)

    def _read_db(self):
        with open(self.file_path, "r") as f:
            return json.load(f)

    def _write_db(self, data):
        with open(self.file_path, "w") as f:
            json.dump(data, f, indent=4)

    def get_data(self): return self._read_db()

    def get_user_by_username(self, username):
        """Get user by username - database-ready lookup"""
        db = self._read_db()
        for user in db.get("users", []):
            if user.get("username") == username:
                return user
        return None

    def log_generation(self, user_id, product_info, target_user_name, response_content, merchant_id=None, campaign_id=None):
        db = self._read_db()
        # Create preview from first 10 characters of product info
        preview_text = product_info[:10] if len(product_info) <= 10 else product_info[:10] + "..."
        new_entry = {
            "id": len(db.get("ad_generation_history", [])) + 1,
            "user_id": user_id,
            "merchant_id": merchant_id,
            "target_customer": target_user_name,
            "product_info": product_info[:100],
            "prompt_preview": preview_text,  # First 10 chars of product only
            "full_content": response_content,
            "campaign_id": campaign_id,
            "created_at": datetime.now().isoformat(),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        if "ad_generation_history" not in db:
            db["ad_generation_history"] = []
        db["ad_generation_history"].insert(0, new_entry)
        
        # Update telemetry
        db["telemetry"]["total_api_calls"] += 1
        db["telemetry"]["last_api_call_timestamp"] = new_entry["created_at"]
        db["telemetry"]["last_updated"] = datetime.now().isoformat()
        self._write_db(db)

    def get_user_history(self, username, role, merchant_id=None):
        db = self._read_db()
        history = db.get("ad_generation_history", [])
        
        if role == "super_admin":
            return history
        elif role in ["merchant_admin", "employee"] and merchant_id:
            return [h for h in history if h.get("merchant_id") == merchant_id]
        return []

    def get_customers_for_merchant(self, merchant_id):
        """Get customers for a specific merchant"""
        db = self._read_db()
        if not merchant_id:
            return []
        return [c for c in db.get("customers", []) if c.get("merchant_id") == merchant_id]

    def log_sms_send(self, user_id, phone, message, status):
        """Log single SMS send"""
        db = self._read_db()
        if "sms_history" not in db:
            db["sms_history"] = []
        
        db["sms_history"].insert(0, {
            "id": len(db["sms_history"]) + 1,
            "user_id": user_id,
            "phone": phone,
            "message_preview": message[:50] + "..." if len(message) > 50 else message,
            "status": status,
            "created_at": datetime.now().isoformat(),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        
        # Keep only last 100 SMS logs
        db["sms_history"] = db["sms_history"][:100]
        self._write_db(db)

    def log_bulk_sms_send(self, user_id, total, sent, failed):
        """Log bulk SMS send"""
        db = self._read_db()
        if "sms_campaigns" not in db:
            db["sms_campaigns"] = []
        
        db["sms_campaigns"].insert(0, {
            "id": len(db["sms_campaigns"]) + 1,
            "user_id": user_id,
            "type": "bulk_send",
            "total": total,
            "sent": sent,
            "failed": failed,
            "created_at": datetime.now().isoformat(),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        
        self._write_db(db)

    def log_sms_campaign(self, user_id, campaign_id, product_info, total_generated, messages_sent, merchant_id=None):
        """Log SMS campaign with personalization"""
        db = self._read_db()
        if "sms_campaigns" not in db:
            db["sms_campaigns"] = []
        
        db["sms_campaigns"].insert(0, {
            "id": len(db["sms_campaigns"]) + 1,
            "campaign_id": campaign_id,
            "user_id": user_id,
            "merchant_id": merchant_id,
            "type": "personalized_campaign",
            "product": product_info[:50],
            "total_generated": total_generated,
            "messages_sent": messages_sent,
            "created_at": datetime.now().isoformat(),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        
        # Update telemetry
        db["telemetry"]["total_campaigns"] += 1
        if messages_sent:
            db["telemetry"]["total_sms_sent"] += messages_sent
        
        self._write_db(db)

db_svc = DBService()