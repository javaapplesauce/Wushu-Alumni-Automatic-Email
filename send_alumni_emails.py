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
from typing import Iterable, List, Tuple

try:
    from dotenv import load_dotenv
except ImportError:
    raise SystemExit("Please install python-dotenv: pip install python-dotenv")

# ----------------------------- Config ---------------------------------

DEFAULT_SUBJECT = "Support Columbia Wushu October 21st Columbia Giving Day"

TEMPLATE = """Hi {{alumni_name}},

I hope this email finds you well! My name is Richard Li, Columbia Wushu’s current Vice President. October 21st marks Columbia University’s annual Giving Day, and I’m reaching out on behalf of our team to kindly ask for your support. 

Over the past year, our community has grown tremendously; not only in size, but also in the scope of our initiatives. Our club membership has quadrupled since last semester, and we’ve ambitiously planned community-wide joint workshops with other martial art clubs, new annual showcases featuring CU and non-CU performing arts teams, and so much more. This is all in the hopes of sharing the practice and values of Columbia Wushu with as many people as possible.

Your support would directly go towards:
* Helping provide gear to everybody, like shoes, silks, weapons.
* Keeping events accessible by minimizing registration, travel, and rooming fees passed onto students.
* Sustaining our club’s operational events, community programming and social activities.

Every contribution, no matter the size, directly supports Columbia’s and New York’s Wushu community. If you’d like to help us keep growing, you can donate directly through venmo (@wangyichen).

Thank you for believing in our movement, and we hope to see you at future CU Wushu events!

Warm regards,
The Columbia Wushu Team
columbiawushu@gmail.com | columbiawushu.org | IG: @columbiawushu
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
                print(f"⚠️  Skipping unrecognized entry: {raw}")
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
                print(f"✅ Sent to {c.display_name} <{c.email}>")
                sent += 1
            except smtplib.SMTPAuthenticationError as e:
                print("❌ Authentication failed. If you use 2‑Step Verification, you must use an App Password.")
                raise
            except Exception as e:
                print(f"⚠️  Failed to send to {c.display_name} <{c.email}>: {e}")

            # Polite delay
            time.sleep(max(0.0, args.delay) + random.uniform(0.0, 0.75))

    print(f"Done. Successfully processed {sent}/{len(contacts)} contacts.")

if __name__ == "__main__":
    main()
