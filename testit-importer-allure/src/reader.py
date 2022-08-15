from interface import Interface


class Reader(Interface):

    def read_result_files(self):
        pass

    def read_attachment(self, name: str):
        pass
