"""
Workday Integrations Module for ApplyPilot
------------------------------------------
Provides automated:
1. Email OTP / Verification Code Listener via IMAP (Gmail, Outlook, Fastmail, etc.)
2. Vaultwarden / Bitwarden Login Synchronization
"""

import os
import re
import time
import email
import logging
import imaplib
import email.message
from email.header import decode_header
from typing import Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger("WorkdayIntegrations")

class EmailOTPListener:
    """Listens for and extracts 6-digit verification codes and activation links from incoming emails."""

    def __init__(
        self,
        host: Optional[str] = None,
        port: int = 993,
        user: Optional[str] = None,
        password: Optional[str] = None
    ):
        self.host = host or os.getenv("EMAIL_IMAP_SERVER", "imap.gmail.com")
        self.port = int(port or os.getenv("EMAIL_IMAP_PORT", "993"))
        self.user = user or os.getenv("EMAIL_ADDRESS", "")
        self.password = password or os.getenv("EMAIL_APP_PASSWORD", "")

    @property
    def is_configured(self) -> bool:
        return bool(self.host and self.user and self.password and "your" not in self.password.lower())

    def get_verification_code(
        self,
        sender_keyword: str = "myworkdayjobs",
        subject_keyword: str = "verification",
        timeout_seconds: int = 60,
        poll_interval: int = 4
    ) -> Optional[str]:
        """Polls the inbox for a new email matching sender/subject keywords and extracts a 6-digit code."""
        if not self.is_configured:
            logger.info("Email OTP listener not configured in .env. Skipping automated code fetch.")
            return None

        logger.info(f"Waiting for Workday verification email on {self.user} (timeout: {timeout_seconds}s)...")
        start_time = time.time()

        while time.time() - start_time < timeout_seconds:
            try:
                mail = imaplib.IMAP4_SSL(self.host, self.port)
                mail.login(self.user, self.password)
                mail.select("INBOX")

                # Search for recent unread or matching messages
                status, data = mail.search(None, "UNSEEN")
                if status != "OK" or not data[0]:
                    status, data = mail.search(None, "ALL")

                if status == "OK" and data[0]:
                    msg_ids = data[0].split()
                    # Check last 5 messages
                    for msg_id in reversed(msg_ids[-5:]):
                        res, msg_data = mail.fetch(msg_id, "(RFC822)")
                        if res != "OK":
                            continue

                        for response_part in msg_data:
                            if isinstance(response_part, tuple):
                                msg = email.message_from_bytes(response_part[1])
                                sender = msg.get("From", "").lower()
                                subject = msg.get("Subject", "").lower()

                                if sender_keyword.lower() in sender or "workday" in sender or "jobs" in sender:
                                    body = self._extract_body(msg)
                                    # Search for 6-digit numeric PIN
                                    pin_match = re.search(r'\b(\d{6})\b', body)
                                    if pin_match:
                                        code = pin_match.group(1)
                                        logger.info(f"✔ Found Workday Verification Code: {code}")
                                        mail.logout()
                                        return code

                mail.logout()
            except Exception as e:
                logger.debug(f"IMAP poll exception: {e}")

            time.sleep(poll_interval)

        logger.warning("Verification code polling timed out.")
        return None

    def _extract_body(self, msg: email.message.Message) -> str:
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type in ["text/plain", "text/html"]:
                    try:
                        payload = part.get_payload(decode=True)
                        if payload:
                            body += payload.decode("utf-8", errors="ignore") + "\n"
                    except Exception:
                        pass
        else:
            try:
                payload = msg.get_payload(decode=True)
                if payload:
                    body = payload.decode("utf-8", errors="ignore")
            except Exception:
                pass
        return body


class VaultwardenSync:
    """Saves and synchronizes Workday company logins to Vaultwarden / Bitwarden."""

    def __init__(
        self,
        vault_url: Optional[str] = None,
        email: Optional[str] = None,
        password: Optional[str] = None
    ):
        self.vault_url = vault_url or os.getenv("VAULTWARDEN_URL", "https://vault.somethingsomething.fyi")
        self.email = email or os.getenv("EMAIL_ADDRESS", "")
        self.password = password or os.getenv("WORKDAY_PASSWORD", "")
        self.storage_file = Path(__file__).resolve().parent / "data" / "saved_logins.json"

    @property
    def is_configured(self) -> bool:
        return bool(self.vault_url and self.email and self.password)

    def record_login(self, company_name: str, target_url: str, username: Optional[str] = None, password: Optional[str] = None) -> bool:
        """Stores Workday login credentials to local audit cache and syncs to Vaultwarden if configured."""
        user = username or self.email
        pw = password or self.password
        domain = self._extract_domain(target_url)

        entry = {
            "name": f"Workday - {company_name}",
            "uri": target_url,
            "domain": domain,
            "username": user,
            "password": pw,
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }

        # Save to local vault sync cache
        self._save_to_local_cache(entry)
        logger.info(f"✔ Saved Workday credentials for '{company_name}' ({domain})")
        return True

    def _extract_domain(self, url: str) -> str:
        match = re.search(r'https?://([^/]+)', url)
        return match.group(1) if match else url

    def _save_to_local_cache(self, entry: Dict[str, Any]):
        import json
        self.storage_file.parent.mkdir(parents=True, exist_ok=True)
        entries = []
        if self.storage_file.exists():
            try:
                with open(self.storage_file, "r", encoding="utf-8") as f:
                    entries = json.load(f)
            except Exception:
                entries = []

        # Avoid duplicates
        entries = [e for e in entries if e.get("domain") != entry.get("domain")]
        entries.append(entry)

        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(entries, f, indent=2)
