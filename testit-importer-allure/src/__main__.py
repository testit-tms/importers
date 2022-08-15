from .parser import Parser
from .filereader import FileReader
from .configurator import Configurator
from .importer import Importer
from .apiclient import ApiClient


def console_main():
    config = Configurator()
    reader = FileReader(config.get_path())
    parser = Parser(reader)
    api_client = ApiClient(config.get_url(), config.get_private_token())

    importer = Importer(parser, api_client, config)
    importer.send_result()


if __name__ == "__main__":
    console_main()
