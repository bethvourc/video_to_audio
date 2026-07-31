import json
import os
import shutil
import tempfile

import pika
from bson.objectid import ObjectId
from moviepy.editor import VideoFileClip


def parse_message(raw_message):
    try:
        message = json.loads(raw_message)
    except (json.JSONDecodeError, UnicodeDecodeError) as err:
        raise ValueError("message is not valid JSON") from err

    if not isinstance(message, dict):
        raise TypeError("message must be a JSON object")

    video_fid = message.get("video_fid")
    username = message.get("username")
    if not isinstance(video_fid, str) or not ObjectId.is_valid(video_fid):
        raise ValueError("message has an invalid video_fid")
    if not isinstance(username, str) or not username or len(username) > 254:
        raise ValueError("message has an invalid username")

    return message


def start(message, fs_videos, fs_mp3s, channel):
    message = parse_message(message)
    video_fid = message["video_fid"]

    with tempfile.TemporaryDirectory(prefix="video-to-audio-") as temp_dir:
        video_path = os.path.join(temp_dir, "input-video")
        audio_path = os.path.join(temp_dir, "output.mp3")

        source = fs_videos.get(ObjectId(video_fid))
        with open(video_path, "wb") as video_file:
            shutil.copyfileobj(source, video_file)

        with VideoFileClip(video_path) as video_clip:
            if video_clip.audio is None:
                raise ValueError("video has no audio stream")
            video_clip.audio.write_audiofile(audio_path, logger=None)

        with open(audio_path, "rb") as audio_file:
            fid = fs_mp3s.put(
                audio_file,
                filename=f"{video_fid}.mp3",
                content_type="audio/mpeg",
                uploaded_by=message["username"],
            )

    message["mp3_fid"] = str(fid)

    try:
        channel.basic_publish(
            exchange="",
            routing_key=os.environ.get("MP3_QUEUE", "mp3"),
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
            ),
        )
    except Exception:
        fs_mp3s.delete(fid)
        raise
