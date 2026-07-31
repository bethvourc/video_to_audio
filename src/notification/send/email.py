import json
import os
import re
import smtplib
import ssl
from email.headerregistry import Address
from email.message import EmailMessage


def required_secret(name):
    value = os.environ.get(name)
    if not value or value.startswith("CHANGE_ME"):
        raise RuntimeError(f"{name} must be configured as a deployment secret")
    return value


def parse_message(raw_message):
    try:
        message = json.loads(raw_message)
    except (json.JSONDecodeError, UnicodeDecodeError) as err:
        raise ValueError("message is not valid JSON") from err

    if not isinstance(message, dict):
        raise TypeError("message must be a JSON object")

    mp3_fid = message.get("mp3_fid")
    username = message.get("username")
    if not isinstance(mp3_fid, str) or not re.fullmatch(r"[0-9a-fA-F]{24}", mp3_fid):
        raise ValueError("message has an invalid mp3_fid")
    if not isinstance(username, str) or len(username) > 254:
        raise ValueError("message has an invalid username")

    try:
        receiver = Address(addr_spec=username)
    except ValueError as err:
        raise ValueError("message has an invalid username") from err

    if not receiver.domain:
        raise ValueError("message has an invalid username")

    return mp3_fid, receiver


def notification(message):
    mp3_fid, receiver_address = parse_message(message)
    sender_address = required_secret("GMAIL_ADDRESS")
    sender_password = required_secret("GMAIL_PASSWORD")

    msg = EmailMessage()
    msg.set_content(f"MP3 file ID {mp3_fid} is now ready.")
    msg["Subject"] = "MP3 Download"
    msg["From"] = sender_address
    msg["To"] = receiver_address

    with smtplib.SMTP("smtp.gmail.com", 587, timeout=10) as session:
        session.ehlo()
        session.starttls(context=ssl.create_default_context())
        session.ehlo()
        session.login(sender_address, sender_password)
        session.send_message(msg, sender_address, str(receiver_address))
