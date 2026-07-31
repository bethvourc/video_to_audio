import io


class Upload:
    def __init__(self, filename, mimetype, content):
        self.filename = filename
        self.mimetype = mimetype
        self.stream = io.BytesIO(content)


def test_accepts_supported_container_signatures(load_source):
    storage = load_source("gateway_storage", "src/gateway/storage/util.py")
    samples = [
        Upload("clip.mp4", "video/mp4", b"\x00\x00\x00\x18ftypisomdata"),
        Upload("clip.webm", "video/webm", b"\x1aE\xdf\xa3webm-data"),
        Upload("clip.avi", "video/x-msvideo", b"RIFF\x00\x00\x00\x00AVI data"),
    ]

    assert all(storage.is_allowed_video(sample) for sample in samples)
    assert all(sample.stream.tell() == 0 for sample in samples)


def test_rejects_spoofed_or_unsupported_uploads(load_source):
    storage = load_source("gateway_storage_invalid", "src/gateway/storage/util.py")
    samples = [
        Upload("payload.mp4", "video/mp4", b"#!/bin/sh\nwhoami"),
        Upload("clip.mp4.exe", "video/mp4", b"\x00\x00\x00\x18ftypisomdata"),
        Upload("clip.mp4", "application/octet-stream", b"\x00\x00\x00\x18ftypisomdata"),
        Upload("clip", "video/mp4", b"\x00\x00\x00\x18ftypisomdata"),
    ]

    assert not any(storage.is_allowed_video(sample) for sample in samples)
