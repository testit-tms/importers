from src.filereader import FileReader
from src.configurator import Configurator
from src.importer import Importer
from src.apiclient import ApiClient


def console_main():
    config = Configurator()
    reader = FileReader(config.get_path())
    api_client = ApiClient(config.get_url(), config.get_private_token())

    importer = Importer(reader, api_client, config)
    importer.send_result()


if __name__ == "__main__":
    console_main()
