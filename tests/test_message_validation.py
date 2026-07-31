import json

import pytest


def test_converter_accepts_expected_message(load_source):
    converter = load_source("converter_to_mp3", "src/converter/convert/to_mp3.py")
    payload = {
        "video_fid": "507f1f77bcf86cd799439011",
        "mp3_fid": None,
        "username": "user@example.com",
    }

    assert converter.parse_message(json.dumps(payload)) == payload


@pytest.mark.parametrize(
    "payload",
    [
        b"not-json",
        json.dumps([]),
        json.dumps({"video_fid": "../etc/passwd", "username": "user@example.com"}),
        json.dumps({"video_fid": "507f1f77bcf86cd799439011", "username": ""}),
    ],
)
def test_converter_rejects_malformed_messages(load_source, payload):
    converter = load_source("converter_to_mp3_invalid", "src/converter/convert/to_mp3.py")

    with pytest.raises((TypeError, ValueError)):
        converter.parse_message(payload)


def test_notification_validates_email_and_object_id(load_source):
    notification = load_source("notification_email", "src/notification/send/email.py")
    payload = json.dumps(
        {"mp3_fid": "507f1f77bcf86cd799439011", "username": "user@example.com"}
    )

    mp3_fid, receiver = notification.parse_message(payload)

    assert mp3_fid == "507f1f77bcf86cd799439011"
    assert str(receiver) == "user@example.com"


@pytest.mark.parametrize(
    "payload",
    [
        {"mp3_fid": "not-an-object-id", "username": "user@example.com"},
        {
            "mp3_fid": "507f1f77bcf86cd799439011",
            "username": "victim@example.com\nBcc: attacker@example.com",
        },
        {"mp3_fid": "507f1f77bcf86cd799439011", "username": "local-only"},
    ],
)
def test_notification_rejects_untrusted_fields(load_source, payload):
    notification = load_source(
        "notification_email_invalid", "src/notification/send/email.py"
    )

    with pytest.raises(ValueError):
        notification.parse_message(json.dumps(payload))
