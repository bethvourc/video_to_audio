import os
import sys

import gridfs
import pika
from convert import to_mp3
from pymongo import MongoClient
from pymongo.errors import ConfigurationError
from pymongo.uri_parser import parse_uri


def required_secret(name):
    value = os.environ.get(name)
    if not value or value.startswith("CHANGE_ME"):
        raise RuntimeError(f"{name} must be configured as a deployment secret")
    return value


def required_mongo_uri(name):
    uri = required_secret(name)
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


def main():
    video_queue = os.environ.get("VIDEO_QUEUE", "video")
    mp3_queue = os.environ.get("MP3_QUEUE", "mp3")
    rabbitmq_user = required_secret("RABBITMQ_DEFAULT_USER")
    rabbitmq_password = required_secret("RABBITMQ_DEFAULT_PASS")

    video_client = MongoClient(required_mongo_uri("MONGO_VIDEO_URI"))
    mp3_client = MongoClient(required_mongo_uri("MONGO_MP3_URI"))
    db_videos = video_client.get_default_database()
    db_mp3s = mp3_client.get_default_database()
    fs_videos = gridfs.GridFS(db_videos)
    fs_mp3s = gridfs.GridFS(db_mp3s)

    credentials = pika.PlainCredentials(rabbitmq_user, rabbitmq_password)
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=os.environ.get("RABBITMQ_HOST", "rabbitmq"), credentials=credentials
        )
    )
    channel = connection.channel()
    dead_queue = f"{video_queue}.dead"
    channel.queue_declare(queue=dead_queue, durable=True)
    channel.queue_declare(
        queue=video_queue,
        durable=True,
        arguments={"x-dead-letter-exchange": "", "x-dead-letter-routing-key": dead_queue},
    )
    mp3_dead_queue = f"{mp3_queue}.dead"
    channel.queue_declare(queue=mp3_dead_queue, durable=True)
    channel.queue_declare(
        queue=mp3_queue,
        durable=True,
        arguments={
            "x-dead-letter-exchange": "",
            "x-dead-letter-routing-key": mp3_dead_queue,
        },
    )
    channel.basic_qos(prefetch_count=1)

    def callback(ch, method, properties, body):
        try:
            to_mp3.start(body, fs_videos, fs_mp3s, ch)
        except (ValueError, TypeError, KeyError) as err:
            print(f"Discarding invalid conversion message: {err}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        except Exception as err:  # noqa: BLE001 - callback must reject unexpected poison jobs
            print(f"Conversion failed: {err}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        else:
            ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_consume(queue=video_queue, on_message_callback=callback)

    print("Waiting for messages. To exit press CMD+C")

    channel.start_consuming()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Interrupted")
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
