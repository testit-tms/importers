from .apiclient import ApiClient
from .importer import Importer
from .parser import Parser
from .configurator import Configurator


def console_main():
    config = Configurator()

    if config.get_path() is None:
        return

    parser = Parser(config)
    api_client = ApiClient(config.get_url(), config.get_private_token())
    importer = Importer(parser, api_client, config)

    importer.send_results()


if __name__ == "__main__":
    console_main()
