import logging
import os
from pathlib import Path
from typing import Dict, List

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env", override=True)

_log = logging.getLogger(__name__)


def _sms_debug_temp(msg: str, *args: object) -> None:
    """TODO: remove temporary SMS trace logs after root-cause."""
    _log.warning("[SMS_DEBUG_TEMP] " + msg, *args)


def _mask_phone_tail(phone: str) -> str:
    if not phone or len(phone) < 5:
        return "(redacted)"
    return "***" + phone[-4:]


def _normalize_sms_phone(phone: str) -> str:
    """E.164-style number for India (+91…) matching app SMS validation."""
    if not phone:
        return ""
    v = phone.replace(" ", "").replace("-", "")
    if not v.startswith("+"):
        if v.startswith("91") and len(v) >= 12:
            v = "+" + v
        elif v.startswith("0"):
            v = "+91" + v.lstrip("0")
        else:
            v = "+91" + v
    return v


def _sns_allowed_phone_set() -> set[str] | None:
    """
    If SNS_ALLOWED_PHONES is set (comma-separated E.164), only those numbers use AWS SNS Publish.
    Other numbers return skipped_allowlist (no AWS call). If unset/empty, all numbers may use SNS.
    """
    raw = (os.getenv("SNS_ALLOWED_PHONES") or "").strip()
    if not raw:
        return None
    out: set[str] = set()
    for part in raw.split(","):
        n = _normalize_sms_phone(part.strip())
        if n:
            out.add(n)
    return out or None


class SNSService:
    """AWS SNS SMS via direct ``Publish(PhoneNumber=…)`` (mock in ENV_MODE=test or without credentials)."""

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

        self._sns_allowed_phones = _sns_allowed_phone_set()
        if self.client and self._sns_allowed_phones is not None:
            print(
                "ℹ️  [SNS] SNS_ALLOWED_PHONES active — AWS Publish only for: "
                + ", ".join(sorted(self._sns_allowed_phones))
            )

    def dispatch_mode(self) -> str:
        """
        How outbound SMS is handled for this process.
        - mock_test_env: ENV_MODE=test (no AWS Publish; counts as 'sent' in bulk stats)
        - mock_no_aws_client: missing keys or failed boto init
        - live: real SNS Publish attempts
        """
        if self.env_mode == "test":
            return "mock_test_env"
        if not self.client:
            return "mock_no_aws_client"
        return "live"

    def send_sms(self, phone_number: str, message: str) -> Dict:
        """Publish one SMS (E.164 phone)."""
        if self.env_mode == "test" or not self.client:
            _sms_debug_temp(
                "MOCK path: env_mode=%s has_client=%s phone=%s msg_len=%s",
                self.env_mode,
                bool(self.client),
                _mask_phone_tail(str(phone_number)),
                len(message or ""),
            )
            return {
                "status": "success",
                "message_id": f"MOCK-{hash(phone_number + message) % 100000}",
                "phone": phone_number,
                "message": "SMS sent successfully (MOCK MODE)",
            }

        try:
            raw_in = phone_number
            phone_number = _normalize_sms_phone(phone_number)
            if not phone_number:
                _sms_debug_temp(
                    "invalid phone after normalize raw=%s norm=%r",
                    _mask_phone_tail(str(raw_in)),
                    phone_number,
                )
                return {"status": "error", "message": "Invalid phone number", "phone": phone_number}

            allowed = self._sns_allowed_phones
            if allowed is not None and phone_number not in allowed:
                _sms_debug_temp(
                    "allowlist SKIP phone=%s allowed_count=%s sample_allowed=%s",
                    _mask_phone_tail(phone_number),
                    len(allowed),
                    sorted(list(allowed))[:3],
                )
                return {
                    "status": "skipped_allowlist",
                    "message_id": None,
                    "phone": phone_number,
                    "message": "Not sent via AWS SNS (number not in SNS_ALLOWED_PHONES).",
                }

            _sms_debug_temp(
                "SNS publish attempt region=%s phone=%s msg_len=%s",
                self.aws_region,
                _mask_phone_tail(phone_number),
                len(message or ""),
            )
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

            _sms_debug_temp("SNS publish OK message_id=%s phone=%s", response.get("MessageId"), _mask_phone_tail(phone_number))
            return {
                "status": "success",
                "message_id": response["MessageId"],
                "phone": phone_number,
                "message": "SMS sent successfully",
            }

        except Exception as e:
            _sms_debug_temp(
                "SNS publish EXCEPTION phone=%s err_type=%s err=%s",
                _mask_phone_tail(str(phone_number)),
                type(e).__name__,
                str(e),
            )
            return {"status": "error", "message": str(e), "phone": phone_number}

    def send_bulk_sms(self, recipients: List[Dict]) -> Dict:
        """Send each dict with keys phone, message."""
        _sms_debug_temp(
            "send_bulk_sms start count=%s dispatch_mode=%s",
            len(recipients),
            self.dispatch_mode(),
        )
        results = []
        sent_count = 0
        failed_count = 0
        skipped_count = 0

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

            st = result["status"]
            if st == "success":
                sent_count += 1
            elif st == "skipped_allowlist":
                skipped_count += 1
            else:
                failed_count += 1

        out = {
            "status": "completed",
            "total": len(recipients),
            "sent": sent_count,
            "failed": failed_count,
            "skipped": skipped_count,
            "results": results,
        }
        _sms_debug_temp(
            "send_bulk_sms done sent=%s failed=%s skipped=%s",
            sent_count,
            failed_count,
            skipped_count,
        )
        for r in results:
            if r.get("status") == "error":
                _sms_debug_temp(
                    "per-recipient ERROR phone=%s detail=%s",
                    _mask_phone_tail(str(r.get("phone", ""))),
                    (r.get("message") or "")[:500],
                )
        return out

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
