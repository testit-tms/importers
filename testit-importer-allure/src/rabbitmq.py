import pika


class RabbitMQ:
    def __init__(self, url: str, user: str, password: str, exchange: str):
        self.__url = pika.URLParameters('amqp://' + user + ':' + password + '@' + url)
        self.__exchange = exchange

    def consume(self):
        connection = pika.BlockingConnection(self.__url)
        channel = connection.channel()
        channel.exchange_declare(exchange=self.__exchange, exchange_type='direct')

        result = channel.queue_declare(queue='', exclusive=True)
        queue_name = result.method.queue
        channel.queue_bind(exchange=self.__exchange, queue=queue_name)

        channel.basic_consume(queue=queue_name, on_message_callback=self.callback, auto_ack=True)
        channel.start_consuming()

    @staticmethod
    def callback(ch, method, properties, body):
        print(" [x] %r" % body)
