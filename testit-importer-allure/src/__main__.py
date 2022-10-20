from .rabbitmq import RabbitMQ
from .minioreader import MinioReader
from .parser import Parser
from .filereader import FileReader
from .configurator import Configurator
from .importer import Importer
from .apiclient import ApiClient


def console_main():
    config = Configurator()

    if config.get_path() is None:
        return

    reader = FileReader(config.get_path())
    parser = Parser(reader)
    api_client = ApiClient(config.get_url(), config.get_private_token())

    importer = Importer(parser, api_client, config)
    importer.send_result()


def consumer_main():
    config = Configurator()
    rabbitmq = RabbitMQ(config.get_rabbitmq_url(), config.get_rabbitmq_user(), config.get_rabbitmq_password(),
                        config.get_rabbitmq_exchange())

    def callback(ch, method, properties, body):
        reader = MinioReader(config.get_minio_url(), config.get_minio_access_key(), config.get_minio_secret_key(),
                             body.decode("utf-8"))
        parser = Parser(reader)
        api_client = ApiClient(config.get_url(), config.get_private_token())

        importer = Importer(parser, api_client, config)
        importer.send_result()

    rabbitmq.consume(callback)


if __name__ == "__main__":
    console_main()
