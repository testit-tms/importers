from interface import Interface


class Reader(Interface):

    def get_all_files(self):
        pass

    def read_file(self, file_name: str):
        pass

    def read_attachment(self, file_name: str):
        pass

    def remove_attachment(self, file_name: str):
        pass
