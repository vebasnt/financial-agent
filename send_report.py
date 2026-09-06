"""
Delivers the report via whichever channel(s) are configured through
environment variables (set as GitHub Actions secrets in production):

Email (SMTP):
  SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, EMAIL_TO
  (for Gmail: host=smtp.gmail.com, port=587, use an App Password, not your
  normal password)

Slack:
  SLACK_WEBHOOK_URL  (create at https://api.slack.com/messaging/webhooks)

If neither is configured, the report is just printed to stdout so you can
still see it in the GitHub Actions log.
"""
import os
import json
import smtplib
import logging
from email.mime.text import MIMEText

import urllib.request

log = logging.getLogger(__name__)


def send_email(subject: str, body: str) -> bool:
    host = os.environ.get("SMTP_HOST")
    port = int(os.environ.get("SMTP_PORT", "587"))
    user = os.environ.get("SMTP_USER")
    password = os.environ.get("SMTP_PASS")
    to_addr = os.environ.get("EMAIL_TO")

    if not all([host, user, password, to_addr]):
        return False

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = user
    msg["To"] = to_addr

    try:
        with smtplib.SMTP(host, port) as server:
            server.starttls()
            server.login(user, password)
            server.sendmail(user, [to_addr], msg.as_string())
        log.info("email sent to %s", to_addr)
        return True
    except Exception as e:
        log.error("email send failed: %s", e)
        return False


def send_slack(text: str) -> bool:
    webhook_url = os.environ.get("SLACK_WEBHOOK_URL")
    if not webhook_url:
        return False

    payload = json.dumps({"text": text}).encode("utf-8")
    req = urllib.request.Request(
        webhook_url, data=payload, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            ok = resp.status == 200
        log.info("slack post status ok=%s", ok)
        return ok
    except Exception as e:
        log.error("slack send failed: %s", e)
        return False


def deliver(report_text: str, subject: str = "Daily Market Digest") -> None:
    sent_email = send_email(subject, report_text)
    sent_slack = send_slack(report_text)

    if not sent_email and not sent_slack:
        log.warning("no delivery channel configured — printing to stdout instead")
        print(report_text)
