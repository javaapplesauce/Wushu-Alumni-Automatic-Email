#!/usr/bin/env python3

import argparse
import os
import random
import re
import smtplib
import time
from dataclasses import dataclass
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List

try:
    from dotenv import load_dotenv
except ImportError:
    raise SystemExit("Please install python-dotenv: pip install python-dotenv")

# ----------------------------- Config ---------------------------------

DEFAULT_SUBJECT = "TEMPLATE HERE: "

TEMPLATE = """

YOUR EMAIL HERE

"""

# ----------------------------------------------------------------------

@dataclass
class Contact:
    display_name: str
    email: str

    @property
    def first_name(self) -> str:
        # Extract the first token of the display name as first name
        name = self.display_name.strip()
        if not name:
            return ""
        return re.split(r"\s+", name)[0].strip(",")


CONTACT_RE = re.compile(r"\s*([^<]+?)\s*<\s*([^>]+)\s*>\s*")

def parse_contacts(text: str) -> List[Contact]:
    """
    Parse a blob of comma-separated 'Name <email>' entries.
    Returns a list of Contact(display_name, email).
    Ignores empty / malformed entries but prints warnings.
    """
    contacts: List[Contact] = []
    # Split on commas that are followed by optional whitespace and either a word char or quote
    # Simpler: just split by comma and trim; entries are simple in the provided format.
    for raw in filter(None, (chunk.strip() for chunk in text.split(","))):
        if not raw:
            continue
        m = CONTACT_RE.fullmatch(raw)
        if m:
            display_name, email = m.group(1).strip(), m.group(2).strip()
            contacts.append(Contact(display_name=display_name, email=email))
        else:
            # If only an email was provided, infer a name from local-part
            email_candidate = raw.strip("<> ")
            if "@" in email_candidate and " " not in email_candidate:
                local = email_candidate.split("@", 1)[0]
                inferred = local.replace(".", " ").replace("_", " ").title()
                contacts.append(Contact(display_name=inferred, email=email_candidate))
            else:
                print(f"Skipping unrecognized entry: {raw}")
    return contacts


def load_contacts_from_file(path: str) -> List[Contact]:
    with open(path, "r", encoding="utf-8") as f:
        blob = f.read()
    return parse_contacts(blob)


def personalize(template: str, first_name: str) -> str:
    return template.replace("{{alumni_name}}", first_name or "there")


def send_email_gmail(
    sender_email: str,
    sender_pass: str,
    to_email: str,
    subject: str,
    body: str,
    from_name: str = None,
) -> None:
    msg = MIMEMultipart()
    msg["From"] = f'{from_name} <{sender_email}>' if from_name else sender_email
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain", "utf-8"))

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(sender_email, sender_pass)
        server.send_message(msg)


def main():
    parser = argparse.ArgumentParser(description="Send personalized alumni emails via Gmail SMTP.")
    parser.add_argument("--list", required=True, help="Path to alumni list file (comma-separated 'Name <email>' entries).")
    parser.add_argument("--subject", default=DEFAULT_SUBJECT, help="Email subject.")
    parser.add_argument("--from-name", default="Columbia Wushu Team", help="Display name for the From field.")
    parser.add_argument("--delay", type=float, default=3.0, help="Seconds to wait between sends.")
    parser.add_argument("--dry-run", action="store_true", help="Print emails instead of sending.")
    args = parser.parse_args()

    # Load credentials
    load_dotenv()
    sender_email = os.getenv("EMAIL_USER")
    sender_pass = os.getenv("EMAIL_PASS")

    if not sender_email or not sender_pass:
        raise SystemExit("Missing EMAIL_USER or EMAIL_PASS in environment. Create a .env with both values.")

    contacts = load_contacts_from_file(args.list)
    if not contacts:
        raise SystemExit("No contacts found. Check your list format.")

    print(f"Found {len(contacts)} contacts. {'(DRY RUN)' if args.dry_run else ''}")

    sent = 0
    for c in contacts:
        body = personalize(TEMPLATE, c.first_name)

        if args.dry_run:
            print("-" * 60)
            print(f"TO: {c.display_name} <{c.email}>")
            print(f"SUBJECT: {args.subject}")
            print(body)
        else:
            try:
                send_email_gmail(
                    sender_email=sender_email,
                    sender_pass=sender_pass,
                    to_email=c.email,
                    subject=args.subject,
                    body=body,
                    from_name=args.from_name,
                )
                print(f"Sent to {c.display_name} <{c.email}>")
                sent += 1
            except smtplib.SMTPAuthenticationError as e:
                print("Authentication failed.")
                raise
            except Exception as e:
                print(f"Failed to send to {c.display_name} <{c.email}>: {e}")

            time.sleep(max(0.0, args.delay) + random.uniform(0.0, 0.75))

    print(f"Done.")

if __name__ == "__main__":
    main()
