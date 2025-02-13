import typing

from .link import Link
from .step_result import StepResult


class TestResult:
    __external_id: str = None
    __outcome: str = None
    __title: str = None
    __description: str = None
    __duration: int = 0
    __started_on: str = None
    __completed_on: str = None
    __namespace: str = None
    __classname: str = None
    __message: str = None
    __traces: str = None
    __step_results: typing.List[StepResult] = []
    __setup_results: typing.List[StepResult] = []
    __teardown_results: typing.List[StepResult] = []
    __links: typing.List[Link] = []
    __attachments: typing.List[str] = []
    __labels: typing.List[str] = []
    __work_item_ids: typing.List[str] = []
    __parameters: dict = {}
    __is_flaky: bool = False

    def set_external_id(self, external_id: str):
        self.__external_id = external_id

        return self

    def get_external_id(self) -> str:
        return self.__external_id

    def set_outcome(self, outcome: str):
        self.__outcome = outcome

        return self

    def get_outcome(self) -> str:
        return self.__outcome

    def set_title(self, title: str):
        self.__title = title

        return self

    def get_title(self) -> str:
        return self.__title

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

    def set_started_on(self, started_on: str):
        self.__started_on = started_on

        return self

    def get_started_on(self) -> str:
        return self.__started_on

    def set_completed_on(self, completed_on: str):
        self.__completed_on = completed_on

        return self

    def get_completed_on(self) -> str:
        return self.__completed_on

    def set_namespace(self, namespace: str):
        self.__namespace = namespace

        return self

    def get_namespace(self) -> str:
        return self.__namespace

    def set_classname(self, classname: str):
        self.__classname = classname

        return self

    def get_classname(self) -> str:
        return self.__classname

    def set_message(self, message: str):
        self.__message = message

        return self

    def get_message(self) -> str:
        return self.__message

    def set_traces(self, traces: str):
        self.__traces = traces

        return self

    def get_traces(self) -> str:
        return self.__traces

    def set_step_results(self, step_results: typing.List[StepResult]):
        self.__step_results = step_results

        return self

    def get_step_results(self) -> typing.List[StepResult]:
        return self.__step_results

    def set_setup_results(self, setup_results: typing.List[StepResult]):
        self.__setup_results = setup_results

        return self

    def get_setup_results(self) -> typing.List[StepResult]:
        return self.__setup_results

    def set_teardown_results(self, teardown_results: typing.List[StepResult]):
        self.__teardown_results = teardown_results

        return self

    def get_teardown_results(self) -> typing.List[StepResult]:
        return self.__teardown_results

    def set_links(self, links: list):
        self.__links = links

        return self

    def get_links(self) -> list:
        return self.__links

    def set_attachments(self, attachments: list):
        self.__attachments = attachments

        return self

    def get_attachments(self) -> list:
        return self.__attachments

    def set_labels(self, labels: list):
        self.__labels = labels

        return self

    def get_labels(self) -> list:
        return self.__labels

    def set_work_item_ids(self, work_item_ids: list):
        self.__work_item_ids = work_item_ids

        return self

    def get_work_item_ids(self) -> list:
        return self.__work_item_ids

    def set_parameters(self, parameters: dict):
        self.__parameters = parameters

        return self

    def get_parameters(self) -> dict:
        return self.__parameters

    def set_is_flaky(self, is_flaky: bool):
        self.__is_flaky = is_flaky

        return self

    def get_is_flaky(self) -> bool:
        return self.__is_flaky
