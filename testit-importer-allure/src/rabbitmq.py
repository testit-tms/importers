"""The module provides functionality for consuming rabbit MQ"""
import dataclasses
import pika


@dataclasses.dataclass
class RabbitMQ:
    """Class representing a rabit mq client"""

    def __init__(self, url: str, user: str, password: str, exchange: str):
        self.__url = pika.URLParameters('amqp://' + user + ':' + password + '@' + url)
        self.__exchange = exchange

    def consume(self, callback_func):
        """Function consumes query."""
        connection = pika.BlockingConnection(self.__url)
        channel = connection.channel()

        result = channel.queue_declare(queue='', exclusive=True)
        queue_name = result.method.queue
        channel.queue_bind(exchange=self.__exchange, queue=queue_name, routing_key="key")

        channel.basic_consume(queue=queue_name, on_message_callback=callback_func, auto_ack=True)
        channel.start_consuming()
