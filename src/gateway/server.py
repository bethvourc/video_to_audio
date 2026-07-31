import os

import gridfs
import pika
from auth_svc import access
from bson.objectid import ObjectId
from flask import Flask, request, send_file
from flask_pymongo import PyMongo
from gridfs.errors import NoFile
from pymongo.errors import ConfigurationError
from pymongo.uri_parser import parse_uri
from storage import util

from auth import validate

server = Flask(__name__)
server.config["MAX_CONTENT_LENGTH"] = int(
    os.environ.get("MAX_UPLOAD_BYTES", str(100 * 1024 * 1024))
)

def validated_mongo_uri(name):
    uri = os.environ.get(name)
    if not uri:
        raise RuntimeError(f"{name} must be configured as a deployment secret")
    try:
        parsed = parse_uri(uri)
    except ConfigurationError as err:
        raise RuntimeError(f"{name} is invalid") from err
    username = parsed.get("username")
    password = parsed.get("password")
    if (
        not username
        or not password
        or username.startswith("CHANGE_ME")
        or password.startswith("CHANGE_ME")
    ):
        raise RuntimeError(f"{name} must include non-placeholder credentials")
    return uri


MONGO_VIDEO_URI = validated_mongo_uri("MONGO_VIDEO_URI")
MONGO_MP3_URI = validated_mongo_uri("MONGO_MP3_URI")
RABBITMQ_HOST = os.environ.get("RABBITMQ_HOST", "rabbitmq")
RABBITMQ_USER = os.environ.get("RABBITMQ_DEFAULT_USER")
RABBITMQ_PASSWORD = os.environ.get("RABBITMQ_DEFAULT_PASS")
VIDEO_QUEUE = os.environ.get("VIDEO_QUEUE", "video")

if (
    not RABBITMQ_USER
    or not RABBITMQ_PASSWORD
    or RABBITMQ_USER.startswith("CHANGE_ME")
    or RABBITMQ_PASSWORD.startswith("CHANGE_ME")
):
    raise RuntimeError("RabbitMQ credentials must be configured as deployment secrets")

mongo_video = PyMongo(server, uri=MONGO_VIDEO_URI)

mongo_mp3 = PyMongo(server, uri=MONGO_MP3_URI)

fs_videos = gridfs.GridFS(mongo_video.db)
fs_mp3s = gridfs.GridFS(mongo_mp3.db)

credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
connection = pika.BlockingConnection(
    pika.ConnectionParameters(RABBITMQ_HOST, credentials=credentials)
)
channel = connection.channel()
dead_queue = f"{VIDEO_QUEUE}.dead"
channel.queue_declare(queue=dead_queue, durable=True)
channel.queue_declare(
    queue=VIDEO_QUEUE,
    durable=True,
    arguments={"x-dead-letter-exchange": "", "x-dead-letter-routing-key": dead_queue},
)


@server.get("/healthz")
def healthz():
    return "ok", 200


@server.route("/login", methods=["POST"])
def login():
    token, err = access.login(request)

    if not err:
        return token
    else:
        return err


@server.route("/upload", methods=["POST"])
def upload():
    claims, err = validate.token(request)

    if err:
        return err

    if claims["admin"]:
        if len(request.files) > 1 or len(request.files) < 1:
            return "exactly 1 file required", 400

        for f in request.files.values():
            if not util.is_allowed_video(f):
                return "unsupported file type", 400

            err = util.upload(f, fs_videos, channel, claims)

            if err:
                return err

        return "success!", 200
    else:
        return "not authorized", 403


@server.route("/download", methods=["GET"])
def download():
    claims, err = validate.token(request)

    if err:
        return err

    if claims["admin"]:
        fid_string = request.args.get("fid")

        if not fid_string:
            return "fid is required", 400

        if not ObjectId.is_valid(fid_string):
            return "invalid fid", 400

        try:
            out = fs_mp3s.get(ObjectId(fid_string))
        except NoFile:
            return "file not found", 404

        if getattr(out, "uploaded_by", None) != claims["username"]:
            return "file not found", 404

        return send_file(
            out,
            mimetype="audio/mpeg",
            as_attachment=True,
            download_name=f"{fid_string}.mp3",
            max_age=0,
        )

    return "not authorized", 403


if __name__ == "__main__":
    server.run(host="0.0.0.0", port=8080)
