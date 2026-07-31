import os
import sys

import pika
from send import email


def required_secret(name):
    value = os.environ.get(name)
    if not value or value.startswith("CHANGE_ME"):
        raise RuntimeError(f"{name} must be configured as a deployment secret")
    return value


def main():
    mp3_queue = os.environ.get("MP3_QUEUE", "mp3")
    credentials = pika.PlainCredentials(
        required_secret("RABBITMQ_DEFAULT_USER"),
        required_secret("RABBITMQ_DEFAULT_PASS"),
    )
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=os.environ.get("RABBITMQ_HOST", "rabbitmq"), credentials=credentials
        )
    )
    channel = connection.channel()
    dead_queue = f"{mp3_queue}.dead"
    channel.queue_declare(queue=dead_queue, durable=True)
    channel.queue_declare(
        queue=mp3_queue,
        durable=True,
        arguments={"x-dead-letter-exchange": "", "x-dead-letter-routing-key": dead_queue},
    )
    channel.basic_qos(prefetch_count=10)

    def callback(ch, method, properties, body):
        try:
            email.notification(body)
        except (ValueError, TypeError, KeyError) as err:
            print(f"Discarding invalid notification message: {err}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        except Exception as err:  # noqa: BLE001 - callback must reject unexpected poison jobs
            print(f"Notification failed: {err}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        else:
            ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_consume(queue=mp3_queue, on_message_callback=callback)

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
