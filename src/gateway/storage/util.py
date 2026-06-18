import json
import os

import pika
from werkzeug.utils import secure_filename

ALLOWED_VIDEO_EXTENSIONS = {"avi", "m4v", "mkv", "mov", "mp4", "webm"}


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

    return True


def upload(f, fs, channel, access):
    try:
        fid = fs.put(
            f,
            content_type=f.mimetype,
            filename=secure_filename(f.filename or ""),
            uploaded_by=access["username"],
            max_upload_bytes=int(os.environ.get("MAX_UPLOAD_BYTES", 100 * 1024 * 1024)),
        )
    except Exception as err:
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
            routing_key="video",
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
            ),
        )
    except Exception as err:
        print(err)
        fs.delete(fid)
        return "internal server error", 500
