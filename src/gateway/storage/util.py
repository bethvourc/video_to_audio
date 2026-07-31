import json
import os

import pika
from pymongo.errors import PyMongoError
from werkzeug.utils import secure_filename

ALLOWED_VIDEO_EXTENSIONS = {"avi", "m4v", "mkv", "mov", "mp4", "webm"}
ISO_BASE_MEDIA_EXTENSIONS = {"m4v", "mov", "mp4"}
EBML_EXTENSIONS = {"mkv", "webm"}


def _container_matches(extension, header):
    if extension in ISO_BASE_MEDIA_EXTENSIONS:
        return len(header) >= 12 and header[4:8] == b"ftyp"
    if extension in EBML_EXTENSIONS:
        return header.startswith(b"\x1aE\xdf\xa3")
    if extension == "avi":
        return len(header) >= 12 and header[:4] == b"RIFF" and header[8:12] == b"AVI "
    return False


def is_allowed_video(file_storage):
    filename = secure_filename(file_storage.filename or "")
    if not filename or "." not in filename:
        return False

    extension = filename.rsplit(".", 1)[1].lower()
    if extension not in ALLOWED_VIDEO_EXTENSIONS:
        return False

    content_type = file_storage.mimetype or ""
    if content_type and not content_type.startswith("video/"):
        return False

    header = file_storage.stream.read(16)
    file_storage.stream.seek(0)
    return _container_matches(extension, header)


def upload(f, fs, channel, access):
    try:
        fid = fs.put(
            f,
            content_type=f.mimetype,
            filename=secure_filename(f.filename or ""),
            uploaded_by=access["username"],
        )
    except PyMongoError as err:
        print(err)
        return "internal server error", 500

    message = {
        "video_fid": str(fid),
        "mp3_fid": None,
        "username": access["username"],
    }

    try:
        channel.basic_publish(
            exchange="",
            routing_key=os.environ.get("VIDEO_QUEUE", "video"),
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
            ),
        )
    except pika.exceptions.AMQPError as err:
        print(err)
        try:
            fs.delete(fid)
        except PyMongoError:
            pass
        return "internal server error", 500
