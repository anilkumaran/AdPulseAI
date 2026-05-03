import os
from pathlib import Path
from typing import Dict, List

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env", override=True)


class SNSService:
    """AWS SNS SMS (mock in ENV_MODE=test or without credentials)."""

    def __init__(self):
        self.aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
        self.aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        self.aws_region = os.getenv("AWS_REGION", "ap-south-1")
        self.env_mode = os.getenv("ENV_MODE", "test")

        if self.env_mode == "test":
            print("⚠️  [SNS] Running in TEST mode - SMS will be mocked")
            self.client = None
        elif not self.aws_access_key or not self.aws_secret_key:
            print("⚠️  [SNS] AWS credentials not configured. SMS sending disabled.")
            self.client = None
        else:
            try:
                import boto3

                self.client = boto3.client(
                    "sns",
                    aws_access_key_id=self.aws_access_key,
                    aws_secret_access_key=self.aws_secret_key,
                    region_name=self.aws_region,
                )
                print("✅ [SNS] AWS SNS Service initialized successfully")
            except Exception as e:
                print(f"❌ [SNS] Failed to initialize: {str(e)}")
                self.client = None

    def send_sms(self, phone_number: str, message: str) -> Dict:
        """Publish one SMS (E.164 phone)."""
        if self.env_mode == "test" or not self.client:
            return {
                "status": "success",
                "message_id": f"MOCK-{hash(phone_number + message) % 100000}",
                "phone": phone_number,
                "message": "SMS sent successfully (MOCK MODE)",
            }

        try:
            if not phone_number.startswith("+"):
                phone_number = "+91" + phone_number.lstrip("0")

            response = self.client.publish(
                PhoneNumber=phone_number,
                Message=message,
                MessageAttributes={
                    "AWS.SNS.SMS.SMSType": {
                        "DataType": "String",
                        "StringValue": "Transactional",
                    }
                },
            )

            return {
                "status": "success",
                "message_id": response["MessageId"],
                "phone": phone_number,
                "message": "SMS sent successfully",
            }

        except Exception as e:
            return {"status": "error", "message": str(e), "phone": phone_number}

    def send_bulk_sms(self, recipients: List[Dict]) -> Dict:
        """Send each dict with keys phone, message."""
        results = []
        sent_count = 0
        failed_count = 0

        for recipient in recipients:
            phone = recipient.get("phone")
            message = recipient.get("message")

            if not phone or not message:
                results.append(
                    {"phone": phone or "unknown", "status": "error", "message": "Missing phone or message"}
                )
                failed_count += 1
                continue

            result = self.send_sms(phone, message)
            results.append(result)

            if result["status"] == "success":
                sent_count += 1
            else:
                failed_count += 1

        return {
            "status": "completed",
            "total": len(recipients),
            "sent": sent_count,
            "failed": failed_count,
            "results": results,
        }

    def get_sms_cost_estimate(self, num_messages: int, region: str = "India") -> Dict:
        """Rough SNS SMS cost (USD / INR)."""
        pricing = {"India": 0.00645, "US": 0.00645, "Europe": 0.05, "Other": 0.05}
        cost_per_sms = pricing.get(region, pricing["Other"])
        total_cost_usd = num_messages * cost_per_sms
        total_cost_inr = total_cost_usd * 83

        return {
            "num_messages": num_messages,
            "region": region,
            "cost_per_sms_usd": cost_per_sms,
            "total_cost_usd": round(total_cost_usd, 2),
            "total_cost_inr": round(total_cost_inr, 2),
        }


sns_service = SNSService()
