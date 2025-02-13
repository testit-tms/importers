from .link_type import LinkType


class Link:
    __url: str = None
    __title: str = None
    __link_type: LinkType = None
    __description: str = None

    def set_url(self, url: str):
        self.__url = url

        return self

    def get_url(self) -> str:
        return self.__url

    def set_title(self, title: str):
        self.__title = title

        return self

    def get_title(self) -> str:
        return self.__title

    def set_link_type(self, link_type: LinkType):
        self.__link_type = link_type

        return self

    def get_link_type(self) -> LinkType:
        return self.__link_type

    def set_description(self, description: str):
        self.__description = description

        return self

    def get_description(self) -> str:
        return self.__description
