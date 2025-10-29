from datetime import datetime
from typing import Tuple, Dict, List, BinaryIO


class StepResult:
    __title: str = None
    __outcome: str = None
    __description: str = None
    __duration: int = 0
    __started_on: datetime = None
    __completed_on: datetime = None
    __step_results: List = None
    __attachments: List = None
    __parameters: Dict = None

    def __init__(self):
        self.__step_results = []
        self.__attachments = []
        self.__parameters = {}

    def set_title(self, title: str):
        self.__title = title

        return self

    def get_title(self) -> str:
        return self.__title

    def set_outcome(self, outcome: str):
        self.__outcome = outcome

        return self

    def get_outcome(self) -> str:
        return self.__outcome

    def set_description(self, description: str):
        self.__description = description

        return self

    def get_description(self) -> str:
        return self.__description

    def set_duration(self, duration: int):
        self.__duration = duration

        return self

    def get_duration(self) -> int:
        return self.__duration

    def set_started_on(self, started_on: datetime):
        self.__started_on = started_on

        return self

    def get_started_on(self) -> datetime:
        return self.__started_on

    def set_completed_on(self, completed_on: datetime):
        self.__completed_on = completed_on

        return self

    def get_completed_on(self) -> datetime:
        return self.__completed_on

    def set_step_results(self, step_results: List):
        self.__step_results = step_results

        return self

    def get_step_results(self) -> List:
        return self.__step_results

    def set_attachments(self, attachments: List):
        self.__attachments = attachments

        return self

    def get_attachments(self) -> List:
        return self.__attachments

    def set_parameters(self, parameters: Dict):
        self.__parameters = parameters

        return self

    def get_parameters(self) -> Dict:
        return self.__parameters
